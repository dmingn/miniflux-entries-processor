"""Tests for the __main__ module."""

import json
from pathlib import Path

from pydantic_yaml import to_yaml_str
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from miniflux_entries_processor.__main__ import app
from miniflux_entries_processor.actions import LogAction
from miniflux_entries_processor.conditions import MatchAllCondition
from miniflux_entries_processor.config_loader import Config, Rule
from miniflux_entries_processor.sources import StarredSource

runner = CliRunner()


def test_main_runs_process_with_given_config(
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    # arrange
    mock_process = mocker.patch("miniflux_entries_processor.__main__.process")

    config_file = tmp_path / "config.yml"
    config_file.touch()

    # act
    result = runner.invoke(app, [str(config_file)])

    # assert
    assert result.exit_code == 0, result.output
    mock_process.assert_called_once_with(config_files=[config_file])


def test_main_shows_config_schema_when_option_given() -> None:
    # act
    result = runner.invoke(app, ["--show-config-schema"])

    # assert
    assert result.exit_code == 0
    assert json.loads(result.stdout) == Config.model_json_schema()


def test_main_validates_config_and_exits_without_processing(
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    # arrange
    mock_process = mocker.patch("miniflux_entries_processor.__main__.process")
    config_file = tmp_path / "config.yml"
    config = Config(
        rules=frozenset(
            [
                Rule(
                    name="Test Rule",
                    source=StarredSource(),
                    condition=MatchAllCondition(),
                    action=LogAction(),
                ),
            ]
        )
    )
    config_file.write_text(to_yaml_str(config), encoding="utf-8")

    # act
    result = runner.invoke(
        app,
        [
            "--validate-config",
            str(config_file),
        ],
    )

    # assert
    assert result.exit_code == 0, result.output
    assert "Configuration is valid." in result.output
    mock_process.assert_not_called()


def test_main_exits_with_error_for_invalid_config_when_validating(
    mocker: MockerFixture,
    tmp_path: Path,
) -> None:
    # arrange
    mock_process = mocker.patch("miniflux_entries_processor.__main__.process")
    config_file = tmp_path / "config.yml"
    # write invalid YAML that will fail validation
    config_file.write_text("not: valid: yaml:", encoding="utf-8")

    # act
    result = runner.invoke(
        app,
        [
            "--validate-config",
            str(config_file),
        ],
    )

    # assert
    assert result.exit_code == 1
    mock_process.assert_not_called()
