"""Conditions for filtering Feedly entries."""

from miniflux_entries_processor.conditions.match_all_condition import (
    MatchAllCondition,
)
from miniflux_entries_processor.conditions.regex_partial_match_condition import (
    RegexPartialMatchCondition,
)
from miniflux_entries_processor.conditions.stream_id_in_list_condition import (
    StreamIdInListCondition,
)

__all__ = [
    "MatchAllCondition",
    "RegexPartialMatchCondition",
    "StreamIdInListCondition",
]

Condition = MatchAllCondition | StreamIdInListCondition | RegexPartialMatchCondition
