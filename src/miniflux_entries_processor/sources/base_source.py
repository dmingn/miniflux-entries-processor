"""Base class for entry sources."""

from abc import ABC, abstractmethod
from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict

from miniflux_entries_processor.miniflux_client import Entry, MinifluxClient


class BaseSource(ABC, BaseModel):
    """Base class for sources that fetch entries from Miniflux."""

    name: str
    model_config = ConfigDict(frozen=True)

    @abstractmethod
    def fetch_entries(self, client: MinifluxClient) -> Iterable[Entry]:
        """Fetch entries from this source using the given client."""
        ...
