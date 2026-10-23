"""StreamIdInListCondition module."""

from typing import Literal

from miniflux_entries_processor.conditions.base_condition import BaseCondition
from miniflux_entries_processor.feedly_client import Entry


class StreamIdInListCondition(BaseCondition):
    """Condition that matches when stream_id is in a given set."""

    name: Literal["stream_id_in_list"] = "stream_id_in_list"
    stream_ids: frozenset[str]

    def matches(self, entry: Entry) -> bool:
        """Return True if the entry's stream_id is in the provided set."""
        return entry.origin is not None and entry.origin.stream_id in self.stream_ids
