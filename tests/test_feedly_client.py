"""Tests for the Feedly client."""

import stat
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture
from requests.exceptions import RequestException

from miniflux_entries_processor.exceptions import (
    FeedlyClientInitError,
    FeedlyEntriesProcessorError,
    FetchEntriesError,
)
from miniflux_entries_processor.feedly_client import (
    Entry,
    FeedlyClient,
    Origin,
    Summary,
    create_feedly_client,
)


@pytest.fixture
def mock_feedly_session(mocker: MockerFixture) -> MagicMock:
    session: MagicMock = mocker.MagicMock()
    session.user.id = "test_user_id"
    return session


def test_FeedlyClient_fetch_entries_returns_entries_for_single_page(
    mock_feedly_session: MagicMock,
) -> None:
    # arrange
    mock_feedly_session.do_api_request.return_value = {
        "items": [
            {
                "id": "entry1",
                "title": "Title 1",
                "author": "Author 1",
                "published": 1678886400000,
                "summary": {"content": "Summary 1"},
                "canonicalUrl": "http://example.com/canonical/1",
                "origin": {
                    "htmlUrl": "http://example.com/1",
                    "streamId": "stream1",
                    "title": "Origin 1",
                },
            },
            {
                "id": "entry2",
                "title": "Title 2",
                "author": "Author 2",
                "published": 1678886401000,
                "summary": {"content": "Summary 2"},
                "canonicalUrl": "http://example.com/canonical/2",
                "origin": {
                    "htmlUrl": "http://example.com/2",
                    "streamId": "stream2",
                    "title": "Origin 2",
                },
            },
        ],
        "continuation": None,  # No more pages
    }

    client = FeedlyClient(mock_feedly_session)
    stream_id = "dummy_stream_id"

    # act
    entries = list(client.fetch_entries(stream_id))

    # assert
    expected_entries = [
        Entry(
            id="entry1",
            title="Title 1",
            author="Author 1",
            published=1678886400000,
            summary=Summary(content="Summary 1"),
            canonical_url="http://example.com/canonical/1",
            alternate=None,
            origin=Origin(
                html_url="http://example.com/1",
                stream_id="stream1",
                title="Origin 1",
            ),
        ),
        Entry(
            id="entry2",
            title="Title 2",
            author="Author 2",
            published=1678886401000,
            summary=Summary(content="Summary 2"),
            canonical_url="http://example.com/canonical/2",
            alternate=None,
            origin=Origin(
                html_url="http://example.com/2",
                stream_id="stream2",
                title="Origin 2",
            ),
        ),
    ]

    assert entries == expected_entries
    mock_feedly_session.do_api_request.assert_called_once_with(
        relative_url="/v3/streams/contents",
        params={
            "streamId": stream_id,
            "count": "1000",
            "ranked": "newest",
        },
    )


def test_FeedlyClient_fetch_entries_returns_all_entries_for_multiple_pages(
    mock_feedly_session: MagicMock,
) -> None:
    # arrange
    mock_feedly_session.do_api_request.side_effect = [
        # First page
        {
            "items": [{"id": "entry1"}, {"id": "entry2"}],
            "continuation": "continuation1",
        },
        # Second page
        {
            "items": [{"id": "entry3"}, {"id": "entry4"}],
            "continuation": None,  # No more pages
        },
    ]

    client = FeedlyClient(mock_feedly_session)
    stream_id = "dummy_stream_id"

    # act
    entries = list(client.fetch_entries(stream_id))

    # assert
    assert len(entries) == 4
    assert entries[0].id == "entry1"
    assert entries[1].id == "entry2"
    assert entries[2].id == "entry3"
    assert entries[3].id == "entry4"

    mock_feedly_session.do_api_request.assert_any_call(
        relative_url="/v3/streams/contents",
        params={
            "streamId": stream_id,
            "count": "1000",
            "ranked": "newest",
        },
    )
    mock_feedly_session.do_api_request.assert_any_call(
        relative_url="/v3/streams/contents",
        params={
            "streamId": stream_id,
            "count": "1000",
            "ranked": "newest",
            "continuation": "continuation1",
        },
    )
    assert mock_feedly_session.do_api_request.call_count == 2


def test_FeedlyClient_fetch_entries_returns_empty_list_when_no_entries(
    mock_feedly_session: MagicMock,
) -> None:
    # arrange
    mock_feedly_session.do_api_request.return_value = {
        "items": [],
        "continuation": None,
    }

    client = FeedlyClient(mock_feedly_session)
    stream_id = "dummy_stream_id"

    # act
    entries = list(client.fetch_entries(stream_id))

    # assert
    assert len(entries) == 0
    mock_feedly_session.do_api_request.assert_called_once()


