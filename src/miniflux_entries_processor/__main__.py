"""CLI application."""

import json
from pathlib import Path
from typing import Annotated

import logzero
import typer
from logzero import logger

from miniflux_entries_processor.config_loader import Config, load_config
from miniflux_entries_processor.exceptions import (
    ConfigError,
    MinifluxEntriesProcessorError,
)
from miniflux_entries_processor.process import process

app = typer.Typer()


def show_config_schema_callback(*, value: bool) -> None:
    """Callback for the --show-config-schema option."""  # noqa: D401
    if not value:
        return

    try:
        typer.echo(json.dumps(Config.model_json_schema(), indent=2))
    except TypeError:
        logger.exception("Failed to generate JSON schema for the configuration.")
        raise typer.Exit(code=1) from None

    raise typer.Exit


@app.command()
def main(
    config_files: Annotated[
        list[Path],
        typer.Argument(exists=True, file_okay=True, dir_okay=True),
    ],
    *,
    json_log: Annotated[
        bool,
        typer.Option(help="Output logs in JSON format."),
    ] = False,
    validate_config: Annotated[
        bool,
        typer.Option(
            "--validate-config",
            help="Validate configuration files and exit.",
        ),
    ] = False,
    show_config_schema_flag: Annotated[  # noqa: ARG001
        bool,
        typer.Option(
            "--show-config-schema",
            help="Show the JSON schema for the configuration file and exit.",
            is_eager=True,
            callback=show_config_schema_callback,
        ),
    ] = False,
) -> None:
    """A CLI application to process Miniflux entries."""  # noqa: D401
    if json_log:
        logzero.json()

    if validate_config:
        try:
            load_config(config_files)
        except ConfigError:
            logger.exception("Configuration validation failed.")
            raise typer.Exit(code=1) from None

        typer.echo("Configuration is valid.")
        raise typer.Exit

    try:
        process(config_files=config_files)
    except MinifluxEntriesProcessorError:
        logger.exception("An error occurred during Miniflux entries processing.")
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    try:
        app()
    except typer.Exit:
        raise
    except Exception:  # noqa: BLE001
        logger.exception("An unexpected error occurred.")
        raise typer.Exit(code=1) from None
