"""Tests for the RunInSequenceAction."""

from collections.abc import Callable

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

from miniflux_entries_processor.actions import LogAction, RunInSequenceAction
from miniflux_entries_processor.feedly_client import Entry, Origin, Summary


@pytest.fixture
def entry_builder() -> Callable[..., Entry]:
    """Fixture for a builder function to create Entry objects."""

    def _builder(
        entry_id: str = "entry_abc",
        title: str = "Test Entry",
    ) -> Entry:
        return Entry(
            id=entry_id,
            title=title,
            canonical_url="http://example.com/test",
            origin=Origin(
                title="Test Origin",
                html_url="http://example.com",
                stream_id="test_stream_id",
            ),
            summary=Summary(content="Summary"),
            published=1234567890,
            author=None,
        )

    return _builder


def test_RunInSequenceAction_process_runs_actions_in_order(
    entry_builder: Callable[..., Entry],
    mocker: MockerFixture,
) -> None:
    # arrange: side_effect records call order (args[0] is self)
    call_order: list[LogAction] = []

    def track(self: LogAction, _entry: Entry) -> None:
        call_order.append(self)

    mocker.patch.object(LogAction, "process", side_effect=track, autospec=True)

    actions = (LogAction(), LogAction(), LogAction())
    sequence = RunInSequenceAction(actions=actions)
    entry = entry_builder()

    # act
    sequence.process(entry)

    # assert
    assert call_order == list(actions)


def test_RunInSequenceAction_process_runs_nested_sequence_in_order(
    entry_builder: Callable[..., Entry],
    mocker: MockerFixture,
) -> None:
    # arrange: nested sequence contains action2; outer runs action1, nested, action3
    call_order: list[LogAction] = []

    def track(self: LogAction, _entry: Entry) -> None:
        call_order.append(self)

    mocker.patch.object(LogAction, "process", side_effect=track, autospec=True)

    action1 = LogAction()
    action2 = LogAction()
    action3 = LogAction()
    nested = RunInSequenceAction(actions=(action2,))
    sequence = RunInSequenceAction(actions=(action1, nested, action3))
    entry = entry_builder()

    # act
    sequence.process(entry)

    # assert
    assert call_order == [action1, action2, action3]


def test_RunInSequenceAction_process_stops_on_first_failure(
    entry_builder: Callable[..., Entry],
    mocker: MockerFixture,
) -> None:
    # arrange: 1st call returns, 2nd raises, 3rd never reached
    msg = "intentional failure"
    mock_process = mocker.patch.object(
        LogAction, "process", side_effect=[None, ValueError(msg)]
    )

    sequence = RunInSequenceAction(actions=(LogAction(), LogAction(), LogAction()))
    entry = entry_builder()

    # act & assert
    with pytest.raises(ValueError, match=msg):
        sequence.process(entry)

    assert mock_process.call_count == 2


def test_RunInSequenceAction_rejects_empty_actions() -> None:
    # act & assert
    with pytest.raises(ValidationError):
        RunInSequenceAction(actions=())
