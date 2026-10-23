"""Actions for Feedly entries."""

from miniflux_entries_processor.actions.add_todoist_task_action import (
    AddTodoistTaskAction,
)
from miniflux_entries_processor.actions.log_action import LogAction
from miniflux_entries_processor.actions.remove_from_feedly_tag_action import (
    RemoveFromFeedlyTagAction,
)
from miniflux_entries_processor.actions.run_in_sequence_action import (
    RunInSequenceAction,
)

__all__ = [
    "AddTodoistTaskAction",
    "LogAction",
    "RemoveFromFeedlyTagAction",
    "RunInSequenceAction",
]

Action = (
    LogAction | AddTodoistTaskAction | RemoveFromFeedlyTagAction | RunInSequenceAction
)

RunInSequenceAction.model_rebuild()
