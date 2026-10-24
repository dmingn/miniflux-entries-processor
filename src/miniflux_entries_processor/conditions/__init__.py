"""Conditions for filtering Miniflux entries."""

from miniflux_entries_processor.conditions.all_of_condition import AllOfCondition
from miniflux_entries_processor.conditions.feed_id_in_list_condition import (
    FeedIdInListCondition,
)
from miniflux_entries_processor.conditions.match_all_condition import (
    MatchAllCondition,
)
from miniflux_entries_processor.conditions.regex_partial_match_condition import (
    RegexPartialMatchCondition,
)

__all__ = [
    "AllOfCondition",
    "FeedIdInListCondition",
    "MatchAllCondition",
    "RegexPartialMatchCondition",
]

Condition = (
    MatchAllCondition
    | FeedIdInListCondition
    | RegexPartialMatchCondition
    | AllOfCondition
)

AllOfCondition.model_rebuild()
