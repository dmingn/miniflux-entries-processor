"""Settings loaded from environment variables and optional .env, per secret type."""

from pydantic import Field, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_common_config = SettingsConfigDict(
    env_prefix="",
    env_file=".env",
    env_file_encoding="utf-8",
    env_ignore_empty=True,
    extra="ignore",
    frozen=True,
)


class MinifluxSettings(BaseSettings):
    """Miniflux-related settings (base URL and API key)."""

    model_config = _common_config

    base_url: HttpUrl = Field(
        description="Base URL of the Miniflux instance.",
        validation_alias="MINIFLUX_BASE_URL",
    )
    api_key: SecretStr = Field(
        description="Miniflux API key.",
        validation_alias="MINIFLUX_API_KEY",
    )


class TodoistSettings(BaseSettings):
    """Todoist-related settings (e.g. API token)."""

    model_config = _common_config

    todoist_api_token: SecretStr | None = Field(
        default=None,
        description="Todoist API token.",
        validation_alias="TODOIST_API_TOKEN",
    )
