"""Tests for the BaseAction."""

import pytest
from pytest_mock import MockerFixture

from miniflux_entries_processor.actions.base_action import BaseAction
from miniflux_entries_processor.exceptions import ActionSkippedDueToPersistentError
from miniflux_entries_processor.feedly_client import Entry


class ConcreteAction(BaseAction):
    """A concrete action for testing BaseAction."""

    def _process(self, entry: Entry) -> None:
        pass


def test_BaseAction_process_raises_ActionSkippedDueToPersistentError_when_persistent_error_exists(
    mocker: MockerFixture,
) -> None:
    # arrange
    action = ConcreteAction()
    mock_entry = mocker.Mock(spec=Entry)
    persistent_error = Exception("Persistent")
    # Accessing private member for testing purposes
    action._persistent_error = persistent_error  # noqa: SLF001

    # act & assert
    with pytest.raises(ActionSkippedDueToPersistentError) as exc_info:
        action.process(mock_entry)

    assert "persistent error occurred previously" in str(exc_info.value)
    assert exc_info.value.__cause__ is persistent_error


def test_BaseAction_process_calls_internal_process_when_no_persistent_error_exists(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_process = mocker.Mock(return_value=None)

    class MockAction(BaseAction):
        def _process(self, entry: Entry) -> None:
            mock_process(entry)

    action = MockAction()
    mock_entry = mocker.Mock(spec=Entry)

    # act
    action.process(mock_entry)

    # assert
    mock_process.assert_called_once_with(mock_entry)
