"""Tests for the query-string filter helpers in app.services.filters."""
from __future__ import annotations

import pytest

from app.services.filters import parse_int_or_none


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
