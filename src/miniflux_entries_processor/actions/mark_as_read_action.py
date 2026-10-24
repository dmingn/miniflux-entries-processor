"""Mark Miniflux entry as read action."""

from functools import cached_property
from typing import Literal

from logzero import logger

from miniflux_entries_processor.actions.base_action import BaseAction
from miniflux_entries_processor.miniflux_client import (
    Entry,
    MinifluxClient,
    create_miniflux_client,
)


class MarkAsReadAction(BaseAction):
    """An action that marks a Miniflux entry as read."""

    name: Literal["mark_as_read"] = "mark_as_read"

    @cached_property
    def _miniflux_client(self) -> MinifluxClient:
        """Initialize and cache the Miniflux API client."""
        return create_miniflux_client()

    def _process(self, entry: Entry) -> None:
        """Process a Miniflux entry by marking it as read."""
        self._miniflux_client.mark_entry_as_read(entry.id)
        logger.info(f"Marked entry as read: {entry.title!r} (entry ID: {entry.id})")
