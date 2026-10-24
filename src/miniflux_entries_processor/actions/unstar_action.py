"""Unstar Miniflux entry action."""

from functools import cached_property
from typing import Literal

from logzero import logger

from miniflux_entries_processor.actions.base_action import BaseAction
from miniflux_entries_processor.miniflux_client import (
    Entry,
    MinifluxClient,
    create_miniflux_client,
)


class UnstarAction(BaseAction):
    """An action that removes the star from a Miniflux entry."""

    name: Literal["unstar"] = "unstar"

    @cached_property
    def _miniflux_client(self) -> MinifluxClient:
        """Initialize and cache the Miniflux API client."""
        return create_miniflux_client()

    def _process(self, entry: Entry) -> None:
        """Process a Miniflux entry by unstarring it when currently starred."""
        if self._miniflux_client.unstar_entry(entry.id):
            logger.info(f"Unstarred entry: {entry.title!r} (entry ID: {entry.id})")
