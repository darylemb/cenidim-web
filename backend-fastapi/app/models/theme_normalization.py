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
    """Title-case each slash-delimited segment, collapse whitespace.

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
    chars = list(segment)
    chars[0] = chars[0].upper()
    for i in range(1, len(chars)):
        chars[i] = chars[i].lower()
    return "".join(chars)


__all__ = ["canonical_tema"]
