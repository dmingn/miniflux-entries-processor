"""Fixtures for Miniflux Docker Compose-backed integration tests."""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import requests

if TYPE_CHECKING:
    from collections.abc import Generator

COMPOSE_FILE = Path(__file__).with_name("docker-compose.yml")
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "test1234"  # noqa: S105
COMPOSE_PROJECT = "mep-miniflux-integration"
DOCKER_BIN = shutil.which("docker")
RSS_FEED_URL = "http://rss/feed.xml"


@dataclass(frozen=True)
class MinifluxIntegrationEnv:
    """Running Miniflux instance credentials for integration tests."""

    base_url: str
    api_key: str
    feed_url: str


def _docker_env() -> dict[str, str]:
    env = os.environ.copy()
    env["ADMIN_USERNAME"] = ADMIN_USERNAME
    env["ADMIN_PASSWORD"] = ADMIN_PASSWORD
    if env.get("DOCKER_HOST"):
        return env

    if Path("/var/run/docker.sock").exists():
        return env

    bind_mounts = Path("/mnt/wsl/docker-desktop-bind-mounts")
    if bind_mounts.is_dir():
        for sock in bind_mounts.glob("*/docker.sock"):
            env["DOCKER_HOST"] = f"unix://{sock}"
            return env

    return env


def _docker_available() -> bool:
    if DOCKER_BIN is None:
        return False
    try:
        completed = subprocess.run(  # noqa: S603
            [DOCKER_BIN, "version"],
            check=False,
            capture_output=True,
            text=True,
            env=_docker_env(),
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False
    return completed.returncode == 0


def _unused_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _compose(*args: str, host_port: int) -> subprocess.CompletedProcess[str]:
    if DOCKER_BIN is None:
        msg = "docker executable not found"
        raise RuntimeError(msg)
    env = _docker_env()
    env["MINIFLUX_HOST_PORT"] = str(host_port)
    return subprocess.run(  # noqa: S603
        [
            DOCKER_BIN,
            "compose",
            "-p",
            COMPOSE_PROJECT,
            "-f",
            str(COMPOSE_FILE),
            *args,
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
    )


def _wait_for_miniflux(base_url: str, *, timeout_seconds: float = 120) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            response = requests.get(
                f"{base_url}/v1/me",
                auth=(ADMIN_USERNAME, ADMIN_PASSWORD),
                timeout=5,
            )
            if response.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    msg = f"Miniflux did not become ready at {base_url}"
    raise RuntimeError(msg)


def _create_api_key(base_url: str) -> str:
    response = requests.post(
        f"{base_url}/v1/api-keys",
        auth=(ADMIN_USERNAME, ADMIN_PASSWORD),
        json={"description": "miniflux-integration"},
        timeout=30,
    )
    response.raise_for_status()
    token = response.json()["token"]
    if not isinstance(token, str) or not token:
        msg = "Miniflux API key response did not include a token"
        raise RuntimeError(msg)
    return token


@pytest.fixture(scope="session")
def miniflux_integration_env() -> Generator[MinifluxIntegrationEnv]:
    if not _docker_available():
        pytest.fail(
            "Docker is required for miniflux_integration tests "
            "(run via `make miniflux-integration`)."
        )

    host_port = _unused_port()
    base_url = f"http://127.0.0.1:{host_port}"

    up = _compose("up", "-d", "--wait", "--pull", "missing", host_port=host_port)
    if up.returncode != 0:
        _compose("down", "-v", "--remove-orphans", host_port=host_port)
        pytest.fail(
            f"docker compose up failed:\nstdout:\n{up.stdout}\nstderr:\n{up.stderr}"
        )

    try:
        _wait_for_miniflux(base_url)
        api_key = _create_api_key(base_url)
        yield MinifluxIntegrationEnv(
            base_url=base_url,
            api_key=api_key,
            feed_url=RSS_FEED_URL,
        )
    finally:
        down = _compose("down", "-v", "--remove-orphans", host_port=host_port)
        if down.returncode != 0:
            # Prefer surfacing the original failure; cleanup errors go to stderr.
            print(  # noqa: T201
                "docker compose down failed:\n"
                f"stdout:\n{down.stdout}\n"
                f"stderr:\n{down.stderr}"
            )
