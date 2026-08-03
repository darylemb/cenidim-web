"""Unit tests for scripts/build_db.py (the Python port of the Go db-builder).

Mirrors backend/cmd/build-db/main_test.go.
"""
from __future__ import annotations

import importlib.util
import os
import sys

import pytest

_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
_SCRIPTS = os.path.join(_ROOT, "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)


import normalize_db as ndb  # noqa: E402


@pytest.fixture(scope="module")
def bdb():
    spec = importlib.util.spec_from_file_location("build_db", os.path.join(_SCRIPTS, "build_db.py"))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


# ─── normalize ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "input_,expected",
    [
        ("El Grillo Músico", "grillo musico"),
        ("La Patita (introducción)", "patita"),
        ("  VAMOS A CANTAR  ", "vamos a cantar"),
        ("Los Cien Pies del Ciempiés", "cien pies del ciempies"),
        ("Canción [demo]", "cancion"),
        ("Una   canción", "cancion"),
        ("", ""),
    ],
)
def test_normalize(input_, expected):
    assert ndb._normalize_title(input_) == expected


def test_normalize_does_not_eat_la_of_content_words():
    # Regression: article removal must use " la " (with trailing space) so
    # the "la" inside "lado" survives ("El gusanito medidor ... Lado 2:").
    assert ndb._normalize_title("El gusanito medidor (G. Rincón/V. Rincón); Lado 2:") == (
        "gusanito medidor lado 2"
    )


# ─── levenshtein ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "s,t,want",
    [
        ("", "", 0),
        ("abc", "abc", 0),
        ("abc", "axc", 1),
        ("kitten", "sitting", 3),
        ("", "abc", 3),
        ("abc", "", 3),
        ("a", "b", 1),
    ],
)
def test_levenshtein(s, t, want):
    assert ndb._levenshtein(s, t) == want


# ─── calculateMatchScore ───────────────────────────────────────────────


def test_match_score():
    assert ndb._match_score("hello", "hello") == 1.0
    assert ndb._match_score("", "") == 1.0
    assert ndb._match_score("cancion", "canciones") > 0.6
    assert ndb._match_score("hello", "xyz") < 0.6
    assert ndb._match_score("grillo", "grillo musico") > ndb._match_score("grillo", "xyz")


def test_match_score_bonus_is_one_way():
    # "La rana" (title) must NOT match "LA ARAÑA.txt" (filename): even
    # though "rana" is a substring of "arana" (araña, tilde stripped),
    # the filename is not contained in the title, so no bonus applies
    # and the score stays below the 0.85 threshold.
    rana = ndb._normalize_title("La rana")
    arana = ndb._normalize_title("LA ARAÑA")
    assert ndb._match_score(rana, arana) < 0.85

    # The bonus applies only when the filename is contained in the
    # title. "El gusanito medidor ... Lado 2:" (title) contains the
    # filename "el gusanito medidor", so title-vs-filename scores higher
    # than the reversed (no-bonus) direction.
    gusanito = ndb._normalize_title("El gusanito medidor (G. Rincón/V. Rincón); Lado 2:")
    archivo = ndb._normalize_title("EL GUSANITO MEDIDOR")
    assert archivo in gusanito  # filename ⊆ title
    assert ndb._match_score(gusanito, archivo) > ndb._match_score(archivo, gusanito)


# ─── extractSongTitles ─────────────────────────────────────────────────


def test_extract_song_titles_standard(bdb):
    titles = bdb.extract_song_titles("1. Song One (composer), 2. Song Two; 3. Song Three")
    assert titles == ["Song One", "Song Two", "Song Three"]


def test_extract_song_titles_single(bdb):
    assert bdb.extract_song_titles("1. Only Song") == ["Only Song"]


def test_extract_song_titles_empty(bdb):
    assert bdb.extract_song_titles("") == []


def test_extract_song_titles_no_numbers(bdb):
    assert bdb.extract_song_titles("Sin pistas disponibles") == []


def test_extract_song_titles_sided_lp(bdb):
    titles = bdb.extract_song_titles(
        "Lado 1: 1. First Song (A. Author), 2. Second Song; Lado 2: 3. Third Song"
    )
    assert len(titles) == 3
    assert titles[0] == "First Song"
    assert titles[2] == "Third Song"
    assert titles[1].startswith("Second Song")


def test_extract_song_titles_trailing_punct(bdb):
    assert bdb.extract_song_titles("1. Hello World,") == ["Hello World"]


def test_extract_song_titles_parenthetical(bdb):
    assert bdb.extract_song_titles("1. Mi Canción (Autor Desconocido)") == ["Mi Canción"]


# ─── extractSongMetadata ───────────────────────────────────────────────


def test_extract_song_metadata_closing_block(bdb):
    body = (
        "Apúntate la negra, María…\ncuando te vayas a bailar.\n\n"
        "Dura: 2:08\n"
        "Tema: Familia, Eternidad/ Temporalidad.\n"
        "Personajes: Conejo.\n"
        "\n"
        "M.G.A.\n"
    )
    m = bdb.extract_song_metadata(body)
    assert m.duracion == "2:08"
    assert m.personajes == "Conejo."
    assert m.autor == "M.G.A."
    assert "Apúntate la negra" in m.clean_lyrics
    assert "Dura:" not in m.clean_lyrics
    assert "M.G.A." not in m.clean_lyrics


def test_extract_song_metadata_explicit_autor(bdb):
    body = (
        "Apúntate la negra, María…\n\n"
        "Dura: 4:00\n"
        "Tema: Juventud/ Vejez, Eternidad/ Temporalidad.\n"
        "Personajes: La niña y el gusano\n"
    )
    m = bdb.extract_song_metadata(body)
    assert m.duracion == "4:00"
    assert m.autor == ""


def test_extract_song_metadata_ignores_early_autor(bdb):
    body = (
        "EL GUSANITO MEDIDOR\n\n"
        "Autor: Gilda y Valentín Rincón\n\n"
        "Apúntate la negra…\n\n"
        "Dura: 4:00\n"
        "Tema: Naturaleza/ Cultura-Civilización.\n"
        "Personajes: Niños\n"
    )
    m = bdb.extract_song_metadata(body)
    assert m.duracion == "4:00"
    assert "Gilda y Valentín Rincón" in m.clean_lyrics


def test_extract_song_metadata_no_markers(bdb):
    m = bdb.extract_song_metadata("verse\nchorus\n")
    assert "verse" in m.clean_lyrics
    assert "chorus" in m.clean_lyrics
    assert m.autor == ""
    assert m.duracion == ""


def test_tema_takes_first_segment(bdb):
    body = "verso\n\nDura: 3:00\nTema: Familia, Eternidad/ Temporalidad.\n"
    m = bdb.extract_song_metadata(body)
    assert m.tema == "Familia"
