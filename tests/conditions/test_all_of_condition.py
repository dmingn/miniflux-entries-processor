"""Tests for AllOfCondition."""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from miniflux_entries_processor.conditions import (
    AllOfCondition,
    FeedIdInListCondition,
    MatchAllCondition,
    RegexPartialMatchCondition,
)
from tests.helpers import make_entry


def test_AllOfCondition_matches_when_all_nested_conditions_match() -> None:
    # arrange
    condition = AllOfCondition(
        conditions=(
            FeedIdInListCondition(feed_ids=frozenset({42})),
            RegexPartialMatchCondition(fields=("title",), patterns=("Test",)),
        )
    )
    entry = make_entry(feed_id=42, title="Test Entry")

    # act / assert
    assert condition.matches(entry) is True


def test_AllOfCondition_does_not_match_when_any_nested_condition_fails() -> None:
    # arrange
    condition = AllOfCondition(
        conditions=(
            FeedIdInListCondition(feed_ids=frozenset({42})),
            RegexPartialMatchCondition(fields=("title",), patterns=("Missing",)),
        )
    )
    entry = make_entry(feed_id=42, title="Test Entry")

    # act / assert
    assert condition.matches(entry) is False


def test_AllOfCondition_supports_nested_all_of() -> None:
    # arrange
    condition = AllOfCondition(
        conditions=(
            MatchAllCondition(),
            AllOfCondition(
                conditions=(FeedIdInListCondition(feed_ids=frozenset({7})),)
            ),
        )
    )
    entry = make_entry(feed_id=7)

    # act / assert
    assert condition.matches(entry) is True


def test_AllOfCondition_short_circuits_on_first_false() -> None:
    # arrange
    first = MagicMock()
    first.matches.return_value = False
    second = MagicMock()
    condition = AllOfCondition.model_construct(conditions=(first, second))
    entry = make_entry()

    # act
    result = condition.matches(entry)

    # assert
    assert result is False
    first.matches.assert_called_once_with(entry)
    second.matches.assert_not_called()


def test_AllOfCondition_can_be_instantiated() -> None:
    # arrange / act
    condition = AllOfCondition(conditions=(MatchAllCondition(),))

    # assert
    assert condition.name == "all_of"


def test_AllOfCondition_rejects_empty_conditions() -> None:
    # act / assert
    with pytest.raises(ValidationError):
        AllOfCondition(conditions=())
