"""Add Todoist task action."""

from typing import Literal

from logzero import logger
from pydantic import Field
from todoist_api_python.api import TodoistAPI

from miniflux_entries_processor.actions.base_action import BaseAction
from miniflux_entries_processor.exceptions import TodoistApiError
from miniflux_entries_processor.feedly_client import Entry
from miniflux_entries_processor.settings import TodoistSettings
from miniflux_entries_processor.todoist_client import add_task_with_retry


class AddTodoistTaskAction(BaseAction):
    """An action that adds Feedly entries as tasks in Todoist."""

    name: Literal["add_todoist_task"] = "add_todoist_task"
    project_id: str
    due_string: str | None = None
    priority: Literal[1, 2, 3, 4] | None = None
    labels: frozenset[str] | None = None
    todoist_settings: TodoistSettings = Field(default_factory=TodoistSettings)

    def _process(self, entry: Entry) -> None:
        """Process a Feedly entry by adding it as a task to Todoist."""
        if self.todoist_settings.todoist_api_token is None:
            error_message = "TODOIST_API_TOKEN must be set (e.g. via environment or .env) when using add_todoist_task action"
            raise ValueError(error_message)

        if entry.effective_url is None:
            error_message = "Entry must have a URL (canonical_url or alternate) to be processed by AddTodoistTaskAction."
            raise ValueError(error_message)

        api_token = self.todoist_settings.todoist_api_token.get_secret_value()
        client = TodoistAPI(api_token)

        task_content = f"{entry.title} - {entry.effective_url}"

        try:
            task = add_task_with_retry(
                client,
                content=task_content,
                project_id=self.project_id,
                priority=self.priority,
                due_string=self.due_string,
                description=entry.summary.content if entry.summary else None,
                labels=self.labels,
            )
        except TodoistApiError as exc:
            if exc.details.get("status_code") in {401, 403}:
                self._persistent_error = exc
            raise

        logger.info(f"Added task to Todoist: {task.content} (ID: {task.id})")
