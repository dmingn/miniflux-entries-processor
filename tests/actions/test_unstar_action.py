"""Tests for the UnstarAction."""

from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from miniflux_entries_processor.actions.unstar_action import UnstarAction
from tests.helpers import make_entry


def test_UnstarAction_process_logs_when_unstar_changes_state(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_client = MagicMock()
    mock_client.unstar_entry.return_value = True
    mocker.patch(
        "miniflux_entries_processor.actions.unstar_action.create_miniflux_client",
        return_value=mock_client,
    )
    mock_logger = mocker.patch(
        "miniflux_entries_processor.actions.unstar_action.logger"
    )
    action = UnstarAction()
    entry = make_entry(entry_id=99, title="Starred")

    # act
    action.process(entry)

    # assert
    mock_client.unstar_entry.assert_called_once_with(99)
    mock_logger.info.assert_called_once()
    assert "Unstarred entry" in mock_logger.info.call_args.args[0]


def test_UnstarAction_process_does_not_log_when_already_unstarred(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_client = MagicMock()
    mock_client.unstar_entry.return_value = False
    mocker.patch(
        "miniflux_entries_processor.actions.unstar_action.create_miniflux_client",
        return_value=mock_client,
    )
    mock_logger = mocker.patch(
        "miniflux_entries_processor.actions.unstar_action.logger"
    )
    action = UnstarAction()
    entry = make_entry(entry_id=99, title="Already unstarred")

    # act
    action.process(entry)

    # assert
    mock_client.unstar_entry.assert_called_once_with(99)
    mock_logger.info.assert_not_called()


def test_UnstarAction_can_be_instantiated() -> None:
    # arrange / act
    action = UnstarAction()

    # assert
    assert action.name == "unstar"
