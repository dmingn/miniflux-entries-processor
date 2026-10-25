"""Tests for the Miniflux client."""

from unittest.mock import MagicMock

import pytest
from pydantic import HttpUrl, SecretStr, TypeAdapter, ValidationError
from pytest_mock import MockerFixture
from requests.exceptions import HTTPError, RequestException

from miniflux_entries_processor.exceptions import (
    FetchEntriesError,
    GetEntryError,
    MarkAsReadError,
    MinifluxClientInitError,
    ToggleBookmarkError,
)
from miniflux_entries_processor.miniflux_client import (
    Entry,
    MinifluxClient,
    create_miniflux_client,
)
from miniflux_entries_processor.settings import MinifluxSettings
from tests.helpers import entry_api_dict, make_entry


@pytest.fixture
def mock_session(mocker: MockerFixture) -> MagicMock:
    session: MagicMock = mocker.MagicMock()
    return session


def test_MinifluxClient_fetch_entries_returns_entries_for_single_page(
    mock_session: MagicMock,
) -> None:
    # arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"{}"
    mock_response.json.return_value = {
        "total": 2,
        "entries": [
            entry_api_dict(entry_id=1),
            entry_api_dict(entry_id=2, title="Title 2", author="Author 2"),
        ],
    }
    mock_response.raise_for_status.return_value = None
    mock_session.request.return_value = mock_response
    client = MinifluxClient(
        base_url="https://miniflux.example",
        api_key="secret",
        session=mock_session,
    )

    # act
    entries = list(client.fetch_entries(starred=True))

    # assert
    assert len(entries) == 2
    assert entries[0].id == 1
    assert entries[1].id == 2
    mock_session.request.assert_called_once()
    _, kwargs = mock_session.request.call_args
    assert kwargs["params"]["starred"] == "true"
    assert kwargs["params"]["order"] == "id"
    assert kwargs["params"]["direction"] == "desc"
    assert "before_entry_id" not in kwargs["params"]
    assert "offset" not in kwargs["params"]


def test_MinifluxClient_fetch_entries_returns_all_entries_for_multiple_pages(
    mock_session: MagicMock,
) -> None:
    # arrange
    first = MagicMock()
    first.status_code = 200
    first.content = b"{}"
    first.json.return_value = {
        "total": 2,
        "entries": [entry_api_dict(entry_id=2)],
    }
    first.raise_for_status.return_value = None

    second = MagicMock()
    second.status_code = 200
    second.content = b"{}"
    second.json.return_value = {
        "total": 3,
        "entries": [entry_api_dict(entry_id=1)],
    }
    second.raise_for_status.return_value = None

    # Exactly page_size entries forces another request; empty page ends paging.
    third = MagicMock()
    third.status_code = 200
    third.content = b"{}"
    third.json.return_value = {"total": 3, "entries": []}
    third.raise_for_status.return_value = None
    mock_session.request.side_effect = [first, second, third]
    client = MinifluxClient(
        base_url="https://miniflux.example",
        api_key="secret",
        session=mock_session,
        page_size=1,
    )

    # act
    entries = list(client.fetch_entries(status="unread"))

    # assert
    assert [entry.id for entry in entries] == [2, 1]
    assert mock_session.request.call_count == 3
    first_params = mock_session.request.call_args_list[0].kwargs["params"]
    second_params = mock_session.request.call_args_list[1].kwargs["params"]
    assert "before_entry_id" not in first_params
    assert second_params["before_entry_id"] == 2


def test_MinifluxClient_fetch_entries_returns_empty_list_when_no_entries(
    mock_session: MagicMock,
) -> None:
    # arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"{}"
    mock_response.json.return_value = {"total": 0, "entries": []}
    mock_response.raise_for_status.return_value = None
    mock_session.request.return_value = mock_response
    client = MinifluxClient(
        base_url="https://miniflux.example",
        api_key="secret",
        session=mock_session,
    )

    # act
    entries = list(client.fetch_entries())

    # assert
    assert entries == []


def test_MinifluxClient_fetch_entries_raises_FetchEntriesError_when_request_raises(
    mock_session: MagicMock,
) -> None:
    # arrange
    mock_session.request.side_effect = RequestException("boom")
    client = MinifluxClient(
        base_url="https://miniflux.example",
        api_key="secret",
        session=mock_session,
    )

    # act / assert
    with pytest.raises(FetchEntriesError):
        list(client.fetch_entries())


