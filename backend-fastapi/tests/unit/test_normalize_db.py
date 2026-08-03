"""Unit tests for scripts/normalize_db.py's lyric cleaning.

The script lives outside the ``app`` package but only uses the
stdlib (plus a bare importlib load of theme_normalization), so it is
safe to import from the test venv.
"""
from __future__ import annotations

import importlib.util
import os

import pytest

_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
_SCRIPT = os.path.join(_ROOT, "scripts", "normalize_db.py")


@pytest.fixture(scope="module")
def ndb():
    spec = importlib.util.spec_from_file_location("normalize_db", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_cleans_metadata_marker_lines(ndb):
    lyrics = "Dura: 2:11\nTema: Sabiduría/ ignorancia, orden/ caos.\nPersonajes: lápices.\n\nLa letra real aquí\nAutor: M.G.A."
    out = ndb.clean_lyrics_body(lyrics, "Mi canción")
    assert "Dura:" not in out
    assert "Tema:" not in out
    assert "Personajes:" not in out
    assert "Autor:" not in out
    assert "La letra real aquí" in out


def test_drops_exact_title_header(ndb):
    lyrics = "La marcha de las letras\n\nLos lápices azules,\nlos lápices morados."
    out = ndb.clean_lyrics_body(lyrics, "La marcha de las letras")
    assert not out.startswith("La marcha de las letras")
    assert out.startswith("Los lápices azules")


def test_drops_uppercase_alternate_header_followed_by_blank(ndb):
    lyrics = "MARCHA DE LOS LAPICES\n\nLos lápices azules,\nlos lápices morados."
    out = ndb.clean_lyrics_body(lyrics, "La marcha de las letras")
    assert not out.startswith("MARCHA DE LOS LAPICES")
    assert out.startswith("Los lápices azules")


def test_preserves_first_line_that_is_real_content(ndb):
    # "Caracol, caracol, tu sí que de curioso" starts with the title
    # word but is lyric content; it must survive.
    lyrics = "Caracol, caracol, tu sí que de curioso\ncon cuatro cuernecitos\ny en cada cuerno un ojo."
    out = ndb.clean_lyrics_body(lyrics, "Caracol")
    assert out.startswith("Caracol, caracol, tu sí que de curioso")


def test_is_idempotent(ndb):
    lyrics = (
        "La marcha de las letras\n\nMARCHA DE LOS LAPICES\n\nLos lápices azules,\n"
        "los lápices morados.\n\nDura: 2:11\nTema: Sabiduría/ ignorancia.\nM.G.A."
    )
    once = ndb.clean_lyrics_body(lyrics, "La marcha de las letras")
    twice = ndb.clean_lyrics_body(once, "La marcha de las letras")
    assert twice == once


def test_handles_empty_and_whitespace(ndb):
    assert ndb.clean_lyrics_body("", "Título") == ""
    assert ndb.clean_lyrics_body("   \n  \n", "Título") == "   \n  \n"
    assert ndb.clean_lyrics_body(None, "Título") is None
