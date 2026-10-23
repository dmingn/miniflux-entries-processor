"""Settings loaded from environment variables and optional .env, per secret type."""

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_common_config = SettingsConfigDict(
    env_prefix="",
    env_file=".env",
    env_file_encoding="utf-8",
    env_ignore_empty=True,
    extra="ignore",
    frozen=True,
)


class FeedlySettings(BaseSettings):
    """Feedly-related settings (e.g. token directory)."""

    model_config = _common_config

    token_dir: Path = Field(
        default_factory=lambda: Path.home() / ".config" / "feedly",
        description="Directory where Feedly API token files are stored.",
        validation_alias="FEEDLY_TOKEN_DIR",
    )


class TodoistSettings(BaseSettings):
    """Todoist-related settings (e.g. API token)."""

    model_config = _common_config

    todoist_api_token: SecretStr | None = Field(
        default=None,
        description="Todoist API token.",
        validation_alias="TODOIST_API_TOKEN",
    )
