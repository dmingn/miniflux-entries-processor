"""Actions for Miniflux entries."""

from miniflux_entries_processor.actions.add_todoist_task_action import (
    AddTodoistTaskAction,
)
from miniflux_entries_processor.actions.log_action import LogAction
from miniflux_entries_processor.actions.mark_as_read_action import MarkAsReadAction
from miniflux_entries_processor.actions.run_in_sequence_action import (
    RunInSequenceAction,
)
from miniflux_entries_processor.actions.star_action import StarAction
from miniflux_entries_processor.actions.unstar_action import UnstarAction

__all__ = [
    "AddTodoistTaskAction",
    "LogAction",
    "MarkAsReadAction",
    "RunInSequenceAction",
    "StarAction",
    "UnstarAction",
]

Action = (
    LogAction
    | AddTodoistTaskAction
    | UnstarAction
    | StarAction
    | MarkAsReadAction
    | RunInSequenceAction
)

RunInSequenceAction.model_rebuild()
