#!/usr/bin/env python3
"""
normalize_db.py
Limpia y normaliza la base de datos SQLite de letras.

Sin dependencias pesadas (no usa spaCy): puede ejecutarse en cualquier
momento, tanto contra una BD recién construida como contra una
existente, para:

1.  Limpiar el cuerpo de la letra (``songs.lyrics``):
    - quita la cabecera de la primera línea cuando es el título del
      .txt (coincide con ``title`` o sigue el patrón "cabecera +
      línea en blanco"),
    - elimina líneas de metadatos (``Dura:``, ``Tema:``, ``Subtema:``,
      ``Personajes:``, ``Autor:``, ``Compositor:``, ``Comp:``) que
      algunos archivos conservan al pie, y la atribución "Autor:" que
      a veces aparece bajo el título,
    - colapsa líneas en blanco consecutivas al inicio.

    Así la nube de palabras refleja solo el léxico de la letra y no
    cabeceras, autores ni marcadores (revisión 01/jul/2026, puntos 15
    y 16).

2.  Normalizar los temas (``songs.tema``) con ``canonical_tema`` +
    ``TEMA_TYPO_MAP`` de ``app.models.theme_normalization``, de modo
    que "Solidarida/Individualismo" y "Solidaridad/Individualismo"
    colapsen en una sola entrada en la base (punto 11).

Es idempotente: ejecutarlo varias veces no cambia el resultado.

Uso:
    python3 scripts/normalize_db.py --db letras.db
    python3 scripts/normalize_db.py --db letras.db --lyrics-only
"""

import argparse
import importlib.util
import os
import re
import sqlite3

_META_LINE_RE = re.compile(
    r"^\s*(?:dura|duracion|duración|tema|subtema|personajes|autor|compositor|comp)\s*:",
    re.IGNORECASE,
)


def _load_canonical_tema():
    """Load ``canonical_tema`` directly from theme_normalization.py.

    Importing ``app.models`` pulls in the package ``__init__`` which
    needs SQLAlchemy; this script must run without the FastAPI venv.
    theme_normalization.py itself only uses the stdlib, so a bare
    importlib load is enough.
    """
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "backend-fastapi",
        "app",
        "models",
        "theme_normalization.py",
    )
    spec = importlib.util.spec_from_file_location("theme_normalization", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"No se pudo cargar {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.canonical_tema


canonical_tema = _load_canonical_tema()


def _title_norm(song_title: str) -> str:
    return song_title.strip().lower()

def _norm_token(s: str) -> str:
    """Lowercase, strip and drop trailing punctuation for header match."""
    s = s.strip().lower()
    s = re.sub(r"[.,;:!¡¿]+$", "", s)
    return re.sub(r"\s+", " ", s)


def clean_lyrics_body(lyrics: str, song_title: str = "") -> str:
    """Remove header lines, metadata markers and leading blank noise.

    Idempotent: every header-like line is removed in one pass (the
    ``while`` loop consumes consecutive header lines), so running it
    twice never removes lyric content. A line is only treated as a
    header when it (a) matches the song title exactly (case-insensitive,
    punctuation-insensitive) or (b) is followed by a blank line — the
    classic ``.txt`` "TITLE + blank + lyrics" layout. Metadata marker
    lines (``Dura:``, ``Tema:``, ``Personajes:``, ``Autor:``, …) are
    dropped anywhere.
    """
    if not lyrics or not lyrics.strip():
        return lyrics

    lines = lyrics.split("\n")
    title_norm = _norm_token(song_title)

    # 1. Consume every consecutive leading header line. Both rules are
    #    evaluated against the *current* first line, so after one pass
    #    the first line is real lyric content and a second pass is a
    #    no-op.
    while lines:
        while lines and not lines[0].strip():
            lines.pop(0)
        if not lines:
            break
        first = lines[0].strip()
        second_blank = len(lines) > 1 and not lines[1].strip()
        is_title = bool(title_norm) and _norm_token(first) == title_norm
        if is_title or second_blank:
            lines.pop(0)
            continue
        break

    # 2. Drop metadata marker lines anywhere (footer block, early
    #    "Autor:" attribution, ...).
    cleaned = [line for line in lines if not _META_LINE_RE.match(line)]

    # 3. Collapse repeated blank lines at the start.
    while cleaned and not cleaned[0].strip():
        cleaned.pop(0)

    return "\n".join(cleaned).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Limpia y normaliza letras.db.")
    parser.add_argument("--db", default="letras.db", help="Ruta a la BD SQLite")
    parser.add_argument(
        "--lyrics-only",
        action="store_true",
        help="Solo limpiar lyrics, sin normalizar temas",
    )
    args = parser.parse_args()

    con = sqlite3.connect(args.db)
    cur = con.cursor()

    # ---- Temas: normalización canónica (con typos) ----
    if not args.lyrics_only:
        cur.execute("SELECT id, tema FROM songs WHERE tema IS NOT NULL AND tema != ''")
        rows = cur.fetchall()
        n_changed = 0
        for song_id, tema in rows:
            canon = canonical_tema(tema)
            if canon and canon != tema:
                cur.execute("UPDATE songs SET tema = ? WHERE id = ?", (canon, song_id))
                n_changed += 1
        print(f"Temas normalizados: {n_changed} de {len(rows)}")

    # ---- Lyrics: limpieza de cabeceras y metadatos ----
    cur.execute("SELECT id, title, lyrics FROM songs WHERE lyrics IS NOT NULL AND lyrics != ''")
    rows = cur.fetchall()
    n_cleaned = 0
    for song_id, title, lyrics in rows:
        body = clean_lyrics_body(lyrics, title or "")
        if body != lyrics:
            cur.execute("UPDATE songs SET lyrics = ? WHERE id = ?", (body, song_id))
            n_cleaned += 1
    print(f"Letras limpiadas: {n_cleaned} de {len(rows)}")

    con.commit()
    con.close()
    print("Listo.")


if __name__ == "__main__":
    main()
