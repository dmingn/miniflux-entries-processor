"""Run in sequence action."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import Field

from miniflux_entries_processor.actions.base_action import BaseAction

if TYPE_CHECKING:
    from miniflux_entries_processor.actions import Action
    from miniflux_entries_processor.miniflux_client import Entry


class RunInSequenceAction(BaseAction):
    """An action that runs multiple actions in sequence.

    If any action raises an exception, subsequent actions are not executed
    and the exception is propagated.
    """

    name: Literal["run_in_sequence"] = "run_in_sequence"
    actions: tuple[Action, ...] = Field(min_length=1)

    def _process(self, entry: Entry) -> None:
        """Process a Miniflux entry by running each sub-action in sequence."""
        for action in self.actions:
            action.process(entry)
