"""Miniflux integration coverage for starring and unstarring via the processor."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
import requests

from miniflux_entries_processor.process import process

if TYPE_CHECKING:
    from pathlib import Path

    from tests.miniflux_integration.conftest import MinifluxIntegrationEnv

UNSTAR_CONFIG = """
rules:
  - name: "Unstar all starred entries"
    source:
      name: "starred"
    condition:
      name: "match_all"
    action:
      name: "unstar"
"""


def _api_headers(api_key: str) -> dict[str, str]:
    return {"X-Auth-Token": api_key, "Accept": "application/json"}


def _create_feed(base_url: str, api_key: str, feed_url: str) -> int:
    response = requests.post(
        f"{base_url}/v1/feeds",
        headers=_api_headers(api_key),
        json={"feed_url": feed_url},
        timeout=60,
    )
    response.raise_for_status()
    feed_id = response.json()["feed_id"]
    assert isinstance(feed_id, int)
    return feed_id


def _refresh_feed(base_url: str, api_key: str, feed_id: int) -> None:
    response = requests.put(
        f"{base_url}/v1/feeds/{feed_id}/refresh",
        headers=_api_headers(api_key),
        timeout=60,
    )
    response.raise_for_status()


def _list_entries(
    base_url: str,
    api_key: str,
    *,
    starred: bool | None = None,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {"limit": "100"}
    if starred is not None:
        params["starred"] = str(starred).lower()
    response = requests.get(
        f"{base_url}/v1/entries",
        headers=_api_headers(api_key),
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    entries = response.json()["entries"]
    assert isinstance(entries, list)
    return entries


def _toggle_bookmark(base_url: str, api_key: str, entry_id: int) -> None:
    response = requests.put(
        f"{base_url}/v1/entries/{entry_id}/bookmark",
        headers=_api_headers(api_key),
        timeout=30,
    )
    response.raise_for_status()


@pytest.mark.miniflux_integration
def test_process_unstars_starred_entry_from_miniflux(
    miniflux_integration_env: MinifluxIntegrationEnv,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # arrange
    feed_id = _create_feed(
        miniflux_integration_env.base_url,
        miniflux_integration_env.api_key,
        miniflux_integration_env.feed_url,
    )
    _refresh_feed(
        miniflux_integration_env.base_url,
        miniflux_integration_env.api_key,
        feed_id,
    )

    entries = _list_entries(
        miniflux_integration_env.base_url,
        miniflux_integration_env.api_key,
    )
    assert len(entries) >= 1
    entry_id = entries[0]["id"]
    assert isinstance(entry_id, int)

    _toggle_bookmark(
        miniflux_integration_env.base_url,
        miniflux_integration_env.api_key,
        entry_id,
    )
    starred_before = _list_entries(
        miniflux_integration_env.base_url,
        miniflux_integration_env.api_key,
        starred=True,
    )
    assert any(entry["id"] == entry_id for entry in starred_before)

    config_path = tmp_path / "config.yaml"
    config_path.write_text(UNSTAR_CONFIG, encoding="utf-8")

    monkeypatch.setenv("MINIFLUX_BASE_URL", miniflux_integration_env.base_url)
    monkeypatch.setenv("MINIFLUX_API_KEY", miniflux_integration_env.api_key)

    # act
    process([config_path])

    # assert
    starred_after = _list_entries(
        miniflux_integration_env.base_url,
        miniflux_integration_env.api_key,
        starred=True,
    )
    assert all(entry["id"] != entry_id for entry in starred_after)
