"""RegexPartialMatchCondition module."""

import re
from functools import cached_property
from typing import Literal, assert_never

from pydantic import Field, field_validator

from miniflux_entries_processor.conditions.base_condition import BaseCondition
from miniflux_entries_processor.miniflux_client import Entry

FieldName = Literal["title", "author", "content", "url"]


class RegexPartialMatchCondition(BaseCondition):
    """Condition that matches when any of the patterns are found in any of the specified fields."""

    name: Literal["regex_partial_match"] = "regex_partial_match"
    fields: tuple[FieldName, ...] = Field(min_length=1)
    patterns: tuple[str, ...] = Field(min_length=1)

    @field_validator("patterns", mode="after")
    @classmethod
    def _validate_patterns_are_compilable(
        cls,
        patterns: tuple[str, ...],
    ) -> tuple[str, ...]:
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as exc:
                msg = f"Invalid regular expression pattern: {pattern!r}"
                raise ValueError(msg) from exc
        return patterns

    @staticmethod
    def _get_field_value(entry: Entry, field_name: FieldName) -> str | None:
        if field_name == "title":
            return entry.title
        if field_name == "author":
            return entry.author
        if field_name == "content":
            return entry.content
        if field_name == "url":
            return entry.url

        assert_never(field_name)

    @cached_property
    def _compiled_patterns(self) -> tuple[re.Pattern[str], ...]:
        return tuple(re.compile(pattern) for pattern in self.patterns)

    def matches(self, entry: Entry) -> bool:
        """Return True if any of the entry's specified fields match any of the patterns."""
        return any(
            pattern.search(value)
            for field_name in self.fields
            if (value := self._get_field_value(entry, field_name)) is not None
            for pattern in self._compiled_patterns
        )