def test_MinifluxClient_fetch_entries_raises_FetchEntriesError_when_validation_fails(
    mock_session: MagicMock,
) -> None:
    # arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"{}"
    mock_response.json.return_value = {"total": 1, "entries": [{"id": "bad"}]}
    mock_response.raise_for_status.return_value = None
    mock_session.request.return_value = mock_response
    client = MinifluxClient(
        base_url="https://miniflux.example",
        api_key="secret",
        session=mock_session,
    )

    # act / assert
    with pytest.raises(FetchEntriesError) as exc_info:
        list(client.fetch_entries())
    assert isinstance(exc_info.value.__cause__, ValidationError)


def test_MinifluxClient_get_entry_returns_entry(mock_session: MagicMock) -> None:
    # arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"{}"
    mock_response.json.return_value = entry_api_dict(entry_id=9)
    mock_response.raise_for_status.return_value = None
    mock_session.request.return_value = mock_response
    client = MinifluxClient(
        base_url="https://miniflux.example",
        api_key="secret",
        session=mock_session,
    )

    # act
    entry = client.get_entry(9)

    # assert
    assert entry.id == 9
    assert isinstance(entry, Entry)


def test_MinifluxClient_get_entry_raises_GetEntryError_when_request_raises(
    mock_session: MagicMock,
) -> None:
    # arrange
    mock_session.request.side_effect = RequestException("fail")
    client = MinifluxClient(
        base_url="https://miniflux.example",
        api_key="secret",
        session=mock_session,
    )

    # act / assert
    with pytest.raises(GetEntryError):
        client.get_entry(9)


def test_MinifluxClient_unstar_entry_toggles_when_starred(
    mock_session: MagicMock,
) -> None:
    # arrange
    get_response = MagicMock()
    get_response.status_code = 200
    get_response.content = b"{}"
    get_response.json.return_value = entry_api_dict(entry_id=3, starred=True)
    get_response.raise_for_status.return_value = None

    toggle_response = MagicMock()
    toggle_response.status_code = 204
    toggle_response.content = b""
    toggle_response.raise_for_status.return_value = None
    mock_session.request.side_effect = [get_response, toggle_response]
    client = MinifluxClient(
        base_url="https://miniflux.example",
        api_key="secret",
        session=mock_session,
    )

    # act
    changed = client.unstar_entry(3)

    # assert
    assert changed is True
    assert mock_session.request.call_count == 2
    assert mock_session.request.call_args_list[1].args[0] == "PUT"
    assert (
        mock_session.request.call_args_list[1]
        .args[1]
        .endswith("/v1/entries/3/bookmark")
    )


def test_MinifluxClient_unstar_entry_skips_toggle_when_already_unstarred(
    mock_session: MagicMock,
) -> None:
    # arrange
    get_response = MagicMock()
    get_response.status_code = 200
    get_response.content = b"{}"
    get_response.json.return_value = entry_api_dict(entry_id=3, starred=False)
    get_response.raise_for_status.return_value = None
    mock_session.request.return_value = get_response
    client = MinifluxClient(
        base_url="https://miniflux.example",
        api_key="secret",
        session=mock_session,
    )

    # act
    changed = client.unstar_entry(3)

    # assert
    assert changed is False
    assert mock_session.request.call_count == 1


def test_MinifluxClient_star_entry_toggles_when_unstarred(
    mock_session: MagicMock,
) -> None:
    # arrange
    get_response = MagicMock()
    get_response.status_code = 200
    get_response.content = b"{}"
    get_response.json.return_value = entry_api_dict(entry_id=3, starred=False)
    get_response.raise_for_status.return_value = None

    toggle_response = MagicMock()
    toggle_response.status_code = 204
    toggle_response.content = b""
    toggle_response.raise_for_status.return_value = None
    mock_session.request.side_effect = [get_response, toggle_response]
    client = MinifluxClient(
        base_url="https://miniflux.example",
        api_key="secret",
        session=mock_session,
    )

    # act
    changed = client.star_entry(3)

    # assert
    assert changed is True
    assert mock_session.request.call_count == 2
    assert mock_session.request.call_args_list[1].args[0] == "PUT"
    assert (
        mock_session.request.call_args_list[1]
        .args[1]
        .endswith("/v1/entries/3/bookmark")
    )


