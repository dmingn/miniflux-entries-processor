"""Tests for the LogAction."""

from typing import Literal
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

from miniflux_entries_processor.actions.log_action import LogAction
from miniflux_entries_processor.feedly_client import Entry


@pytest.fixture
def mock_logger(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("miniflux_entries_processor.actions.log_action.logger")


@pytest.fixture
def mock_entry() -> Entry:
    return Entry(
        id="entry_id",
        title="Test Entry Title",
        canonical_url="http://example.com/entry",
    )


def test_LogAction_can_be_instantiated() -> None:
    # arrange & act
    action = LogAction(level="info")

    # assert
    assert isinstance(action, LogAction)
    assert action.name == "log"
    assert action.level == "info"


def test_LogAction_defaults_to_info_level() -> None:
    # arrange & act
    action = LogAction()

    # assert
    assert action.level == "info"


@pytest.mark.parametrize(
    ("level", "expected_log_method"),
    [
        pytest.param("info", "info", id="info"),
        pytest.param("debug", "debug", id="debug"),
        pytest.param("warning", "warning", id="warning"),
        pytest.param("error", "error", id="error"),
    ],
)
def test_LogAction_process_logs_at_configured_level(
    level: Literal["info", "debug", "warning", "error"],
    expected_log_method: str,
    mock_logger: MagicMock,
    mock_entry: Entry,
) -> None:
    # arrange
    action = LogAction(level=level)

    # act
    action.process(mock_entry)

    # assert
    log_message = (
        f"Processing entry: {mock_entry.title} (URL: {mock_entry.canonical_url})"
    )

    if expected_log_method == "info":
        mock_logger.info.assert_called_once_with(log_message)
    elif expected_log_method == "debug":
        mock_logger.debug.assert_called_once_with(log_message)
    elif expected_log_method == "warning":
        mock_logger.warning.assert_called_once_with(log_message)
    elif expected_log_method == "error":
        mock_logger.error.assert_called_once_with(log_message)
    else:
        pytest.fail(f"Unexpected log level: {level}")


def test_LogAction_raises_ValidationError_for_invalid_level() -> None:
    # act & assert
    with pytest.raises(ValidationError):
        LogAction(level="invalid")  # type: ignore[arg-type, unused-ignore]
