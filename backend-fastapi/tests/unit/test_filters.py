"""Tests for the query-string filter helpers in app.services.filters."""
from __future__ import annotations

import pytest

from app.services.filters import normalize_year, parse_int_or_none


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("5", 5),
        ("-3", -3),
        ("", None),
        ("  12  ", 12),
        (None, None),
    ],
)
def test_parse_int_or_none(raw, expected):
    assert parse_int_or_none(raw) == expected


@pytest.mark.parametrize("bad", ["abc", "1.5", "1e2"])
def test_parse_int_or_none_returns_none_for_non_integer(bad):
    """Tolerant helper: non-integers collapse to ``None`` so the
    query-string filters stay best-effort for the dashboard.
    """
    assert parse_int_or_none(bad) is None


@pytest.mark.parametrize(
    "raw,expected",
    [
        # Clean 4-digit year
        ("1968", "1968"),
        ("1982", "1982"),
        # Whitespace stripped
        ("  1977  ", "1977"),
        # Bracket typo
        ("[1982]", "1982"),
        # Annotation appended
        ("1982 (LP)", "1982"),
        # Multi-year — first wins (canonical: album's primary release)
        ("1965 (disco 1), 1968 (disco 2) y 1976 (disco 3)", "1965"),
        # s/d and empty collapse to None
        ("s/d", None),
        ("S/D", None),
        ("", None),
        (None, None),
        # No 4-digit token → None
        ("???", None),
    ],
)
def test_normalize_year(raw, expected):
    assert normalize_year(raw) == expected
