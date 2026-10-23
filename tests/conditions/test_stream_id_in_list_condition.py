"""Tests for the StreamIdInListCondition."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from miniflux_entries_processor.conditions import StreamIdInListCondition
from miniflux_entries_processor.feedly_client import Entry, Origin


@pytest.mark.parametrize(
    ("entry", "stream_ids", "expected"),
    [
        pytest.param(
            Entry(
                id="entry_with_origin",
                title="Entry with origin",
                origin=Origin(
                    html_url="http://example.com",
                    stream_id="feed/example.com/1",
                    title="Test Feed",
                ),
            ),
            frozenset({"feed/example.com/1", "feed/example.com/2"}),
            True,
            id="origin_and_stream_id_in_list",
        ),
        pytest.param(
            Entry(
                id="entry_with_origin",
                title="Entry with origin",
                origin=Origin(
                    html_url="http://example.com",
                    stream_id="feed/example.com/1",
                    title="Test Feed",
                ),
            ),
            frozenset({"feed/example.com/99"}),
            False,
            id="origin_and_stream_id_not_in_list",
        ),
        pytest.param(
            Entry(
                id="entry_without_origin",
                title="Entry without origin",
                origin=None,
            ),
            frozenset({"feed/example.com/1"}),
            False,
            id="no_origin",
        ),
    ],
)
def test_StreamIdInListCondition_matches_returns_expected_for_entry_and_stream_ids(
    entry: Entry,
    stream_ids: frozenset[str],
    expected: bool,
) -> None:
    # arrange
    condition = StreamIdInListCondition(
        name="stream_id_in_list",
        stream_ids=stream_ids,
    )

    # act
    result = condition.matches(entry)

    # assert
    assert result is expected


def test_StreamIdInListCondition_can_be_instantiated() -> None:
    # arrange & act
    condition = StreamIdInListCondition.model_validate(
        {
            "name": "stream_id_in_list",
            "stream_ids": ["feed/example.com/1", "feed/example.com/2"],
        }
    )

    # assert
    assert isinstance(condition, StreamIdInListCondition)
    assert condition.name == "stream_id_in_list"
    assert condition.stream_ids == frozenset(
        {"feed/example.com/1", "feed/example.com/2"}
    )


@pytest.mark.parametrize(
    "config",
    [
        pytest.param({"name": "stream_id_in_list"}, id="missing_stream_ids"),
        pytest.param(
            {
                "name": "stream_id_in_list",
                "stream_ids": "not_a_list",
            },
            id="wrong_type_stream_ids",
        ),
    ],
)
def test_StreamIdInListCondition_raises_ValidationError_for_invalid_config(
    config: dict[str, Any],
) -> None:
    # act & assert
    with pytest.raises(ValidationError):
        StreamIdInListCondition.model_validate(config)
