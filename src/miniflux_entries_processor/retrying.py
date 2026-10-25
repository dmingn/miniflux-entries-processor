"""Shared HTTP retry helpers for Miniflux and Todoist clients."""

from typing import Final

from tenacity import stop_after_attempt, wait_exponential
from tenacity.stop import stop_base
from tenacity.wait import wait_base

RETRYABLE_STATUS_CODES: Final[frozenset[int]] = frozenset({429, 500, 502, 503, 504})

RETRY_STOP: Final[stop_base] = stop_after_attempt(3)
RETRY_WAIT: Final[wait_base] = wait_exponential(multiplier=1, min=1, max=10)


def is_retryable_status_code(status_code: int) -> bool:
    """Return True if the HTTP status code should be retried."""
    return status_code in RETRYABLE_STATUS_CODES
