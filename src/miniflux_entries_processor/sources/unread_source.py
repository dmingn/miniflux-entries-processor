"""Unread entries source."""

from collections.abc import Generator
from typing import Literal

from miniflux_entries_processor.miniflux_client import Entry, MinifluxClient
from miniflux_entries_processor.sources.base_source import BaseSource


class UnreadSource(BaseSource):
    """Source for unread entries."""

    name: Literal["unread"] = "unread"

    def fetch_entries(self, client: MinifluxClient) -> Generator[Entry]:
        """Fetch unread entries from Miniflux."""
        return client.fetch_entries(status="unread")