def test_FeedlyClient_user_id_returns_session_user_id(
    mock_feedly_session: MagicMock,
) -> None:
    # arrange & act
    client = FeedlyClient(mock_feedly_session)

    # assert
    assert client.user_id == "test_user_id"


def test_FeedlyClient_fetch_entries_raises_FetchEntriesError_when_request_raises(
    mock_feedly_session: MagicMock,
) -> None:
    # arrange
    mock_feedly_session.do_api_request.side_effect = RequestException

    client = FeedlyClient(mock_feedly_session)

    # act & assert
    with pytest.raises(FetchEntriesError):
        list(client.fetch_entries("dummy_stream_id"))


def test_FeedlyClient_fetch_entries_raises_FetchEntriesError_when_validation_fails(
    mock_feedly_session: MagicMock,
) -> None:
    # arrange
    mock_feedly_session.do_api_request.return_value = {
        "items": [{"invalid_field": "foo"}]
    }

    client = FeedlyClient(mock_feedly_session)

    # act & assert
    with pytest.raises(FetchEntriesError) as excinfo:
        list(client.fetch_entries("dummy_stream_id"))

    assert isinstance(excinfo.value.__cause__, ValidationError)


def test_create_feedly_client_returns_FeedlyClient_on_success(
    tmp_path: Path,
) -> None:
    # Create dummy token files
    (tmp_path / "access.token").write_text("dummy_access_token")
    (tmp_path / "refresh.token").write_text("dummy_refresh_token")

    # act
    client = create_feedly_client(token_dir=tmp_path)

    # assert
    assert isinstance(client, FeedlyClient)


def test_create_feedly_client_raises_FeedlyClientInitError_when_dir_missing(
    tmp_path: Path,
) -> None:
    non_existent_dir = tmp_path / "non_existent"
    # act & assert
    with pytest.raises(FeedlyClientInitError):
        create_feedly_client(token_dir=non_existent_dir)


def test_create_feedly_client_raises_FeedlyClientInitError_when_token_file_missing(
    tmp_path: Path,
) -> None:
    # act & assert: directory exists but is empty
    with pytest.raises(FeedlyClientInitError):
        create_feedly_client(token_dir=tmp_path)


def test_create_feedly_client_raises_FeedlyClientInitError_when_file_unreadable(
    tmp_path: Path,
) -> None:
    # arrange
    access_token_file = tmp_path / "access.token"
    access_token_file.write_text("dummy-token")

    # Set file permissions to write and execute only for the owner.
    unreadable_mode = stat.S_IWUSR | stat.S_IXUSR
    access_token_file.chmod(unreadable_mode)

    # act & assert
    with pytest.raises(FeedlyClientInitError) as excinfo:
        create_feedly_client(token_dir=tmp_path)

    assert isinstance(excinfo.value.__cause__, PermissionError)


def test_create_feedly_client_raises_FeedlyClientInitError_when_dir_unreadable(
    tmp_path: Path,
) -> None:
    # arrange
    token_dir = tmp_path / "unreadable_dir"
    token_dir.mkdir()
    (token_dir / "access.token").write_text("dummy-token")

    # Set directory permissions to be non-executable for the owner.
    non_executable_mode = stat.S_IRUSR | stat.S_IWUSR
    token_dir.chmod(non_executable_mode)

    # act & assert
    try:
        with pytest.raises(FeedlyClientInitError) as excinfo:
            create_feedly_client(token_dir=token_dir)
    finally:
        # Restore permissions so pytest can clean up tmp_path.
        token_dir.chmod(0o700)

    assert isinstance(excinfo.value.__cause__, PermissionError)


def test_FeedlyClient_remove_entry_from_tag_calls_delete_with_encoded_path(
    mock_feedly_session: MagicMock,
) -> None:
    # arrange: client builds user/{user_id}/tag/{tag_id} from tag_id
    mock_feedly_session.do_api_request.return_value = None
    client = FeedlyClient(mock_feedly_session)
    tag_id = "global.saved"
    entry_id = "entry_abc=123"

    # act
    client.remove_entry_from_tag(tag_id, entry_id)

    # assert
    mock_feedly_session.do_api_request.assert_called_once_with(
        relative_url="/v3/tags/user%2Ftest_user_id%2Ftag%2Fglobal.saved/entry_abc%3D123",
        method="DELETE",
    )


def test_FeedlyClient_remove_entry_from_tag_raises_FeedlyEntriesProcessorError_when_request_raises(
    mock_feedly_session: MagicMock,
) -> None:
    # arrange
    mock_feedly_session.do_api_request.side_effect = RequestException
    client = FeedlyClient(mock_feedly_session)

    # act & assert
    with pytest.raises(FeedlyEntriesProcessorError):
        client.remove_entry_from_tag("global.saved", "entry1")
