"""All feed stream source."""

from collections.abc import Generator
from typing import Literal

from miniflux_entries_processor.feedly_client import Entry, FeedlyClient
from miniflux_entries_processor.sources.base_source import BaseStreamSource


class AllSource(BaseStreamSource):
    """Stream source for the All feed (global.all)."""

    name: Literal["all"] = "all"

    def fetch_entries(self, client: FeedlyClient) -> Generator[Entry]:
        """Fetch entries from the All feed in Feedly."""
        stream_id = f"user/{client.user_id}/category/global.all"
        return client.fetch_entries(stream_id)
