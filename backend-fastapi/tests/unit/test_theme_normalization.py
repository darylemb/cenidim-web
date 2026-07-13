"""Theme normalization helper unit tests."""
from app.models.theme_normalization import canonical_tema


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
