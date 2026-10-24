"""Configuration loading and validation for Miniflux Entries Processor."""

from collections.abc import Iterable
from pathlib import Path

from pydantic import (
    BaseModel,
    ConfigDict,
    DirectoryPath,
    Field,
    FilePath,
    TypeAdapter,
    ValidationError,
)
from pydantic_yaml import parse_yaml_raw_as
from ruamel.yaml.error import YAMLError

from miniflux_entries_processor.actions import Action
from miniflux_entries_processor.conditions import Condition
from miniflux_entries_processor.exceptions import ConfigError
from miniflux_entries_processor.sources import Source


class Rule(BaseModel):
    """Defines a single processing rule for Miniflux entries."""

    name: str
    source: Source = Field(discriminator="name")
    condition: Condition = Field(discriminator="name")
    action: Action = Field(discriminator="name")
    model_config = ConfigDict(frozen=True)


class Config(BaseModel):
    """Overall configuration for the Miniflux Entries Processor."""

    rules: frozenset[Rule]
    model_config = ConfigDict(frozen=True)

    def __or__(self, other: "Config") -> "Config":
        """Combine two Config objects, merging their rules.

        Args:
            other: Another Config object to combine with.

        Returns
        -------
            A new Config object containing all unique rules from both original Config objects.
        """
        if not isinstance(other, Config):
            return NotImplemented

        return Config(rules=self.rules | other.rules)


def load_config_file(file_path: Path) -> Config:
    """Load and validate the configuration from a YAML file.

    Args:
        file_path: The path to the YAML configuration file.

    Returns
    -------
        A Config object representing the loaded configuration.

    Raises
    ------
        ConfigError: If there is an error in loading or validating the
                     configuration, such as file not found, malformed YAML,
                     or validation failures.
    """
    try:
        validated_path = TypeAdapter(FilePath).validate_python(file_path)
        yaml_content = validated_path.read_text(encoding="utf-8")
        return parse_yaml_raw_as(Config, yaml_content)
    except (YAMLError, ValidationError) as e:
        msg = f"Failed to load configuration from '{file_path}'."
        raise ConfigError(msg) from e


def load_config(paths: Iterable[Path]) -> Config:
    """Load and merge configuration from multiple YAML files in given paths.

    Args:
        paths: An iterable of file or directory paths containing YAML configuration files.

    Returns
    -------
        A Config object representing the merged configuration from all valid files.

    Raises
    ------
        ConfigError: If there is an error in loading or validating any of the
                     configuration files.
    """
    config = Config(rules=frozenset())

    validated_path: TypeAdapter[FilePath | DirectoryPath] = TypeAdapter(
        FilePath | DirectoryPath
    )
    try:
        for path in paths:
            validated_path.validate_python(path)
            if path.is_file():
                config |= load_config_file(path)
            elif path.is_dir():
                for file_path in path.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in {
                        ".yml",
                        ".yaml",
                    }:
                        config |= load_config_file(file_path)
    except ValidationError as e:
        msg = f"Invalid path found in configuration paths: '{path}'."
        raise ConfigError(msg) from e

    return config
