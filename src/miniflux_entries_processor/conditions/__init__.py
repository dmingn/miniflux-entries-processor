"""Conditions for filtering Miniflux entries."""

from miniflux_entries_processor.conditions.all_of_condition import AllOfCondition
from miniflux_entries_processor.conditions.any_of_condition import AnyOfCondition
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
    "AnyOfCondition",
    "FeedIdInListCondition",
    "MatchAllCondition",
    "RegexPartialMatchCondition",
]

Condition = (
    MatchAllCondition
    | FeedIdInListCondition
    | RegexPartialMatchCondition
    | AllOfCondition
    | AnyOfCondition
)

AllOfCondition.model_rebuild()
AnyOfCondition.model_rebuild()
