"""AnyOfCondition module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from miniflux_entries_processor.conditions.base_condition import BaseCondition

if TYPE_CHECKING:
    from miniflux_entries_processor.conditions import Condition
    from miniflux_entries_processor.miniflux_client import Entry


class AnyOfCondition(BaseCondition):
    """Condition that matches when any nested condition matches."""

    name: Literal["any_of"] = "any_of"
    conditions: tuple[Condition, ...] = Field(min_length=1)

    def matches(self, entry: Entry) -> bool:
        """Return True if any nested condition matches the entry."""
        return any(condition.matches(entry) for condition in self.conditions)
