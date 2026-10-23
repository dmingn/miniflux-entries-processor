"""Tests for the MatchAllCondition."""

from miniflux_entries_processor.conditions import MatchAllCondition
from miniflux_entries_processor.feedly_client import Entry


def test_MatchAllCondition_matches_returns_true_for_entry() -> None:
    # arrange
    entry = Entry(id="entry1", title="Test", canonical_url="http://example.com")
    condition = MatchAllCondition(name="match_all")

    # act
    result = condition.matches(entry)

    # assert
    assert result is True


def test_MatchAllCondition_can_be_instantiated() -> None:
    # arrange & act
    condition = MatchAllCondition.model_validate({"name": "match_all"})

    # assert
    assert isinstance(condition, MatchAllCondition)
    assert condition.name == "match_all"
