"""Tests for the process module."""

from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from miniflux_entries_processor.actions import LogAction
from miniflux_entries_processor.conditions import MatchAllCondition
from miniflux_entries_processor.config_loader import Rule
from miniflux_entries_processor.exceptions import (
    ActionSkippedDueToPersistentError,
    ProcessingFailuresError,
)
from miniflux_entries_processor.miniflux_client import Entry
from miniflux_entries_processor.process import process, process_entries, process_entry
from miniflux_entries_processor.sources import StarredSource
from tests.helpers import make_entry


@pytest.fixture
def mock_entry() -> Entry:
    """Fixture for a mock Entry."""
    return make_entry(entry_id=1, title="Test Entry")


@pytest.fixture
def mock_condition(mocker: MockerFixture) -> MatchAllCondition:
    """Fixture for a mock MatchAllCondition."""
    mock = mocker.create_autospec(MatchAllCondition)
    mock.name = "match_all"
    return mock


@pytest.fixture
def mock_action(mocker: MockerFixture) -> LogAction:
    """Fixture for a mock LogAction."""
    mock = mocker.create_autospec(LogAction)
    mock.name = "log"
    return mock


@pytest.fixture
def mock_rule(mock_condition: MatchAllCondition, mock_action: LogAction) -> Rule:
    """Fixture for a mock Rule."""
    return Rule(
        name="test-rule",
        source=StarredSource(),
        condition=mock_condition,
        action=mock_action,
    )


def test_process_entry_calls_action_when_rule_matches(
    mock_entry: Entry,
    mock_rule: Rule,
) -> None:
    # arrange
    cast("MagicMock", mock_rule.condition).matches.return_value = True

    # act
    result = process_entry(mock_entry, mock_rule)

    # assert
    assert result is True
    cast("MagicMock", mock_rule.condition).matches.assert_called_once_with(mock_entry)
    cast("MagicMock", mock_rule.action).process.assert_called_once_with(mock_entry)


def test_process_entry_does_not_call_action_when_rule_does_not_match(
    mock_entry: Entry,
    mock_rule: Rule,
) -> None:
    # arrange
    cast("MagicMock", mock_rule.condition).matches.return_value = False

    # act
    result = process_entry(mock_entry, mock_rule)

    # assert
    assert result is True
    cast("MagicMock", mock_rule.condition).matches.assert_called_once_with(mock_entry)
    cast("MagicMock", mock_rule.action).process.assert_not_called()


def test_process_entry_returns_False_when_matches_raises(
    mocker: MockerFixture,
    mock_entry: Entry,
    mock_rule: Rule,
) -> None:
    # arrange
    cast("MagicMock", mock_rule.condition).matches.side_effect = Exception(
        "Test exception"
    )
    mock_logger_exception = mocker.patch(
        "miniflux_entries_processor.process.logger.exception"
    )

    # act
    result = process_entry(mock_entry, mock_rule)

    # assert
    assert result is False
    cast("MagicMock", mock_rule.condition).matches.assert_called_once_with(mock_entry)
    cast("MagicMock", mock_rule.action).process.assert_not_called()
    mock_logger_exception.assert_called_once()


def test_process_entry_returns_False_when_action_raises(
    mocker: MockerFixture,
    mock_entry: Entry,
    mock_rule: Rule,
) -> None:
    # arrange
    cast("MagicMock", mock_rule.condition).matches.return_value = True
    cast("MagicMock", mock_rule.action).process.side_effect = Exception(
        "Test exception"
    )
    mock_logger_exception = mocker.patch(
        "miniflux_entries_processor.process.logger.exception"
    )

    # act
    result = process_entry(mock_entry, mock_rule)

    # assert
    assert result is False
    cast("MagicMock", mock_rule.condition).matches.assert_called_once_with(mock_entry)
    cast("MagicMock", mock_rule.action).process.assert_called_once_with(mock_entry)
    mock_logger_exception.assert_called_once()


def test_process_entry_returns_False_when_action_raises_ActionSkippedDueToPersistentError(
    mocker: MockerFixture,
    mock_entry: Entry,
    mock_rule: Rule,
) -> None:
    # arrange
    cast("MagicMock", mock_rule.condition).matches.return_value = True
    cast(
        "MagicMock", mock_rule.action
    ).process.side_effect = ActionSkippedDueToPersistentError(
        "skipped due to persistent error"
    )
    mock_logger_error = mocker.patch("miniflux_entries_processor.process.logger.error")
    mock_logger_exception = mocker.patch(
        "miniflux_entries_processor.process.logger.exception"
    )

    # act
    result = process_entry(mock_entry, mock_rule)

    # assert
    assert result is False
    cast("MagicMock", mock_rule.action).process.assert_called_once_with(mock_entry)
    mock_logger_error.assert_called_once()
    assert "test-rule" in mock_logger_error.call_args.args[0]
    assert "skipped due to persistent error" in mock_logger_error.call_args.args[0]
    mock_logger_exception.assert_not_called()


def test_process_entries_counts_successes_and_failures(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_process_entry = mocker.patch(
        "miniflux_entries_processor.process.process_entry",
        side_effect=[True, False, True, True],
    )
    entry1, entry2 = MagicMock(spec=Entry), MagicMock(spec=Entry)
    rule1, rule2 = MagicMock(spec=Rule), MagicMock(spec=Rule)

    # act
    successes, failures = process_entries([entry1, entry2], [rule1, rule2])

    # assert
    assert successes == 3
    assert failures == 1
    assert mock_process_entry.call_args_list == [
        mocker.call(entry1, rule1),
        mocker.call(entry1, rule2),
        mocker.call(entry2, rule1),
        mocker.call(entry2, rule2),
    ]


def _write_minimal_config(tmp_path: Path) -> Path:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
rules:
  - name: r
    source: {name: starred}
    condition: {name: match_all}
    action: {name: log}
""",
        encoding="utf-8",
    )
    return config_file


def test_process_raises_ProcessingFailuresError_when_any_failure(
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    # arrange
    config_file = _write_minimal_config(tmp_path)
    mocker.patch(
        "miniflux_entries_processor.process.create_miniflux_client",
        return_value=MagicMock(),
    )
    mocker.patch(
        "miniflux_entries_processor.process.process_entries",
        return_value=(1, 2),
    )
    mock_logger_info = mocker.patch("miniflux_entries_processor.process.logger.info")

    # act & assert
    with pytest.raises(ProcessingFailuresError, match="2 failure"):
        process([config_file])

    assert any(
        "1 succeeded, 2 failed" in str(call.args[0])
        for call in mock_logger_info.call_args_list
    )


def test_process_does_not_raise_when_all_succeed(
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    # arrange
    config_file = _write_minimal_config(tmp_path)
    mocker.patch(
        "miniflux_entries_processor.process.create_miniflux_client",
        return_value=MagicMock(),
    )
    mocker.patch(
        "miniflux_entries_processor.process.process_entries",
        return_value=(4, 0),
    )

    # act / assert — no exception
    process([config_file])
