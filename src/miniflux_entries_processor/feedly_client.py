"""Feedly client for fetching entries."""

from collections.abc import Generator
from pathlib import Path
from urllib.parse import quote

from feedly.api_client.session import FeedlySession, FileAuthStore
from logzero import logger
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic.alias_generators import to_camel
from requests.exceptions import RequestException

from miniflux_entries_processor.exceptions import (
    FeedlyClientInitError,
    FeedlyEntriesProcessorError,
    FetchEntriesError,
)


class Summary(BaseModel):
    """Summary model."""

    content: str
    model_config = ConfigDict(
        alias_generator=to_camel,
        frozen=True,
        validate_by_alias=True,
        validate_by_name=True,
    )


class Origin(BaseModel):
    """Origin model."""

    html_url: str
    stream_id: str
    title: str
    model_config = ConfigDict(
        alias_generator=to_camel,
        frozen=True,
        validate_by_alias=True,
        validate_by_name=True,
    )


class Alternate(BaseModel):
    """Alternate link (e.g. article URL as shared by the publisher)."""

    href: str
    type: str | None = Field(default=None, alias="type")
    model_config = ConfigDict(
        alias_generator=to_camel,
        frozen=True,
        validate_by_alias=True,
        validate_by_name=True,
        populate_by_name=True,
    )


class Entry(BaseModel):
    """Entry model."""

    id: str
    author: str | None = None
    canonical_url: str | None = None
    alternate: tuple[Alternate, ...] | None = None
    origin: Origin | None = None
    published: int | None = None
    summary: Summary | None = None
    title: str | None = None
    model_config = ConfigDict(
        alias_generator=to_camel,
        frozen=True,
        validate_by_alias=True,
        validate_by_name=True,
    )

    @property
    def effective_url(self) -> str | None:
        """Return the best available URL: canonical_url, or first alternate."""
        return self.canonical_url or (
            self.alternate[0].href if self.alternate else None
        )


class StreamContents(BaseModel):
    """StreamContents model."""

    items: list[Entry]
    continuation: str | None = None
    model_config = ConfigDict(frozen=True)


class FeedlyClient:
    """Feedly client for fetching entries.

    Retries for Feedly API calls are handled by FeedlySession (feedly-client):
    up to 3 attempts with exponential backoff, and HTTPAdapter(max_retries=1)
    for connection errors.
    """

    def __init__(self, feedly_session: FeedlySession) -> None:
        self.feedly_session = feedly_session

    @property
    def user_id(self) -> str:
        """Return the authenticated user's ID."""
        return str(self.feedly_session.user.id)

    def fetch_entries(self, stream_id: str) -> Generator[Entry]:
        """Fetch entries from a stream.

        Parameters
        ----------
            stream_id: The ID of the stream to fetch entries from.

        Yields
        ------
            An iterator of Entry objects.

        Raises
        ------
            FetchEntriesError: If there is an error fetching entries from Feedly.
        """
        continuation = None

        while True:
            logger.debug(
                f"Fetching entries from stream {stream_id} with continuation: {continuation}"
            )
            try:
                stream_contents = StreamContents.model_validate(
                    self.feedly_session.do_api_request(
                        relative_url="/v3/streams/contents",
                        params=(
                            {
                                "streamId": stream_id,
                                "count": "1000",
                                "ranked": "newest",
                            }
                            | ({"continuation": continuation} if continuation else {})
                        ),
                    ),
                )
            except (RequestException, ValidationError) as e:
                msg = f"Failed to fetch entries from stream {stream_id}."
                raise FetchEntriesError(msg) from e

            logger.debug(f"Fetched {len(stream_contents.items)} entries.")

            yield from stream_contents.items

            if (not stream_contents.continuation) or (not stream_contents.items):
                logger.debug("No more entries to fetch or continuation is None.")
                break

            continuation = stream_contents.continuation

    def remove_entry_from_tag(self, tag_id: str, entry_id: str) -> None:
        """Remove an entry from a Feedly tag.

        Parameters
        ----------
            tag_id: The tag identifier (e.g. global.saved, or a user tag label like tech).
            entry_id: The ID of the entry to remove.

        Raises
        ------
            FeedlyEntriesProcessorError: If there is an error removing the entry.
        """
        stream_id_encoded = quote(f"user/{self.user_id}/tag/{tag_id}", safe="")
        entry_encoded = quote(entry_id, safe="")
        try:
            self.feedly_session.do_api_request(
                relative_url=f"/v3/tags/{stream_id_encoded}/{entry_encoded}",
                method="DELETE",
            )
        except RequestException as e:
            msg = f"Failed to remove entry {entry_id!r} from tag {tag_id!r}."
            raise FeedlyEntriesProcessorError(msg) from e


def create_feedly_client(token_dir: Path) -> FeedlyClient:
    """Create a Feedly client.

    Parameters
    ----------
    token_dir
        The directory where the Feedly API token is stored.

    Returns
    -------
    FeedlyClient
        An initialized Feedly client.

    Raises
    ------
    FeedlyClientInitError
        If there is an error initializing the Feedly client.
    """
    try:
        auth = FileAuthStore(token_dir=token_dir)
        feedly_session = FeedlySession(auth=auth)
        return FeedlyClient(feedly_session=feedly_session)
    except (ValueError, FileNotFoundError, PermissionError) as e:
        msg = (
            f"Failed to initialize Feedly client from token directory {token_dir}: {e}"
        )
        raise FeedlyClientInitError(msg) from e
