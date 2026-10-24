"""Tests for the MarkAsReadAction."""

from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from miniflux_entries_processor.actions.mark_as_read_action import MarkAsReadAction
from tests.helpers import make_entry


def test_MarkAsReadAction_process_marks_entry_as_read_and_logs(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_client = MagicMock()
    mocker.patch(
        "miniflux_entries_processor.actions.mark_as_read_action.create_miniflux_client",
        return_value=mock_client,
    )
    mock_logger = mocker.patch(
        "miniflux_entries_processor.actions.mark_as_read_action.logger"
    )
    action = MarkAsReadAction()
    entry = make_entry(entry_id=99, title="Unread", status="unread")

    # act
    action.process(entry)

    # assert
    mock_client.mark_entry_as_read.assert_called_once_with(99)
    mock_logger.info.assert_called_once()
    assert "Marked entry as read" in mock_logger.info.call_args.args[0]


def test_MarkAsReadAction_can_be_instantiated() -> None:
    # arrange / act
    action = MarkAsReadAction()

    # assert
    assert action.name == "mark_as_read"
