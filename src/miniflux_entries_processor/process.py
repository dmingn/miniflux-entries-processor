"""Module for processing Miniflux entries."""

from __future__ import annotations

from typing import TYPE_CHECKING

from logzero import logger

from miniflux_entries_processor.config_loader import Rule, load_config
from miniflux_entries_processor.exceptions import (
    ActionSkippedDueToPersistentError,
    ProcessingFailuresError,
)
from miniflux_entries_processor.miniflux_client import Entry, create_miniflux_client

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from miniflux_entries_processor.sources import Source


def process_entry(entry: Entry, rule: Rule) -> bool:
    """Process a single Miniflux entry based on a rule.

    Returns
    -------
    bool
        True if processing completed without error (including when the
        condition does not match). False if evaluation or the action failed.
    """
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
                return False
            except Exception:  # noqa: BLE001
                logger.exception(
                    f"Error processing entry '{entry.title}' (URL: {entry.url}) with rule '{rule.name}'."
                )
                return False
    except Exception:  # noqa: BLE001
        logger.exception(
            f"Error evaluating rule '{rule.name}' for entry '{entry.title}' (URL: {entry.url})."
        )
        return False

    return True


def process_entries(entries: Iterable[Entry], rules: Iterable[Rule]) -> tuple[int, int]:
    """Process Miniflux entries based on configured rules.

    Returns
    -------
    tuple[int, int]
        Counts of ``(successes, failures)`` across entry/rule pairs.
    """
    successes = 0
    failures = 0
    for entry in entries:
        for rule in rules:
            if process_entry(entry, rule):
                successes += 1
            else:
                failures += 1
    return successes, failures


def process(config_files: list[Path]) -> None:
    """Process entries.

    Raises
    ------
    ProcessingFailuresError
        If any entry/rule processing attempt failed.
    """
    config = load_config(config_files)
    logger.info(f"Loaded {len(config.rules)} rules from {len(config_files)} sources")

    client = create_miniflux_client()

    rules_by_source: dict[Source, list[Rule]] = {}
    for rule in config.rules:
        rules_by_source.setdefault(rule.source, []).append(rule)

    successes = 0
    failures = 0
    for source, rules in rules_by_source.items():
        source_successes, source_failures = process_entries(
            entries=source.fetch_entries(client),
            rules=rules,
        )
        successes += source_successes
        failures += source_failures

    logger.info(f"Finished processing: {successes} succeeded, {failures} failed.")
    if failures:
        msg = f"Processing completed with {failures} failure(s)."
        raise ProcessingFailuresError(msg)
