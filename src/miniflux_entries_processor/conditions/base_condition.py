"""BaseCondition module."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict

from miniflux_entries_processor.miniflux_client import Entry


class BaseCondition(ABC, BaseModel):
    """Base class for rule conditions."""

    model_config = ConfigDict(frozen=True)

    @abstractmethod
    def matches(self, entry: Entry) -> bool:
        """Return True if the entry matches the condition."""
