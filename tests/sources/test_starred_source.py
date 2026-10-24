"""Tests for StarredSource."""

from unittest.mock import MagicMock

from miniflux_entries_processor.sources.starred_source import StarredSource
from tests.helpers import make_entry


def test_StarredSource_fetch_entries_calls_client_with_starred_true() -> None:
    # arrange
    source = StarredSource()
    client = MagicMock()
    client.fetch_entries.return_value = iter([make_entry()])

    # act
    entries = list(source.fetch_entries(client))

    # assert
    client.fetch_entries.assert_called_once_with(starred=True)
    assert len(entries) == 1
