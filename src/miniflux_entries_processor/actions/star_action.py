"""Star Miniflux entry action."""

from functools import cached_property
from typing import Literal

from logzero import logger

from miniflux_entries_processor.actions.base_action import BaseAction
from miniflux_entries_processor.miniflux_client import (
    Entry,
    MinifluxClient,
    create_miniflux_client,
)


class StarAction(BaseAction):
    """An action that stars a Miniflux entry if it is not currently starred."""

    name: Literal["star"] = "star"

    @cached_property
    def _miniflux_client(self) -> MinifluxClient:
        """Initialize and cache the Miniflux API client."""
        return create_miniflux_client()

    def _process(self, entry: Entry) -> None:
        """Process a Miniflux entry by starring it when currently unstarred."""
        if self._miniflux_client.star_entry(entry.id):
            logger.info(f"Starred entry: {entry.title!r} (entry ID: {entry.id})")
