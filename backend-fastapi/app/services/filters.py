"""Filter parsing shared between /api/stats and /api/search."""
from __future__ import annotations

import re
from typing import Annotated

from fastapi import Query


def normalize_year(raw: str | None) -> str | None:
    """Return a clean 4-digit year string, or ``None`` if undated.

    The ``anio`` column is stored as TEXT in the legacy Go schema.
    Real rows look like ``1968`` but the CSV also produced dirty
    values that the dashboard / CancionesView would otherwise
    surface as empty cells:

        ``[1982]``        — bracket typo
        ``1982 (LP)``     — annotation appended
        ``1965 (disco 1), 1968 (disco 2) y 1976 (disco 3)`` — multi-year
        ``s/d``           — "sin dato"
        ``""`` / NULL     — missing

    The function strips brackets/annotations, returns the FIRST
    4-digit token, and maps ``s/d`` / empty / NULL to ``None``.

    >>> normalize_year("1968")
    '1968'
    >>> normalize_year("[1982]")
    '1982'
    >>> normalize_year("1965 (disco 1), 1968 (disco 2) y 1976 (disco 3)")
    '1965'
    >>> normalize_year("s/d")
    >>> normalize_year("")
    """
    if raw is None:
        return None
    s = raw.strip()
    if not s or s.lower() == "s/d":
        return None
    m = re.search(r"(\d{4})", s)
    return m.group(1) if m else None


def parse_int_or_none(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        return None


TemaList = Annotated[str | None, Query(
    description="Comma-separated theme list; use __none__ for unclassified",
)]
YearFromQ = Annotated[int | None, Query(ge=1900, le=2100)]
YearToQ = Annotated[int | None, Query(ge=1900, le=2100)]
AlbumQ = Annotated[str | None, Query(max_length=200)]
ClasificacionList = Annotated[str | None, Query(
    description="Comma-separated clasificacion list",
)]
QueryText = Annotated[str | None, Query(max_length=200)]


__all__ = [
    "AlbumQ",
    "ClasificacionList",
    "QueryText",
    "TemaList",
    "YearFromQ",
    "YearToQ",
    "normalize_year",
    "parse_int_or_none",
]
