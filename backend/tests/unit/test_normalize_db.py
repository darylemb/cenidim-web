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


def test_fix_lyrics_match_clears_wrong_lyrics(tmp_path, ndb):
    import sqlite3

    # Two songs: "Los perritos" (no matching file) and "La casa" (has
    # a matching file). A lyrics dir with only CASA.txt must leave La
    # casa's lyric intact and clear Los perritos' wrong one.
    (tmp_path / "CASA.txt").write_text(
        "LA CASA\n\nLa casa es grande\ny tiene ventanas.\n", encoding="utf-8"
    )

    con = sqlite3.connect(":memory:")
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE songs (id INTEGER PRIMARY KEY, title TEXT, "
        "lyrics TEXT, filename TEXT, tema TEXT)"
    )
    cur.executemany(
        "INSERT INTO songs (id, title, lyrics, filename) VALUES (?, ?, ?, ?)",
        [
            (1, "Los perritos", "¡Oinc oinc! (letra equivocada)", "LOS PUERQUITOS.txt"),
            (2, "La casa", "letra vieja", "CASA.txt"),
        ],
    )
    con.commit()

    ndb.fix_lyrics_match(con, str(tmp_path))

    rows = {r[0]: (r[2], r[3]) for r in cur.execute("SELECT id, title, lyrics, filename FROM songs")}
    # Los perritos: wrong lyric cleared, filename cleared.
    assert rows[1][0] == ""
    assert rows[1][1] == ""
    # La casa: lyric re-read from the file, header stripped, filename kept.
    assert "La casa es grande" in rows[2][0]
    assert rows[2][1] == "CASA.txt"
    con.close()
