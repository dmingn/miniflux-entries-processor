"""Todoist API client with retry and error handling helpers."""

from typing import Any, Literal

import httpx
from tenacity import retry, retry_if_exception
from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task

from miniflux_entries_processor.exceptions import TodoistApiError
from miniflux_entries_processor.retrying import (
    RETRY_STOP,
    RETRY_WAIT,
    is_retryable_status_code,
)


def _response_error_body(response: httpx.Response) -> Any:  # noqa: ANN401
    """Parse JSON body or fall back to raw text."""
    try:
        return response.json()
    except ValueError:
        return response.text


def build_error_details(
    response: httpx.Response | None,
    project_id: str,
) -> dict[str, Any]:
    """Build a details dict from an httpx error response (or None)."""
    if response is None:
        return {
            "status_code": "unknown",
            "error_body": "<no response>",
            "project_id": project_id,
        }
    return {
        "status_code": response.status_code,
        "error_body": _response_error_body(response),
        "project_id": project_id,
    }


def _should_retry(exc: BaseException) -> bool:
    """Return True if the exception is worth retrying (transient/rate limit)."""
    if isinstance(exc, httpx.HTTPStatusError):
        return is_retryable_status_code(exc.response.status_code)
    return isinstance(exc, httpx.RequestError)


def add_task_with_retry(  # noqa: PLR0913
    client: TodoistAPI,
    *,
    content: str,
    project_id: str,
    priority: Literal[1, 2, 3, 4] | None = None,
    due_string: str | None = None,
    description: str | None = None,
    labels: frozenset[str] | None = None,
) -> Task:
    """Call Todoist add_task with retry on transient and rate-limit errors.

    Raises TodoistApiError on httpx.HTTPError (e.g. HTTPStatusError, ConnectError).
    """
    try:
        return _add_task_with_retry_impl(
            client,
            content=content,
            project_id=project_id,
            priority=priority,
            due_string=due_string,
            description=description,
            labels=labels,
        )
    except httpx.HTTPError as exc:
        response = exc.response if isinstance(exc, httpx.HTTPStatusError) else None
        details = build_error_details(response, project_id)
        message = f"Todoist API request failed with status {details['status_code']}"
        raise TodoistApiError(message, details=details) from exc


@retry(
    reraise=True,
    stop=RETRY_STOP,
    wait=RETRY_WAIT,
    retry=retry_if_exception(_should_retry),
)
def _add_task_with_retry_impl(  # noqa: PLR0913
    client: TodoistAPI,
    *,
    content: str,
    project_id: str,
    priority: Literal[1, 2, 3, 4] | None = None,
    due_string: str | None = None,
    description: str | None = None,
    labels: frozenset[str] | None = None,
) -> Task:
    """Call Todoist add_task with retry on transient errors (internal)."""
    return client.add_task(
        content=content,
        project_id=project_id,
        priority=priority,
        due_string=due_string,
        description=description,
        labels=list(labels) if labels else None,
    )
