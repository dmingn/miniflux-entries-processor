"""Shared test helpers."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import httpx
from requests.exceptions import HTTPError

from miniflux_entries_processor.miniflux_client import Category, Entry, Feed


def make_http_error(status_code: int) -> HTTPError:
    """Build a requests HTTPError with the given status code for Miniflux tests."""
    error = HTTPError("Server error")
    error.response = MagicMock()
    error.response.status_code = status_code
    return error


def make_httpx_status_error(status_code: int) -> httpx.HTTPStatusError:
    """Build an httpx HTTPStatusError with the given status code for Todoist tests."""
    request = httpx.Request("POST", "https://api.todoist.com/api/v1/tasks")
    response = httpx.Response(status_code, request=request)
    return httpx.HTTPStatusError(
        "Server error",
        request=request,
        response=response,
    )


def make_entry(  # noqa: PLR0913
    *,
    entry_id: int = 1,
    title: str = "Test Entry",
    url: str = "http://example.com/test",
    author: str | None = "Author",
    content: str = "Content",
    status: str = "unread",
    starred: bool = True,
    feed_id: int = 42,
    feed_title: str = "Feed Title",
    category_id: int = 7,
    category_title: str = "Category",
) -> Entry:
    """Build a Miniflux Entry for tests."""
    return Entry(
        id=entry_id,
        title=title,
        url=url,
        author=author,
        content=content,
        published_at=datetime(2024, 1, 2, 3, 4, 5, tzinfo=UTC),
        status=status,
        starred=starred,
        feed=Feed(
            id=feed_id,
            title=feed_title,
            site_url="http://example.com",
            category=Category(id=category_id, title=category_title),
        ),
    )


def entry_api_dict(  # noqa: PLR0913
    *,
    entry_id: int = 1,
    title: str = "Title 1",
    author: str = "Author 1",
    starred: bool = True,
    status: str = "unread",
    feed_id: int = 42,
    published_at: str = "2024-01-02T03:04:05Z",
) -> dict[str, object]:
    """Build a Miniflux API entry payload for client tests."""
    return {
        "id": entry_id,
        "title": title,
        "url": f"http://example.com/{entry_id}",
        "author": author,
        "content": f"Content {entry_id}",
        "published_at": published_at,
        "status": status,
        "starred": starred,
        "feed": {
            "id": feed_id,
            "title": "Feed Title",
            "site_url": "http://example.com",
            "category": {"id": 7, "title": "Category"},
        },
    }
