"""Tests for the StarAction."""

from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from miniflux_entries_processor.actions.star_action import StarAction
from tests.helpers import make_entry


def test_StarAction_process_logs_when_star_changes_state(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_client = MagicMock()
    mock_client.star_entry.return_value = True
    mocker.patch(
        "miniflux_entries_processor.actions.star_action.create_miniflux_client",
        return_value=mock_client,
    )
    mock_logger = mocker.patch("miniflux_entries_processor.actions.star_action.logger")
    action = StarAction()
    entry = make_entry(entry_id=99, title="Unstarred", starred=False)

    # act
    action.process(entry)

    # assert
    mock_client.star_entry.assert_called_once_with(99)
    mock_logger.info.assert_called_once()
    assert "Starred entry" in mock_logger.info.call_args.args[0]


def test_StarAction_process_does_not_log_when_already_starred(
    mocker: MockerFixture,
) -> None:
    # arrange
    mock_client = MagicMock()
    mock_client.star_entry.return_value = False
    mocker.patch(
        "miniflux_entries_processor.actions.star_action.create_miniflux_client",
        return_value=mock_client,
    )
    mock_logger = mocker.patch("miniflux_entries_processor.actions.star_action.logger")
    action = StarAction()
    entry = make_entry(entry_id=99, title="Already starred")

    # act
    action.process(entry)

    # assert
    mock_client.star_entry.assert_called_once_with(99)
    mock_logger.info.assert_not_called()


def test_StarAction_can_be_instantiated() -> None:
    # arrange / act
    action = StarAction()

    # assert
    assert action.name == "star"
