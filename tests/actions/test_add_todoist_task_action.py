"""Tests for the AddTodoistTaskAction."""

from collections.abc import Callable
from typing import Literal
from unittest.mock import MagicMock

import pytest
from pydantic import SecretStr
from pytest_mock import MockerFixture

from miniflux_entries_processor.actions.add_todoist_task_action import (
    AddTodoistTaskAction,
)
from miniflux_entries_processor.exceptions import (
    ActionSkippedDueToPersistentError,
    TodoistApiError,
)
from miniflux_entries_processor.miniflux_client import Entry
from miniflux_entries_processor.settings import TodoistSettings
from tests.helpers import make_entry, make_httpx_status_error


@pytest.fixture
def mock_todoist_api(mocker: MockerFixture) -> MagicMock:
    """Fixture for mocking TodoistAPI."""
    mock_api: MagicMock = mocker.patch(
        "miniflux_entries_processor.actions.add_todoist_task_action.TodoistAPI"
    )
    return mock_api


@pytest.fixture
def add_todoist_task_action_factory() -> Callable[..., AddTodoistTaskAction]:
    """Fixture for AddTodoistTaskAction factory."""
    project_id = "test_project_id"

    def _factory(
        due_string: str | None = None,
        priority: Literal[1, 2, 3, 4] | None = None,
        labels: frozenset[str] | None = None,
    ) -> AddTodoistTaskAction:
        action = AddTodoistTaskAction(
            project_id=project_id,
            due_string=due_string,
            priority=priority,
            labels=labels,
        )
        action._todoist_settings = TodoistSettings.model_construct(  # noqa: SLF001
            todoist_api_token=SecretStr("test_token")
        )
        return action

    return _factory


@pytest.fixture
def entry_builder() -> Callable[..., Entry]:
    """Fixture for a builder function to create Entry objects."""

    def _builder(
        title: str = "Test Entry",
        url: str = "http://example.com/test",
        content: str = "Test Summary Content",
    ) -> Entry:
        return make_entry(title=title, url=url, content=content)

    return _builder


def test_AddTodoistTaskAction_process_creates_task_without_optional_params(
    mock_todoist_api: MagicMock,
    add_todoist_task_action_factory: Callable[..., AddTodoistTaskAction],
    entry_builder: Callable[..., Entry],
) -> None:
    # arrange
    sample_entry = entry_builder()
    action = add_todoist_task_action_factory()
    mock_instance = mock_todoist_api.return_value
    mock_instance.add_task.return_value.id = "task_123"
    mock_instance.add_task.return_value.content = "Test Task"

    # act
    action.process(sample_entry)

    # assert
    mock_instance.add_task.assert_called_once_with(
        content="Test Entry - http://example.com/test",
        project_id=action.project_id,
        description="Test Summary Content",
        priority=None,
        due_string=None,
        labels=None,
    )


def test_AddTodoistTaskAction_process_creates_task_with_all_optional_params(
    mock_todoist_api: MagicMock,
    add_todoist_task_action_factory: Callable[..., AddTodoistTaskAction],
    entry_builder: Callable[..., Entry],
) -> None:
    # arrange
    due_string = "today"
    priority: Literal[1, 2, 3, 4] = 2
    labels = frozenset({"reading"})

    action_with_params = add_todoist_task_action_factory(
        due_string=due_string, priority=priority, labels=labels
    )
    entry = entry_builder(
        title="Entry with Params",
        url="http://example.com/params",
        content="Summary for params",
    )
    mock_instance = mock_todoist_api.return_value
    mock_instance.add_task.return_value.id = "task_789"
    mock_instance.add_task.return_value.content = "Test Task with Params"

    # act
    action_with_params.process(entry)

    # assert
    mock_instance.add_task.assert_called_once_with(
        content="Entry with Params - http://example.com/params",
        project_id=action_with_params.project_id,
        description="Summary for params",
        priority=priority,
        due_string=due_string,
        labels=["reading"],
    )


def test_AddTodoistTaskAction_process_raises_ValueError_when_todoist_api_token_is_not_set(
    entry_builder: Callable[..., Entry],
) -> None:
    # arrange
    action = AddTodoistTaskAction(project_id="test_project_id")
    action._todoist_settings = TodoistSettings.model_construct(  # noqa: SLF001
        todoist_api_token=None
    )
    entry = entry_builder()

    # act & assert
    with pytest.raises(
        ValueError,
        match=r"TODOIST_API_TOKEN must be set",
    ):
        action.process(entry)


def test_AddTodoistTaskAction_process_raises_ValueError_for_entry_without_url(
    add_todoist_task_action_factory: Callable[..., AddTodoistTaskAction],
    entry_builder: Callable[..., Entry],
) -> None:
    # arrange
    entry = entry_builder(url="", title="Test Entry No URL", content="")
    action = add_todoist_task_action_factory()

    # act & assert
    with pytest.raises(
        ValueError,
        match=r"Entry must have a URL to be processed by AddTodoistTaskAction\.",
    ):
        action.process(entry)


def test_AddTodoistTaskAction_process_raises_error_when_add_task_fails(
    mock_todoist_api: MagicMock,
    add_todoist_task_action_factory: Callable[..., AddTodoistTaskAction],
    entry_builder: Callable[..., Entry],
) -> None:
    # arrange
    sample_entry = entry_builder()
    action = add_todoist_task_action_factory()
    mock_instance = mock_todoist_api.return_value
    mock_instance.add_task.side_effect = Exception("API Error")

    # act & assert
    with pytest.raises(Exception, match="API Error"):
        action.process(sample_entry)

    mock_instance.add_task.assert_called_once()


def test_AddTodoistTaskAction_process_sets_persistent_error_and_skips_subsequent_calls_on_403(
    mock_todoist_api: MagicMock,
    add_todoist_task_action_factory: Callable[..., AddTodoistTaskAction],
    entry_builder: Callable[..., Entry],
) -> None:
    # arrange
    sample_entry = entry_builder()
    action = add_todoist_task_action_factory()
    mock_instance = mock_todoist_api.return_value

    mock_instance.add_task.side_effect = make_httpx_status_error(403)

    # act & assert (first call)
    with pytest.raises(TodoistApiError) as exc_info:
        action.process(sample_entry)
    assert exc_info.value.details["status_code"] == 403

    # act & assert (second call)
    with pytest.raises(ActionSkippedDueToPersistentError) as exc_info_skip:
        action.process(sample_entry)

    assert "persistent error occurred previously" in str(exc_info_skip.value)
    assert mock_instance.add_task.call_count == 1


def test_AddTodoistTaskAction_process_does_not_set_persistent_error_on_500(
    mock_todoist_api: MagicMock,
    add_todoist_task_action_factory: Callable[..., AddTodoistTaskAction],
    entry_builder: Callable[..., Entry],
) -> None:
    # arrange
    sample_entry = entry_builder()
    action = add_todoist_task_action_factory()
    mock_instance = mock_todoist_api.return_value

    mock_instance.add_task.side_effect = make_httpx_status_error(500)

    # act & assert (first call)
    with pytest.raises(TodoistApiError) as exc_info:
        action.process(sample_entry)
    assert exc_info.value.details["status_code"] == 500

    # act & assert (second call)
    with pytest.raises(TodoistApiError) as exc_info_retry:
        action.process(sample_entry)
    assert exc_info_retry.value.details["status_code"] == 500

    assert mock_instance.add_task.call_count == 6
