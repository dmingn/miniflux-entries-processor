"""Tests for AnyOfCondition."""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from miniflux_entries_processor.conditions import (
    AnyOfCondition,
    FeedIdInListCondition,
    MatchAllCondition,
    RegexPartialMatchCondition,
)
from tests.helpers import make_entry


def test_AnyOfCondition_matches_when_any_nested_condition_matches() -> None:
    # arrange
    condition = AnyOfCondition(
        conditions=(
            FeedIdInListCondition(feed_ids=frozenset({99})),
            RegexPartialMatchCondition(fields=("title",), patterns=("Test",)),
        )
    )
    entry = make_entry(feed_id=42, title="Test Entry")

    # act / assert
    assert condition.matches(entry) is True


def test_AnyOfCondition_does_not_match_when_all_nested_conditions_fail() -> None:
    # arrange
    condition = AnyOfCondition(
        conditions=(
            FeedIdInListCondition(feed_ids=frozenset({99})),
            RegexPartialMatchCondition(fields=("title",), patterns=("Missing",)),
        )
    )
    entry = make_entry(feed_id=42, title="Test Entry")

    # act / assert
    assert condition.matches(entry) is False


def test_AnyOfCondition_supports_nested_any_of() -> None:
    # arrange
    condition = AnyOfCondition(
        conditions=(
            FeedIdInListCondition(feed_ids=frozenset({1})),
            AnyOfCondition(
                conditions=(FeedIdInListCondition(feed_ids=frozenset({7})),)
            ),
        )
    )
    entry = make_entry(feed_id=7)

    # act / assert
    assert condition.matches(entry) is True


def test_AnyOfCondition_short_circuits_on_first_true() -> None:
    # arrange
    first = MagicMock()
    first.matches.return_value = True
    second = MagicMock()
    condition = AnyOfCondition.model_construct(conditions=(first, second))
    entry = make_entry()

    # act
    result = condition.matches(entry)

    # assert
    assert result is True
    first.matches.assert_called_once_with(entry)
    second.matches.assert_not_called()


def test_AnyOfCondition_can_be_instantiated() -> None:
    # arrange / act
    condition = AnyOfCondition(conditions=(MatchAllCondition(),))

    # assert
    assert condition.name == "any_of"


def test_AnyOfCondition_rejects_empty_conditions() -> None:
    # act / assert
    with pytest.raises(ValidationError):
        AnyOfCondition(conditions=())
