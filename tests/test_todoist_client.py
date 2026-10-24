"""Tests for the Todoist client."""

from unittest.mock import MagicMock

import httpx
import pytest

from miniflux_entries_processor.exceptions import TodoistApiError
from miniflux_entries_processor.todoist_client import add_task_with_retry
from tests.helpers import make_httpx_status_error


def test_add_task_with_retry_returns_task_on_success() -> None:
    # arrange
    mock_client = MagicMock()
    task = MagicMock()
    task.id = "task_1"
    task.content = "content"
    mock_client.add_task.return_value = task

    # act
    result = add_task_with_retry(
        mock_client,
        content="content",
        project_id="proj_1",
    )

    # assert
    assert result is task
    mock_client.add_task.assert_called_once()
    call_kwargs = mock_client.add_task.call_args.kwargs
    assert call_kwargs["content"] == "content"
    assert call_kwargs["project_id"] == "proj_1"


@pytest.mark.parametrize(
    "retryable_exception",
    [
        pytest.param(make_httpx_status_error(503), id="503"),
        pytest.param(
            httpx.ConnectError("Connection refused"),
            id="connection_error",
        ),
    ],
)
def test_add_task_with_retry_retries_on_retryable_error_then_succeeds(
    retryable_exception: Exception,
) -> None:
    # arrange
    mock_client = MagicMock()
    task = MagicMock()
    task.id = "task_retry"
    task.content = "content"
    mock_client.add_task.side_effect = [retryable_exception, task]

    # act
    result = add_task_with_retry(
        mock_client,
        content="content",
        project_id="proj_1",
    )

    # assert
    assert result is task
    assert mock_client.add_task.call_count == 2


def test_add_task_with_retry_raises_TodoistApiError_after_three_failures() -> None:
    # arrange
    mock_client = MagicMock()
    mock_client.add_task.side_effect = make_httpx_status_error(503)

    # act & assert
    with pytest.raises(TodoistApiError) as exc_info:
        add_task_with_retry(mock_client, content="content", project_id="proj_1")

    assert "Todoist API request failed" in exc_info.value.args[0]
    assert exc_info.value.details["status_code"] == 503
    assert mock_client.add_task.call_count == 3


def test_add_task_with_retry_raises_TodoistApiError_on_400() -> None:
    # arrange: 400 is not retried, add_task_with_retry wraps in TodoistApiError
    mock_client = MagicMock()
    mock_client.add_task.side_effect = make_httpx_status_error(400)

    # act & assert
    with pytest.raises(TodoistApiError) as exc_info:
        add_task_with_retry(mock_client, content="content", project_id="proj_1")

    assert "Todoist API request failed" in exc_info.value.args[0]
    assert exc_info.value.details["status_code"] == 400
    mock_client.add_task.assert_called_once()
