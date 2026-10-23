"""Tests for the process module."""

from typing import cast
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from miniflux_entries_processor.actions import LogAction
from miniflux_entries_processor.conditions import MatchAllCondition
from miniflux_entries_processor.config_loader import Rule
from miniflux_entries_processor.exceptions import ActionSkippedDueToPersistentError
from miniflux_entries_processor.feedly_client import Entry
from miniflux_entries_processor.process import process_entries, process_entry
from miniflux_entries_processor.sources import SavedSource


@pytest.fixture
def mock_entry() -> Entry:
    """Fixture for a mock Entry."""
    return Entry(
        id="entry1",
        title="Test Entry",
        canonical_url="http://example.com/entry1",
        published=1234567890,
    )


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
        source=SavedSource(),
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
    process_entry(mock_entry, mock_rule)

    # assert
    cast("MagicMock", mock_rule.condition).matches.assert_called_once_with(mock_entry)
    cast("MagicMock", mock_rule.action).process.assert_called_once_with(mock_entry)


def test_process_entry_does_not_call_action_when_rule_does_not_match(
    mock_entry: Entry,
    mock_rule: Rule,
) -> None:
    # arrange
    cast("MagicMock", mock_rule.condition).matches.return_value = False

    # act
    process_entry(mock_entry, mock_rule)

    # assert
    cast("MagicMock", mock_rule.condition).matches.assert_called_once_with(mock_entry)
    cast("MagicMock", mock_rule.action).process.assert_not_called()


def test_process_entry_handles_exception_when_matches_raises(
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
    process_entry(mock_entry, mock_rule)

    # assert
    cast("MagicMock", mock_rule.condition).matches.assert_called_once_with(mock_entry)
    cast("MagicMock", mock_rule.action).process.assert_not_called()
    mock_logger_exception.assert_called_once()


def test_process_entry_handles_exception_when_action_raises(
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
    process_entry(mock_entry, mock_rule)

    # assert
    cast("MagicMock", mock_rule.condition).matches.assert_called_once_with(mock_entry)
    cast("MagicMock", mock_rule.action).process.assert_called_once_with(mock_entry)
    mock_logger_exception.assert_called_once()


def test_process_entry_logs_error_when_action_raises_ActionSkippedDueToPersistentError(
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
    process_entry(mock_entry, mock_rule)

    # assert
    cast("MagicMock", mock_rule.action).process.assert_called_once_with(mock_entry)
    mock_logger_error.assert_called_once()
    assert "test-rule" in mock_logger_error.call_args.args[0]
    assert "skipped due to persistent error" in mock_logger_error.call_args.args[0]
    mock_logger_exception.assert_not_called()


def test_process_entries_calls_process_entry_for_each_entry_and_rule(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_process_entry = mocker.patch(
        "miniflux_entries_processor.process.process_entry"
    )
    entry1, entry2 = MagicMock(spec=Entry), MagicMock(spec=Entry)
    rule1, rule2 = MagicMock(spec=Rule), MagicMock(spec=Rule)
    entries = [entry1, entry2]
    rules = [rule1, rule2]

    # act
    process_entries(entries, rules)

    # assert
    expected_calls = [
        mocker.call(entry1, rule1),
        mocker.call(entry1, rule2),
        mocker.call(entry2, rule1),
        mocker.call(entry2, rule2),
    ]
    assert mock_process_entry.call_args_list == expected_calls
