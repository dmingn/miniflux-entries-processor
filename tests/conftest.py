"""Shared pytest fixtures."""

import pytest
from tenacity import wait_fixed


@pytest.fixture(autouse=True)
def patch_todoist_retry_no_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch Todoist retry to wait=0 via tenacity ``retry_with`` so tests do not sleep."""
    from miniflux_entries_processor.todoist_client import (  # noqa: PLC0415
        _add_task_with_retry_impl,
    )

    no_wait_impl = _add_task_with_retry_impl.retry_with(
        wait=wait_fixed(0),
    )
    monkeypatch.setattr(
        "miniflux_entries_processor.todoist_client._add_task_with_retry_impl",
        no_wait_impl,
    )


@pytest.fixture(autouse=True)
def patch_miniflux_retry_no_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch Miniflux client request retry to wait=0 so tests do not sleep."""
    from miniflux_entries_processor.miniflux_client import (  # noqa: PLC0415
        MinifluxClient,
    )

    no_wait_request = MinifluxClient._request.retry_with(  # noqa: SLF001
        wait=wait_fixed(0),
    )
    monkeypatch.setattr(MinifluxClient, "_request", no_wait_request)
