"""Tests for the RegexPartialMatchCondition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from pydantic import ValidationError

from miniflux_entries_processor.conditions import RegexPartialMatchCondition
from tests.helpers import make_entry

if TYPE_CHECKING:
    from miniflux_entries_processor.miniflux_client import Entry


@pytest.mark.parametrize(
    ("entry", "fields", "patterns", "expected"),
    [
        pytest.param(
            make_entry(title="Hello World", author="Alice"),
            ["title"],
            ["Hello"],
            True,
            id="match_title_single_pattern",
        ),
        pytest.param(
            make_entry(title="Hello World", author="Alice"),
            ["title"],
            ["foo", "World"],
            True,
            id="match_title_multiple_patterns",
        ),
        pytest.param(
            make_entry(title="Hello World", author="Alice"),
            ["author"],
            ["Alice"],
            True,
            id="match_author",
        ),
        pytest.param(
            make_entry(title="Hello World", author="Alice", content="This is content"),
            ["content"],
            ["content"],
            True,
            id="match_content",
        ),
        pytest.param(
            make_entry(
                title="Hello World", author="Alice", url="http://example.com/article"
            ),
            ["url"],
            ["example\\.com"],
            True,
            id="match_url",
        ),
        pytest.param(
            make_entry(title="Hello World", author="Alice"),
            ["title", "author"],
            ["Alice"],
            True,
            id="match_multiple_fields",
        ),
        pytest.param(
            make_entry(title="Hello World", author="Alice"),
            ["title"],
            ["(?i)hello"],
            True,
            id="match_case_insensitive_inline_flag",
        ),
        pytest.param(
            make_entry(title="Hello World", author="Alice"),
            ["title"],
            ["^Hello$"],
            False,
            id="no_match_full_match_required_by_regex",
        ),
        pytest.param(
            make_entry(title="Hello World", author="Alice"),
            ["title"],
            ["foo"],
            False,
            id="no_match_wrong_pattern",
        ),
        pytest.param(
            make_entry(title="Hello World", author=None),
            ["author"],
            ["foo"],
            False,
            id="no_match_field_is_none",
        ),
    ],
)
def test_RegexPartialMatchCondition_matches_returns_expected(
    entry: Entry,
    fields: list[str],
    patterns: list[str],
    expected: bool,
) -> None:
    # arrange
    condition = RegexPartialMatchCondition(
        name="regex_partial_match",
        fields=fields,
        patterns=patterns,
    )

    # act
    result = condition.matches(entry)

    # assert
    assert result is expected


def test_RegexPartialMatchCondition_can_be_instantiated() -> None:
    # arrange & act
    condition = RegexPartialMatchCondition.model_validate(
        {
            "name": "regex_partial_match",
            "fields": ["title", "content"],
            "patterns": ["p1", "p2"],
        }
    )

    # assert
    assert isinstance(condition, RegexPartialMatchCondition)
    assert condition.name == "regex_partial_match"
    assert condition.fields == ("title", "content")
    assert condition.patterns == ("p1", "p2")


@pytest.mark.parametrize(
    "config",
    [
        pytest.param(
            {"name": "regex_partial_match", "patterns": ["p1"]}, id="missing_fields"
        ),
        pytest.param(
            {"name": "regex_partial_match", "fields": ["title"]}, id="missing_patterns"
        ),
        pytest.param(
            {"name": "regex_partial_match", "fields": [], "patterns": ["p1"]},
            id="empty_fields",
        ),
        pytest.param(
            {"name": "regex_partial_match", "fields": ["title"], "patterns": []},
            id="empty_patterns",
        ),
        pytest.param(
            {
                "name": "regex_partial_match",
                "fields": ["invalid_field"],
                "patterns": ["p1"],
            },
            id="invalid_field_name",
        ),
        pytest.param(
            {
                "name": "regex_partial_match",
                "fields": ["title"],
                "patterns": ["["],
            },
            id="invalid_regex_pattern",
        ),
    ],
)
def test_RegexPartialMatchCondition_raises_ValidationError_for_invalid_config(
    config: dict[str, Any],
) -> None:
    # act & assert
    with pytest.raises(ValidationError):
        RegexPartialMatchCondition.model_validate(config)
