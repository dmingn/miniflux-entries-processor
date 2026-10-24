"""Entry sources for fetching Miniflux entries."""

from miniflux_entries_processor.sources.starred_source import StarredSource
from miniflux_entries_processor.sources.unread_source import UnreadSource

__all__ = ["Source", "StarredSource", "UnreadSource"]

Source = StarredSource | UnreadSource
