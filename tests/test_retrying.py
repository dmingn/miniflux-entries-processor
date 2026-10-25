"""Tests for shared retry helpers."""

from miniflux_entries_processor.retrying import is_retryable_status_code


def test_is_retryable_status_code_returns_True_for_retryable_codes() -> None:
    assert is_retryable_status_code(429) is True
    assert is_retryable_status_code(503) is True


def test_is_retryable_status_code_returns_False_for_other_codes() -> None:
    assert is_retryable_status_code(400) is False
    assert is_retryable_status_code(404) is False
