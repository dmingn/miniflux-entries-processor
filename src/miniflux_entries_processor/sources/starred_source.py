"""Starred entries source."""

from collections.abc import Generator
from typing import Literal

from miniflux_entries_processor.miniflux_client import Entry, MinifluxClient
from miniflux_entries_processor.sources.base_source import BaseSource


class StarredSource(BaseSource):
    """Source for starred entries."""

    name: Literal["starred"] = "starred"

    def fetch_entries(self, client: MinifluxClient) -> Generator[Entry]:
        """Fetch starred entries from Miniflux."""
        return client.fetch_entries(starred=True)
