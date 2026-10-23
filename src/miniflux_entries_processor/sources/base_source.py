"""Base class for stream sources."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict

from miniflux_entries_processor.feedly_client import Entry, FeedlyClient


class BaseStreamSource(ABC, BaseModel):
    """Base class for stream sources that fetch entries from Feedly."""

    name: str
    model_config = ConfigDict(frozen=True)

    @abstractmethod
    def fetch_entries(self, client: FeedlyClient) -> Iterable[Entry]:
        """Fetch entries from this source using the given client."""
        ...
