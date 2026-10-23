"""Remove from Feedly tag action."""

from functools import cached_property
from typing import Annotated, Literal

from logzero import logger
from pydantic import Field
from pydantic.types import StringConstraints

from miniflux_entries_processor.actions.base_action import BaseAction
from miniflux_entries_processor.feedly_client import (
    Entry,
    FeedlyClient,
    create_feedly_client,
)
from miniflux_entries_processor.settings import FeedlySettings


class RemoveFromFeedlyTagAction(BaseAction):
    """An action that removes Feedly entries from a Feedly tag (e.g. saved)."""

    name: Literal["remove_from_feedly_tag"] = "remove_from_feedly_tag"
    tag: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    feedly_settings: FeedlySettings = Field(default_factory=FeedlySettings)

    @cached_property
    def _feedly_client(self) -> FeedlyClient:
        """Initialize and cache the Feedly API client."""
        return create_feedly_client(self.feedly_settings.token_dir)

    def _process(self, entry: Entry) -> None:
        """Process a Feedly entry by removing it from the configured tag."""
        self._feedly_client.remove_entry_from_tag(self.tag, entry.id)
        logger.info(
            f"Removed entry from Feedly tag: {entry.title!r} (entry ID: {entry.id})"
        )
