"""Module for processing Miniflux entries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from logzero import logger

from miniflux_entries_processor.config_loader import Rule, load_config
from miniflux_entries_processor.exceptions import ActionSkippedDueToPersistentError
from miniflux_entries_processor.miniflux_client import Entry, create_miniflux_client

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from miniflux_entries_processor.sources import Source


def process_entry(entry: Entry, rule: Rule) -> None:
    """Process a single Miniflux entry based on a rule."""
    try:
        if rule.condition.matches(entry):
            logger.info(
                f"Entry '{entry.title}' (URL: {entry.url}) matched rule '{rule.name}'."
            )
            try:
                rule.action.process(entry)
            except ActionSkippedDueToPersistentError as e:
                logger.error(
                    f"Rule '{rule.name}' skipped for entry '{entry.title}': {e}"
                )
            except Exception:  # noqa: BLE001
                logger.exception(
                    f"Error processing entry '{entry.title}' (URL: {entry.url}) with rule '{rule.name}'."
                )
    except Exception:  # noqa: BLE001
        logger.exception(
            f"Error evaluating rule '{rule.name}' for entry '{entry.title}' (URL: {entry.url})."
        )


def process_entries(entries: Iterable[Entry], rules: Iterable[Rule]) -> None:
    """Process Miniflux entries based on configured rules."""
    for entry in entries:
        for rule in rules:
            process_entry(entry, rule)


def process(config_files: list[Path]) -> None:
    """Process entries."""
    config = load_config(config_files)
    logger.info(f"Loaded {len(config.rules)} rules from {len(config_files)} sources")

    client = create_miniflux_client()

    rules_by_source: dict[Source, set[Rule]] = {}
    for rule in config.rules:
        rules_by_source.setdefault(rule.source, set()).add(rule)

    for source, rules in rules_by_source.items():
        process_entries(entries=source.fetch_entries(client), rules=rules)
