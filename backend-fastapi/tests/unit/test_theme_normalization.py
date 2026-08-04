"""Theme normalization helper unit tests."""
from app.models.theme_normalization import TEMA_TYPO_MAP, _fix_typo, canonical_tema


def test_canonical_tema_singles():
    assert canonical_tema("familia") == "Familia"
    assert canonical_tema("FAMILIA") == "Familia"
    assert canonical_tema("") == ""
    assert canonical_tema(None) == ""


def test_canonical_tema_binomials_fold_case():
    assert canonical_tema("Vida/ muerte") == "Vida/Muerte"
    assert canonical_tema("vida/ MUERTE") == "Vida/Muerte"
    assert canonical_tema("Equilibrio / Desequilibrio") == "Equilibrio/Desequilibrio"


def test_canonical_tema_collapses_whitespace():
    assert canonical_tema("  vida /   muerte  ") == "Vida/Muerte"
    assert canonical_tema("equilibrio/\tdesequilibrio") == "Equilibrio/Desequilibrio"


def test_canonical_tema_drops_empty_segments():
    assert canonical_tema("/Amor/") == "Amor"
    assert canonical_tema("Amor/") == "Amor"


def test_canonical_tema_preserves_unicode():
    assert canonical_tema("Año nuevo") == "Año Nuevo"


def test_canonical_tema_fixes_known_typos():
    # Both the misspelled and the canonical form collapse to the same
    # canonical bucket (reviewer feedback 01/jul/2026 #11).
    assert canonical_tema("Solidarida/Individualismo") == "Solidaridad/Individualismo"
    assert canonical_tema("solidarida/individualismo") == "Solidaridad/Individualismo"
    assert canonical_tema("Solidaridad/Individualismo") == "Solidaridad/Individualismo"


def test_typo_map_contains_only_lowercase_typos():
    # Keys are the misspelling (lower-cased), values the canonical word.
    for typo, fixed in TEMA_TYPO_MAP.items():
        assert typo == typo.lower()
        assert typo != fixed


def test_fix_typo_identity_for_unknown_words():
    assert _fix_typo("Amor") == "Amor"
    assert _fix_typo("") == ""
    assert _fix_typo("Solidaridad") == "Solidaridad"
