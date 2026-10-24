"""Custom exceptions for the application."""

from typing import Any


class MinifluxEntriesProcessorError(Exception):
    """Base exception for the application."""


class ConfigError(MinifluxEntriesProcessorError):
    """Raised when there is an error loading the configuration."""


class MinifluxClientInitError(MinifluxEntriesProcessorError):
    """Raised when there is an error initializing the Miniflux client."""


class FetchEntriesError(MinifluxEntriesProcessorError):
    """Raised when there is an error fetching entries from Miniflux."""


class ActionSkippedDueToPersistentError(MinifluxEntriesProcessorError):
    """Raised when an action is skipped because it previously encountered a persistent error."""


class TodoistApiError(MinifluxEntriesProcessorError):
    """Raised when there is an error communicating with the Todoist API.

    Attributes
    ----------
    details
        Optional dict with structured error info (e.g. status_code, error_body,
        project_id). Useful for structured logging.
    """

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.details = details if details is not None else {}
