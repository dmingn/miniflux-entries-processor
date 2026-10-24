"""Miniflux client for fetching and updating entries."""

from collections.abc import Generator, Mapping
from typing import Any, Literal
from urllib.parse import urljoin

import requests
from logzero import logger
from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    ValidationError,
    field_validator,
)
from requests.exceptions import HTTPError, RequestException
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from miniflux_entries_processor.exceptions import (
    FetchEntriesError,
    MinifluxClientInitError,
    MinifluxEntriesProcessorError,
)
from miniflux_entries_processor.settings import MinifluxSettings

EntryStatus = Literal["unread", "read", "removed"]

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class Category(BaseModel):
    """Feed category from Miniflux."""

    id: int
    title: str
    model_config = ConfigDict(frozen=True)


class Feed(BaseModel):
    """Feed nested in an entry response."""

    id: int
    title: str
    site_url: str
    category: Category
    model_config = ConfigDict(frozen=True)


class Entry(BaseModel):
    """Entry model mapped from the Miniflux API."""

    id: int
    title: str
    url: str
    author: str | None = None
    content: str
    published_at: AwareDatetime
    status: EntryStatus
    starred: bool
    feed: Feed
    model_config = ConfigDict(frozen=True)

    @field_validator("author", mode="before")
    @classmethod
    def _normalize_empty_author(cls, value: object) -> object:
        if value == "":
            return None
        return value


class EntriesResponse(BaseModel):
    """Paginated entries response from Miniflux."""

    total: int
    entries: tuple[Entry, ...]
    model_config = ConfigDict(frozen=True)


def _should_retry(exc: BaseException) -> bool:
    """Return True if the exception is worth retrying (transient/rate limit)."""
    if isinstance(exc, HTTPError):
        return (
            exc.response is not None
            and exc.response.status_code in RETRYABLE_STATUS_CODES
        )
    return isinstance(exc, RequestException)


class MinifluxClient:
    """HTTP client for the Miniflux API."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        session: requests.Session | None = None,
        page_size: int = 100,
    ) -> None:
        if not base_url.strip():
            msg = "MINIFLUX_BASE_URL must not be empty."
            raise MinifluxClientInitError(msg)
        if not api_key.strip():
            msg = "MINIFLUX_API_KEY must not be empty."
            raise MinifluxClientInitError(msg)

        self._base_url = base_url.rstrip("/") + "/"
        self._page_size = page_size
        self._session = session or requests.Session()
        self._session.headers.update(
            {
                "X-Auth-Token": api_key,
                "Accept": "application/json",
            }
        )

    def _url(self, path: str) -> str:
        return urljoin(self._base_url, path.lstrip("/"))

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception(_should_retry),
    )
    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
    ) -> Any:  # noqa: ANN401
        response = self._session.request(
            method,
            self._url(path),
            params=params,
            json=json,
            timeout=30,
        )
        response.raise_for_status()
        if response.status_code == requests.codes.no_content or not response.content:
            return None
        return response.json()

    def fetch_entries(
        self,
        *,
        starred: bool | None = None,
        status: EntryStatus | None = None,
    ) -> Generator[Entry]:
        """Fetch entries with optional filters, newest ingested first.

        Pages with ``order=id`` / ``direction=desc`` and ``before_entry_id`` so
        the cursor stays stable while entries are processed.
        """
        before_entry_id: int | None = None

        while True:
            params: dict[str, Any] = {
                "limit": self._page_size,
                "order": "id",
                "direction": "desc",
            }
            if before_entry_id is not None:
                params["before_entry_id"] = before_entry_id
            if starred is not None:
                params["starred"] = str(starred).lower()
            if status is not None:
                params["status"] = status

            logger.debug(f"Fetching entries with params: {params}")
            try:
                payload = self._request("GET", "/v1/entries", params=params)
                page = EntriesResponse.model_validate(payload)
            except (RequestException, ValidationError) as e:
                msg = "Failed to fetch entries from Miniflux."
                raise FetchEntriesError(msg) from e

            logger.debug(f"Fetched {len(page.entries)} entries (total={page.total}).")
            if not page.entries:
                logger.debug("No more entries to fetch.")
                break

            yield from page.entries

            if len(page.entries) < self._page_size:
                logger.debug("Last page reached.")
                break

            before_entry_id = page.entries[-1].id

    def get_entry(self, entry_id: int) -> Entry:
        """Fetch a single entry by ID."""
        try:
            payload = self._request("GET", f"/v1/entries/{entry_id}")
            return Entry.model_validate(payload)
        except (RequestException, ValidationError) as e:
            msg = f"Failed to fetch entry {entry_id}."
            raise MinifluxEntriesProcessorError(msg) from e

    def toggle_entry_bookmark(self, entry_id: int) -> None:
        """Toggle the starred state of an entry (not idempotent)."""
        try:
            self._request("PUT", f"/v1/entries/{entry_id}/bookmark")
        except RequestException as e:
            msg = f"Failed to toggle bookmark for entry {entry_id}."
            raise MinifluxEntriesProcessorError(msg) from e

    def unstar_entry(self, entry_id: int) -> bool:
        """Remove the star from an entry if it is currently starred.

        Returns
        -------
        bool
            True if the bookmark was toggled, False if already unstarred.
        """
        entry = self.get_entry(entry_id)
        if not entry.starred:
            logger.info(f"Entry {entry_id} is already unstarred; skipping toggle.")
            return False
        self.toggle_entry_bookmark(entry_id)
        return True

    def star_entry(self, entry_id: int) -> bool:
        """Star an entry if it is not currently starred.

        Returns
        -------
        bool
            True if the bookmark was toggled, False if already starred.
        """
        entry = self.get_entry(entry_id)
        if entry.starred:
            logger.info(f"Entry {entry_id} is already starred; skipping toggle.")
            return False
        self.toggle_entry_bookmark(entry_id)
        return True

    def mark_entry_as_read(self, entry_id: int) -> None:
        """Mark an entry as read."""
        try:
            self._request(
                "PUT",
                "/v1/entries",
                json={"entry_ids": [entry_id], "status": "read"},
            )
        except RequestException as e:
            msg = f"Failed to mark entry {entry_id} as read."
            raise MinifluxEntriesProcessorError(msg) from e


def create_miniflux_client(settings: MinifluxSettings | None = None) -> MinifluxClient:
    """Create a Miniflux client from settings."""
    if settings is None:
        try:
            settings = MinifluxSettings()
        except ValidationError as e:
            msg = "Failed to load Miniflux settings."
            raise MinifluxClientInitError(msg) from e

    return MinifluxClient(
        base_url=str(settings.base_url),
        api_key=settings.api_key.get_secret_value(),
    )
