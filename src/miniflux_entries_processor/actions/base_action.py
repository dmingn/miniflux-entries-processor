"""Base class for rule actions."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict, PrivateAttr

from miniflux_entries_processor.exceptions import ActionSkippedDueToPersistentError
from miniflux_entries_processor.miniflux_client import Entry


class BaseAction(ABC, BaseModel):
    """Base class for rule actions."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    _persistent_error: Exception | None = PrivateAttr(default=None)

    def process(self, entry: Entry) -> None:
        """Process a single Miniflux entry.

        Raises
        ------
            ActionSkippedDueToPersistentError: If a persistent error occurred previously.
        """
        if self._persistent_error is not None:
            msg = f"Action skipped because a persistent error occurred previously: {self._persistent_error}"
            raise ActionSkippedDueToPersistentError(msg) from self._persistent_error

        self._process(entry)

    @abstractmethod
    def _process(self, entry: Entry) -> None:
        """Process a single Miniflux entry (implementation)."""
