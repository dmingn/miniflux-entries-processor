"""Custom exceptions for the application."""

from typing import Any


class FeedlyEntriesProcessorError(Exception):
    """Base exception for the application."""


class ConfigError(FeedlyEntriesProcessorError):
    """Raised when there is an error loading the configuration."""


class FeedlyClientInitError(FeedlyEntriesProcessorError):
    """Raised when there is an error initializing the Feedly client."""


class FetchEntriesError(FeedlyEntriesProcessorError):
    """Raised when there is an error fetching entries from Feedly."""


class ActionSkippedDueToPersistentError(FeedlyEntriesProcessorError):
    """Raised when an action is skipped because it previously encountered a persistent error."""


class TodoistApiError(FeedlyEntriesProcessorError):
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
