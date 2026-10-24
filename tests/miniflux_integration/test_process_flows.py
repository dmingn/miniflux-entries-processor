"""Miniflux integration coverage for processor actions against a live instance."""

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

STAR_CONFIG = """
rules:
  - name: "Star all unread entries"
    source:
      name: "unread"
    condition:
      name: "match_all"
    action:
      name: "star"
"""

MARK_AS_READ_CONFIG = """
rules:
  - name: "Mark all unread entries as read"
    source:
      name: "unread"
    condition:
      name: "match_all"
    action:
      name: "mark_as_read"
"""


def _api_headers(api_key: str) -> dict[str, str]:
    return {"X-Auth-Token": api_key, "Accept": "application/json"}


def _list_feeds(base_url: str, api_key: str) -> list[dict[str, Any]]:
    response = requests.get(
        f"{base_url}/v1/feeds",
        headers=_api_headers(api_key),
        timeout=30,
    )
    response.raise_for_status()
    feeds = response.json()
    assert isinstance(feeds, list)
    return feeds


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
    status: str | None = None,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {"limit": "100"}
    if starred is not None:
        params["starred"] = str(starred).lower()
    if status is not None:
        params["status"] = status
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


def _get_entry(base_url: str, api_key: str, entry_id: int) -> dict[str, Any]:
    response = requests.get(
        f"{base_url}/v1/entries/{entry_id}",
        headers=_api_headers(api_key),
        timeout=30,
    )
    response.raise_for_status()
    entry = response.json()
    assert isinstance(entry, dict)
    return entry


def _toggle_bookmark(base_url: str, api_key: str, entry_id: int) -> None:
    response = requests.put(
        f"{base_url}/v1/entries/{entry_id}/bookmark",
        headers=_api_headers(api_key),
        timeout=30,
    )
    response.raise_for_status()


def _set_entry_status(
    base_url: str,
    api_key: str,
    entry_id: int,
    status: str,
) -> None:
    response = requests.put(
        f"{base_url}/v1/entries",
        headers=_api_headers(api_key),
        json={"entry_ids": [entry_id], "status": status},
        timeout=30,
    )
    response.raise_for_status()


def _ensure_starred(
    base_url: str, api_key: str, entry_id: int, *, starred: bool
) -> None:
    entry = _get_entry(base_url, api_key, entry_id)
    if bool(entry["starred"]) != starred:
        _toggle_bookmark(base_url, api_key, entry_id)


def _ensure_feed(env: MinifluxIntegrationEnv) -> int:
    for feed in _list_feeds(env.base_url, env.api_key):
        if feed.get("feed_url") == env.feed_url:
            feed_id = feed["id"]
            assert isinstance(feed_id, int)
            _refresh_feed(env.base_url, env.api_key, feed_id)
            return feed_id

    feed_id = _create_feed(env.base_url, env.api_key, env.feed_url)
    _refresh_feed(env.base_url, env.api_key, feed_id)
    return feed_id


def _first_entry_id(env: MinifluxIntegrationEnv) -> int:
    entries = _list_entries(env.base_url, env.api_key)
    assert len(entries) >= 1
    entry_id = entries[0]["id"]
    assert isinstance(entry_id, int)
    return entry_id


def _configure_env(
    env: MinifluxIntegrationEnv,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MINIFLUX_BASE_URL", env.base_url)
    monkeypatch.setenv("MINIFLUX_API_KEY", env.api_key)


@pytest.mark.miniflux_integration
def test_process_unstars_starred_entry_from_miniflux(
    miniflux_integration_env: MinifluxIntegrationEnv,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # arrange
    _ensure_feed(miniflux_integration_env)
    entry_id = _first_entry_id(miniflux_integration_env)
    _ensure_starred(
        miniflux_integration_env.base_url,
        miniflux_integration_env.api_key,
        entry_id,
        starred=True,
    )

    config_path = tmp_path / "config.yaml"
    config_path.write_text(UNSTAR_CONFIG, encoding="utf-8")
    _configure_env(miniflux_integration_env, monkeypatch)

    # act
    process([config_path])

    # assert
    starred_after = _list_entries(
        miniflux_integration_env.base_url,
        miniflux_integration_env.api_key,
        starred=True,
    )
    assert all(entry["id"] != entry_id for entry in starred_after)


@pytest.mark.miniflux_integration
def test_process_stars_unread_entry_from_miniflux(
    miniflux_integration_env: MinifluxIntegrationEnv,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # arrange
    _ensure_feed(miniflux_integration_env)
    entry_id = _first_entry_id(miniflux_integration_env)
    _set_entry_status(
        miniflux_integration_env.base_url,
        miniflux_integration_env.api_key,
        entry_id,
        "unread",
    )
    _ensure_starred(
        miniflux_integration_env.base_url,
        miniflux_integration_env.api_key,
        entry_id,
        starred=False,
    )

    config_path = tmp_path / "config.yaml"
    config_path.write_text(STAR_CONFIG, encoding="utf-8")
    _configure_env(miniflux_integration_env, monkeypatch)

    # act
    process([config_path])

    # assert
    starred_after = _list_entries(
        miniflux_integration_env.base_url,
        miniflux_integration_env.api_key,
        starred=True,
    )
    assert any(entry["id"] == entry_id for entry in starred_after)


@pytest.mark.miniflux_integration
def test_process_marks_unread_entry_as_read_from_miniflux(
    miniflux_integration_env: MinifluxIntegrationEnv,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # arrange
    _ensure_feed(miniflux_integration_env)
    entry_id = _first_entry_id(miniflux_integration_env)
    _set_entry_status(
        miniflux_integration_env.base_url,
        miniflux_integration_env.api_key,
        entry_id,
        "unread",
    )

    config_path = tmp_path / "config.yaml"
    config_path.write_text(MARK_AS_READ_CONFIG, encoding="utf-8")
    _configure_env(miniflux_integration_env, monkeypatch)

    # act
    process([config_path])

    # assert
    unread_after = _list_entries(
        miniflux_integration_env.base_url,
        miniflux_integration_env.api_key,
        status="unread",
    )
    assert all(entry["id"] != entry_id for entry in unread_after)
