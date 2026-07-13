"""Shared helpers for theme normalization.

``canonical_tema`` is the same helper the Go runtime uses to fold
case variants ("Vida/ muerte" vs "Vida/ Muerte") into a single chip.
It lives here so both the API stats aggregation and the seed CLI can
use the exact same logic.
"""
from __future__ import annotations

import re
import unicodedata

_WHITESPACE_RE = re.compile(r"\s+")


def canonical_tema(value: str | None) -> str:
    """Title-case each whitespace-delimited word in every
    slash-delimited segment.

    Examples:
      "Vida/ muerte"     -> "Vida/Muerte"
      "Ao nuevo"        -> "Ao Nuevo"
      "  caf/  T "     -> "Caf/T"

    Empty / None inputs return an empty string so the calling site
    can treat the result as a plain bucket key.
    """
    if not value:
        return ""
    value = unicodedata.normalize("NFC", value).strip()
    parts = [_title_segment(p) for p in value.split("/")]
    return "/".join(p for p in parts if p)


def _title_segment(segment: str) -> str:
    segment = _WHITESPACE_RE.sub(" ", segment).strip()
    if not segment:
        return ""
    # Per-word title-casing so multi-word segments ("Ao nuevo")
    # produce "Ao Nuevo" instead of "Ao nuevo".
    return " ".join(w.capitalize() for w in segment.split(" "))


__all__ = ["canonical_tema"]