def test_MinifluxClient_star_entry_skips_toggle_when_already_starred(
    mock_session: MagicMock,
) -> None:
    # arrange
    get_response = MagicMock()
    get_response.status_code = 200
    get_response.content = b"{}"
    get_response.json.return_value = entry_api_dict(entry_id=3, starred=True)
    get_response.raise_for_status.return_value = None
    mock_session.request.return_value = get_response
    client = MinifluxClient(
        base_url="https://miniflux.example",
        api_key="secret",
        session=mock_session,
    )

    # act
    changed = client.star_entry(3)

    # assert
    assert changed is False
    assert mock_session.request.call_count == 1


def test_MinifluxClient_mark_entry_as_read_puts_status_read(
    mock_session: MagicMock,
) -> None:
    # arrange
    update_response = MagicMock()
    update_response.status_code = 204
    update_response.content = b""
    update_response.raise_for_status.return_value = None
    mock_session.request.return_value = update_response
    client = MinifluxClient(
        base_url="https://miniflux.example",
        api_key="secret",
        session=mock_session,
    )

    # act
    client.mark_entry_as_read(3)

    # assert
    mock_session.request.assert_called_once()
    update_call = mock_session.request.call_args
    assert update_call.args[0] == "PUT"
    assert update_call.args[1].endswith("/v1/entries")
    assert update_call.kwargs["json"] == {
        "entry_ids": [3],
        "status": "read",
    }


def test_MinifluxClient_mark_entry_as_read_raises_MarkAsReadError_when_request_raises(
    mock_session: MagicMock,
) -> None:
    # arrange
    mock_session.request.side_effect = RequestException("fail")
    client = MinifluxClient(
        base_url="https://miniflux.example",
        api_key="secret",
        session=mock_session,
    )

    # act / assert
    with pytest.raises(MarkAsReadError):
        client.mark_entry_as_read(3)


def test_MinifluxClient_toggle_entry_bookmark_raises_on_request_error(
    mock_session: MagicMock,
) -> None:
    # arrange
    error = HTTPError("fail")
    error.response = MagicMock()
    error.response.status_code = 500
    mock_session.request.side_effect = error
    client = MinifluxClient(
        base_url="https://miniflux.example",
        api_key="secret",
        session=mock_session,
    )

    # act / assert
    with pytest.raises(ToggleBookmarkError):
        client.toggle_entry_bookmark(1)
    assert mock_session.request.call_count == 3


def test_MinifluxClient_does_not_retry_on_client_error(
    mock_session: MagicMock,
) -> None:
    # arrange
    error = HTTPError("not found")
    error.response = MagicMock()
    error.response.status_code = 404
    mock_session.request.side_effect = error
    client = MinifluxClient(
        base_url="https://miniflux.example",
        api_key="secret",
        session=mock_session,
    )

    # act / assert
    with pytest.raises(ToggleBookmarkError):
        client.toggle_entry_bookmark(1)
    assert mock_session.request.call_count == 1


def test_MinifluxClient_rejects_empty_base_url() -> None:
    with pytest.raises(MinifluxClientInitError):
        MinifluxClient(base_url="  ", api_key="secret")


def test_create_miniflux_client_returns_client() -> None:
    # arrange
    settings = MinifluxSettings.model_construct(
        base_url=TypeAdapter(HttpUrl).validate_python("https://miniflux.example"),
        api_key=SecretStr("secret"),
    )

    # act
    client = create_miniflux_client(settings)

    # assert
    assert isinstance(client, MinifluxClient)


def test_Entry_normalizes_empty_author_to_None() -> None:
    # arrange / act
    entry = make_entry(author="")

    # assert
    assert entry.author is None


def test_Entry_rejects_naive_published_at() -> None:
    # arrange
    payload = entry_api_dict()
    payload["published_at"] = "2024-01-02T03:04:05"

    # act / assert
    with pytest.raises(ValidationError):
        Entry.model_validate(payload)


def test_Entry_keeps_timezone_aware_published_at() -> None:
    # arrange / act
    entry = Entry.model_validate(entry_api_dict())

    # assert
    assert entry.published_at.tzinfo is not None
