"""FeedUrlInListCondition module."""

from typing import Literal

from miniflux_entries_processor.conditions.base_condition import BaseCondition
from miniflux_entries_processor.miniflux_client import Entry


class FeedUrlInListCondition(BaseCondition):
    """Condition that matches when the entry's feed URL is in a given set."""

    name: Literal["feed_url_in_list"] = "feed_url_in_list"
    feed_urls: frozenset[str]

    def matches(self, entry: Entry) -> bool:
        """Return True if the entry's feed URL is in the provided set."""
        return entry.feed.feed_url in self.feed_urls
