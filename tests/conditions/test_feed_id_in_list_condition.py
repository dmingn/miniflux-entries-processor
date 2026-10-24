"""Tests for FeedIdInListCondition."""

import pytest
from pydantic import ValidationError

from miniflux_entries_processor.conditions.feed_id_in_list_condition import (
    FeedIdInListCondition,
)
from tests.helpers import make_entry


@pytest.mark.parametrize(
    ("feed_id", "feed_ids", "expected"),
    [
        pytest.param(42, frozenset({42, 99}), True, id="feed_id_in_list"),
        pytest.param(42, frozenset({1, 2}), False, id="feed_id_not_in_list"),
    ],
)
def test_FeedIdInListCondition_matches_returns_expected(
    feed_id: int,
    feed_ids: frozenset[int],
    expected: bool,
) -> None:
    # arrange
    condition = FeedIdInListCondition(feed_ids=feed_ids)
    entry = make_entry(feed_id=feed_id)

    # act
    result = condition.matches(entry)

    # assert
    assert result is expected


def test_FeedIdInListCondition_can_be_instantiated() -> None:
    # arrange / act
    condition = FeedIdInListCondition(feed_ids=frozenset({1}))

    # assert
    assert condition.name == "feed_id_in_list"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({}, id="missing_feed_ids"),
        pytest.param({"feed_ids": ["not-an-int"]}, id="wrong_type_feed_ids"),
    ],
)
def test_FeedIdInListCondition_raises_ValidationError_for_invalid_config(
    payload: dict[str, object],
) -> None:
    # arrange / act / assert
    with pytest.raises(ValidationError):
        FeedIdInListCondition.model_validate(payload)
