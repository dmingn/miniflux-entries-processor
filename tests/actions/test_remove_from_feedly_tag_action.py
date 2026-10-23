"""Tests for the RemoveFromFeedlyTagAction."""

from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

from miniflux_entries_processor.actions.remove_from_feedly_tag_action import (
    RemoveFromFeedlyTagAction,
)
from miniflux_entries_processor.feedly_client import Entry, Origin, Summary


@pytest.fixture
def mock_feedly_client(mocker: MockerFixture) -> MagicMock:
    """Fixture for mocking FeedlyClient returned by create_feedly_client."""
    mock_client: MagicMock = MagicMock()
    mock_client.user_id = "test_user_123"
    mocker.patch(
        "miniflux_entries_processor.actions.remove_from_feedly_tag_action.create_feedly_client",
        return_value=mock_client,
    )
    return mock_client


@pytest.fixture
def entry_builder() -> Callable[..., Entry]:
    """Fixture for a builder function to create Entry objects."""

    def _builder(
        entry_id: str = "entry_abc",
        title: str = "Test Entry",
    ) -> Entry:
        return Entry(
            id=entry_id,
            title=title,
            canonical_url="http://example.com/test",
            origin=Origin(
                title="Test Origin",
                html_url="http://example.com",
                stream_id="test_stream_id",
            ),
            summary=Summary(content="Summary"),
            published=1234567890,
            author=None,
        )

    return _builder


@pytest.mark.parametrize(
    "tag",
    [
        pytest.param("", id="empty"),
        pytest.param("   ", id="whitespace_only_after_strip"),
    ],
)
def test_RemoveFromFeedlyTagAction_rejects_invalid_tag(tag: str) -> None:
    # act & assert
    with pytest.raises(ValidationError):
        RemoveFromFeedlyTagAction(tag=tag)


@pytest.mark.parametrize(
    ("tag", "entry_id"),
    [
        pytest.param("global.saved", "entry_456", id="global_saved"),
        pytest.param("tech", "entry_789", id="custom_tag"),
    ],
)
def test_RemoveFromFeedlyTagAction_process_calls_remove_entry_from_tag_with_tag_and_entry_id(
    mock_feedly_client: MagicMock,
    entry_builder: Callable[..., Entry],
    tag: str,
    entry_id: str,
) -> None:
    # arrange
    action = RemoveFromFeedlyTagAction(tag=tag)
    entry = entry_builder(entry_id=entry_id)

    # act
    action.process(entry)

    # assert
    mock_feedly_client.remove_entry_from_tag.assert_called_once_with(tag, entry_id)


def test_RemoveFromFeedlyTagAction_uses_create_feedly_client(
    entry_builder: Callable[..., Entry],
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # arrange
    create_feedly_client = mocker.patch(
        "miniflux_entries_processor.actions.remove_from_feedly_tag_action.create_feedly_client",
    )
    monkeypatch.setenv("FEEDLY_TOKEN_DIR", str(tmp_path))
    action = RemoveFromFeedlyTagAction(tag="global.saved")
    entry = entry_builder()

    # act
    action.process(entry)

    # assert
    create_feedly_client.assert_called_once()
    call_args = create_feedly_client.call_args[0]
    assert call_args[0] == tmp_path
