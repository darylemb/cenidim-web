"""Filter parsing shared between /api/stats and /api/search."""
from __future__ import annotations

from typing import Annotated

from fastapi import Query


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
    "parse_int_or_none",
]
