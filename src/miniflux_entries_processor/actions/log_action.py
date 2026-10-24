"""Log action."""

from typing import Literal, assert_never

from logzero import logger

from miniflux_entries_processor.actions.base_action import BaseAction
from miniflux_entries_processor.miniflux_client import Entry


class LogAction(BaseAction):
    """An action that logs the Miniflux entry."""

    name: Literal["log"] = "log"
    level: Literal["info", "debug", "warning", "error"] = "info"

    def _process(self, entry: Entry) -> None:
        """Process a Miniflux entry by logging its details."""
        log_message = f"Processing entry: {entry.title} (URL: {entry.url})"
        match self.level:
            case "info":
                logger.info(log_message)
            case "debug":
                logger.debug(log_message)
            case "warning":
                logger.warning(log_message)
            case "error":
                logger.error(log_message)
            case _ as unexpected_level:
                assert_never(unexpected_level)
