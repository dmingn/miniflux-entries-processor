"""FeedIdInListCondition module."""

from typing import Literal

from miniflux_entries_processor.conditions.base_condition import BaseCondition
from miniflux_entries_processor.miniflux_client import Entry


class FeedIdInListCondition(BaseCondition):
    """Condition that matches when the entry's feed ID is in a given set."""

    name: Literal["feed_id_in_list"] = "feed_id_in_list"
    feed_ids: frozenset[int]

    def matches(self, entry: Entry) -> bool:
        """Return True if the entry's feed ID is in the provided set."""
        return entry.feed.id in self.feed_ids
