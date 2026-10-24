"""Actions for Miniflux entries."""

from miniflux_entries_processor.actions.add_todoist_task_action import (
    AddTodoistTaskAction,
)
from miniflux_entries_processor.actions.log_action import LogAction
from miniflux_entries_processor.actions.run_in_sequence_action import (
    RunInSequenceAction,
)
from miniflux_entries_processor.actions.unstar_action import UnstarAction

__all__ = [
    "AddTodoistTaskAction",
    "LogAction",
    "RunInSequenceAction",
    "UnstarAction",
]

Action = LogAction | AddTodoistTaskAction | UnstarAction | RunInSequenceAction

RunInSequenceAction.model_rebuild()
