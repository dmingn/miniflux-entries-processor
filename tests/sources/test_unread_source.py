"""Tests for UnreadSource."""

from unittest.mock import MagicMock

from miniflux_entries_processor.sources.unread_source import UnreadSource
from tests.helpers import make_entry


def test_UnreadSource_fetch_entries_calls_client_with_status_unread() -> None:
    # arrange
    source = UnreadSource()
    client = MagicMock()
    client.fetch_entries.return_value = iter([make_entry(starred=False)])

    # act
    entries = list(source.fetch_entries(client))

    # assert
    client.fetch_entries.assert_called_once_with(status="unread")
    assert len(entries) == 1
