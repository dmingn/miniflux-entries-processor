"""Tests for the Entry model."""

import pytest

from miniflux_entries_processor.feedly_client import Alternate, Entry


@pytest.mark.parametrize(
    ("entry", "expected_effective_url"),
    [
        pytest.param(
            Entry(
                id="e1",
                canonical_url="http://example.com/canonical",
                alternate=None,
            ),
            "http://example.com/canonical",
            id="canonical_url",
        ),
        pytest.param(
            Entry(
                id="e2",
                canonical_url=None,
                alternate=(
                    Alternate(href="http://example.com/alt-page", type="text/html"),
                ),
            ),
            "http://example.com/alt-page",
            id="alternate_only",
        ),
        pytest.param(
            Entry(
                id="e3",
                canonical_url=None,
                alternate=(
                    Alternate(href="http://example.com/first", type="text/html"),
                    Alternate(
                        href="http://example.com/second",
                        type="application/pdf",
                    ),
                ),
            ),
            "http://example.com/first",
            id="alternate_multiple",
        ),
        pytest.param(
            Entry(id="e4", canonical_url=None, alternate=None),
            None,
            id="neither",
        ),
    ],
)
def test_Entry_effective_url_returns_expected(
    entry: Entry,
    expected_effective_url: str | None,
) -> None:
    assert entry.effective_url == expected_effective_url
