"""Shared helpers for theme normalization.

``canonical_tema`` is the same helper the Go runtime uses to fold
case variants ("Vida/ muerte" vs "Vida/ Muerte") into a single chip.
It lives here so both the API stats aggregation and the seed CLI can
use the exact same logic.

In addition to case/whitespace folding, ``canonical_tema`` also
applies ``TEMA_TYPO_MAP``: a curated set of *obvious* transcription
typos (e.g. ``Solidarida`` → ``Solidaridad``) so near-identical
theme labels collapse into one canonical bucket. The API's theme
filter mirrors this map (see ``public._tema_filter_variants``) so a
search for the canonical spelling still matches rows stored under
the misspelled variant.
"""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE_RE = re.compile(r"\s+")

# Curated, unambiguous transcription typos observed in the corpus.
# Keys are the misspelling (lower-cased), values the canonical word.
# Only add entries that are clearly typos — vocabulary decisions
# (whether "Solidaridad" vs "Individualismo" should be a binomio)
# belong to the editorial team, not this map.
TEMA_TYPO_MAP: dict[str, str] = {
    "solidarida": "solidaridad",
}


def _fix_typo(word: str) -> str:
    """Return ``word`` with a known typo corrected (case-insensitive)."""
    fixed = TEMA_TYPO_MAP.get(word.lower())
    return fixed if fixed is not None else word


def canonical_tema(value: str | None) -> str:
    """Title-case each whitespace-delimited word in every
    slash-delimited segment, correcting known typos.

    Examples:
      "Vida/ muerte"     -> "Vida/Muerte"
      "Ao nuevo"        -> "Ao Nuevo"
      "  caf/  T "     -> "Caf/T"
      "Solidarida/Individualismo" -> "Solidaridad/Individualismo"

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
    # produce "Ao Nuevo" instead of "Ao nuevo". Typo correction runs
    # before capitalisation so the map keys (lower-cased) match.
    return " ".join(_fix_typo(w).capitalize() for w in segment.split(" "))


__all__ = ["TEMA_TYPO_MAP", "canonical_tema", "_fix_typo"]
