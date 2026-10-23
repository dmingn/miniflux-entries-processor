"""Stream sources for fetching Feedly entries."""

from miniflux_entries_processor.sources.all_source import AllSource
from miniflux_entries_processor.sources.saved_source import SavedSource

__all__ = ["AllSource", "SavedSource", "StreamSource"]

StreamSource = SavedSource | AllSource
