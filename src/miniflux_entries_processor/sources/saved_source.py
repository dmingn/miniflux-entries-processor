"""Saved entries stream source."""

from collections.abc import Generator
from typing import Literal

from miniflux_entries_processor.feedly_client import Entry, FeedlyClient
from miniflux_entries_processor.sources.base_source import BaseStreamSource


class SavedSource(BaseStreamSource):
    """Stream source for saved entries."""

    name: Literal["saved"] = "saved"

    def fetch_entries(self, client: FeedlyClient) -> Generator[Entry]:
        """Fetch saved entries from Feedly."""
        stream_id = f"user/{client.user_id}/tag/global.saved"
        return client.fetch_entries(stream_id)
