"""Tests for FeedUrlInListCondition."""

import pytest
from pydantic import ValidationError

from miniflux_entries_processor.conditions.feed_url_in_list_condition import (
    FeedUrlInListCondition,
)
from tests.helpers import make_entry


@pytest.mark.parametrize(
    ("feed_url", "feed_urls", "expected"),
    [
        pytest.param(
            "http://example.com/feed.atom",
            frozenset({"http://example.com/feed.atom", "http://other.com/rss"}),
            True,
            id="feed_url_in_list",
        ),
        pytest.param(
            "http://example.com/feed.atom",
            frozenset({"http://other.com/rss"}),
            False,
            id="feed_url_not_in_list",
        ),
    ],
)
def test_FeedUrlInListCondition_matches_returns_expected(
    feed_url: str,
    feed_urls: frozenset[str],
    expected: bool,
) -> None:
    # arrange
    condition = FeedUrlInListCondition(feed_urls=feed_urls)
    entry = make_entry(feed_url=feed_url)

    # act
    result = condition.matches(entry)

    # assert
    assert result is expected


def test_FeedUrlInListCondition_can_be_instantiated() -> None:
    # arrange / act
    condition = FeedUrlInListCondition(feed_urls=frozenset({"http://example.com/feed"}))

    # assert
    assert condition.name == "feed_url_in_list"


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({}, id="missing_feed_urls"),
        pytest.param({"feed_urls": [1]}, id="wrong_type_feed_urls"),
    ],
)
def test_FeedUrlInListCondition_raises_ValidationError_for_invalid_config(
    payload: dict[str, object],
) -> None:
    # arrange / act / assert
    with pytest.raises(ValidationError):
        FeedUrlInListCondition.model_validate(payload)
