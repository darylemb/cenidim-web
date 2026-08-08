#!/usr/bin/env python3
"""
build_db.py — Python port of backend/cmd/build-db/main.go.

Regenerates letras.db from db_fonografia.csv + LetrasTXT/*.txt with the
same schema and behaviour as the retired Go builder:

  - creates the base tables (fonogramas, songs, users) exactly as the
    Go tool did — the FastAPI entrypoint then applies alembic on top,
  - parses the CSV (14 fields, lenient quoting, variable-width rows),
  - extracts per-track titles from the "Pistas" column,
  - matches each track to a lyric .txt via the same normalize +
    Levenshtein scoring as Go (threshold 0.85 — the fix that stopped
    "Los perritos" from getting "LOS PUERQUITOS.txt"),
  - parses the lyric metadata footer (Dura:, Tema:, Personajes:,
    Autor:, Compositor: + initials fallback) and stores a clean body,
  - creates the default admin user with a bcrypt(plain) hash, which
    the FastAPI login accepts via its legacy-password fallback.

The output DB is byte-compatible with what the Go builder produced, so
`docker compose up` and the FastAPI runtime behave identically.

Usage:
    python3 scripts/build_db.py --csv db_fonografia.csv --db letras.db \
        --letras LetrasTXT --admin-pass admin123
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sqlite3
from pathlib import Path

try:
    import bcrypt
except ImportError:
    bcrypt = None  # type: ignore[assignment]

from normalize_db import (  # noqa: E402
    _clean_track_suffix,
    _match_score,
    _normalize_title,
)

TRACK_RE = re.compile(r"\d+\.\s+")
TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")
PAREN_RE = re.compile(r"\s*\(.*?\)")
RE_DURA = re.compile(r"^Dura:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
RE_PERSONAJES = re.compile(r"^Personajes:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
RE_TEMA = re.compile(r"^Tema:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
RE_AUTOR = re.compile(r"^Autor:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
RE_COMPOSITOR = re.compile(r"^Compositor:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
RE_INITIALS = re.compile(r"(?m)^[A-Z](?:\.[A-Z]){1,4}\.?$")
RE_TEMA_SEGMENT = re.compile(r"[,;]")
RE_TEMA_PAREN = re.compile(r"\s*\([^)]*\)")

MATCH_THRESHOLD = 0.85

_SCHEMA = """
CREATE TABLE fonogramas (
    clave_fonograma    INTEGER PRIMARY KEY,
    titulo             TEXT NOT NULL,
    subtitulo          TEXT,
    interprete_principal   TEXT,
    interpretes_invitados  TEXT,
    interprete_participante TEXT,
    soporte_fisico     TEXT,
    editora            TEXT,
    numero_catalogo    TEXT,
    ciudad_edicion     TEXT,
    pais_edicion       TEXT,
    anio               TEXT,
    pistas             TEXT,
    observaciones      TEXT,
    version            INTEGER DEFAULT 0
);
CREATE TABLE songs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    fonograma_id   INTEGER NOT NULL,
    title          TEXT NOT NULL,
    filename       TEXT,
    lyrics         TEXT,
    clasificacion  TEXT,
    tema           TEXT,
    autor          TEXT,
    compositor     TEXT,
    duracion       TEXT,
    personajes     TEXT,
    temas_raw      TEXT,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    version        INTEGER DEFAULT 0,
    FOREIGN KEY (fonograma_id) REFERENCES fonogramas(clave_fonograma)
);
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'viewer',
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    version       INTEGER DEFAULT 0
);
"""


def _read_internal_title(path: str) -> str:
    """First non-blank line of a lyrics .txt — the song's real title."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                s = line.strip()
                if s:
                    return s
    except OSError:
        pass
    return ""


def _index_lyrics_by_internal_title(letras_dir: str) -> list[tuple[str, str]]:
    """Index every .txt by its INTERNAL title (first line), not its
    filename. The filename can be misspelled (\"PALOMES\", \"CHIPICHIPI\")
    or abbreviated; the internal title is the actual song identity, so
    matching against it avoids both false positives (\"La rana\" vs
    \"LA ARAÑA\") and false negatives.
    """
    indexed: list[tuple[str, str]] = []
    for dirpath, _dirs, files in os.walk(letras_dir):
        for fname in files:
            if not fname.lower().endswith(".txt"):
                continue
            if fname.startswith(".") or fname == ".txt":
                continue
            path = os.path.join(dirpath, fname)
            internal = _normalize_title(_read_internal_title(path))
            if len(internal) >= 3:
                indexed.append((path, internal))
    return indexed


def find_lyrics_file(
    root: str,
    target_title: str,
    index: list[tuple[str, str]] | None = None,
) -> str:
    """Best .txt for ``target_title``, scored against the INTERNAL title."""
    nt = _normalize_title(_clean_track_suffix(target_title))
    if len(nt) < 3:
        return ""

    if index is None:
        index = _index_lyrics_by_internal_title(root)

    best_match = ""
    best_score = -1.0
    for path, nf in index:
        score = _match_score(nt, nf)
        if score >= MATCH_THRESHOLD and score > best_score:
            best_score = score
            best_match = path
    return best_match


def extract_song_titles(pistas: str) -> list[str]:
    """Mirror of Go's extractSongTitles."""
    matches = list(TRACK_RE.finditer(pistas))
    if not matches:
        return []
    titles: list[str] = []
    for i, m in enumerate(matches):
        start = m.end()
        if i + 1 < len(matches):
            raw = pistas[start : matches[i + 1].start()]
        else:
            raw = pistas[start:]
        raw = raw.rstrip(" ,;")
        raw = TRAILING_PAREN_RE.sub("", raw)
        raw = raw.strip()
        if raw:
            titles.append(raw)
    return titles


class SongMetadata:
    __slots__ = ("autor", "compositor", "duracion", "personajes", "tema", "clean_lyrics")

    def __init__(self) -> None:
        self.autor = ""
        self.compositor = ""
        self.duracion = ""
        self.personajes = ""
        self.tema = ""
        self.clean_lyrics = ""


def extract_song_metadata(lyrics_text: str) -> SongMetadata:
    """Mirror of Go's extractSongMetadata."""
    m = SongMetadata()
    m.clean_lyrics = lyrics_text
    if not lyrics_text.strip():
        return m

    cut = lyrics_text.rfind("\nDura:")
    if cut < 0:
        cut = lyrics_text.rfind("\nTema:")
    if cut >= 0:
        head = lyrics_text[:cut]
        tail = lyrics_text[cut:]
        m.clean_lyrics = head.strip()

        dura = RE_DURA.search(tail)
        if dura:
            m.duracion = dura.group(1).strip()
        pers = RE_PERSONAJES.search(tail)
        if pers:
            m.personajes = pers.group(1).strip()
        tema = RE_TEMA.search(tail)
        if tema:
            raw = tema.group(1).strip()
            raw = RE_TEMA_PAREN.sub("", raw)
            raw = RE_TEMA_SEGMENT.split(raw, 1)[0]
            raw = raw.strip().rstrip(".")
            m.tema = raw.strip()
        autor = RE_AUTOR.search(tail)
        if autor:
            m.autor = autor.group(1).strip()
        else:
            init = RE_INITIALS.search(tail)
            if init:
                m.autor = init.group(0)
        comp = RE_COMPOSITOR.search(tail)
        if comp:
            m.compositor = comp.group(1).strip()
    return m


def load_lyrics(
    letras_root: str,
    track_title: str,
    index: list[tuple[str, str]] | None = None,
) -> tuple[str, str, SongMetadata]:
    """Mirror of Go's loadLyrics (match by internal title)."""
    found = find_lyrics_file(letras_root, track_title, index)
    if not found:
        return "", "", SongMetadata()
    try:
        content = Path(found).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "", "", SongMetadata()

    filename = os.path.basename(found)
    parts = content.split("\n", 1)
    if parts and _normalize_title(parts[0].strip()) == _normalize_title(track_title):
        content = parts[1].strip() if len(parts) > 1 else ""
    md = extract_song_metadata(content)
    return md.clean_lyrics.strip(), filename, md


def build_database(*, csv_path: str, db_path: str, letras_dir: str, admin_pass: str) -> None:
    if not admin_pass:
        raise SystemExit("❌ --admin-pass is required")
    if bcrypt is None:
        raise SystemExit("❌ 'bcrypt' is required (pip install bcrypt)")

    print(f"🚀 Parsing {csv_path} and building database at {db_path}...")

    # Remove existing DB.
    if os.path.exists(db_path):
        os.remove(db_path)

    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.executescript(_SCHEMA)

    # Pre-index the lyric corpus by internal title once (loadLyrics /
    # find_lyrics_file reuse it for every track).
    lyrics_index = _index_lyrics_by_internal_title(letras_dir)

    with open(csv_path, encoding="utf-8", errors="replace", newline="") as fh:
        reader = csv.reader(fh)
        next(reader, None)  # skip header

        fonograma_count = 0
        song_count = 0

        for record in reader:
            if not record:
                continue
            # Pad record to 14 fields.
            record = (record + [""] * 14)[:14]

            clave_str = record[0].strip()
            if not clave_str:
                continue
            try:
                clave = int(clave_str)
            except ValueError:
                print(f"⚠️ Non-numeric ClavedeFonograma '{clave_str}', skipping")
                continue

            titulo = record[1].strip()
            if not titulo:
                continue

            cur.execute(
                "INSERT OR REPLACE INTO fonogramas "
                "(clave_fonograma, titulo, subtitulo, interprete_principal, interpretes_invitados, "
                "interprete_participante, soporte_fisico, editora, numero_catalogo, ciudad_edicion, "
                "pais_edicion, anio, pistas, observaciones) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    clave, titulo, record[2].strip(), record[3].strip(), record[4].strip(),
                    record[5].strip(), record[6].strip(), record[7].strip(),
                    record[8].strip(), record[9].strip(), record[10].strip(),
                    record[11].strip(), record[12].strip(), record[13].strip(),
                ),
            )
            fonograma_count += 1

            for track_title in extract_song_titles(record[12].strip()):
                lyrics_text, filename, md = load_lyrics(letras_dir, track_title, lyrics_index)
                if filename:
                    print(f"🔍 Matched: '{track_title}' -> {filename}")
                cur.execute(
                    "INSERT INTO songs "
                    "(fonograma_id, title, filename, lyrics, autor, compositor, duracion, personajes, tema) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (
                        clave, track_title, filename, lyrics_text,
                        md.autor, md.compositor, md.duracion, md.personajes, md.tema,
                    ),
                )
                song_count += 1

    # Default admin user.
    hash_b = bcrypt.hashpw(admin_pass.encode("utf-8"), bcrypt.gensalt())
    cur.execute(
        "INSERT OR IGNORE INTO users (username, email, password_hash, role) "
        "VALUES ('admin', 'admin@cenidim.mx', ?, 'admin')",
        (hash_b.decode("ascii"),),
    )

    con.commit()
    con.close()

    print(f"✅ Database built successfully in '{db_path}'!")
    print(f"📊 Summary: {fonograma_count} Fonogramas, {song_count} Songs inserted.")
    print("👤 Admin user created: admin")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build letras.db from CSV + LetrasTXT (Python port).")
    parser.add_argument("--csv", default="../db_fonografia.csv", help="Path to db_fonografia.csv")
    parser.add_argument("--db", default="letras.db", help="Path to the SQLite database file")
    parser.add_argument("--letras", default="../LetrasTXT", help="Path to LetrasTXT directory")
    parser.add_argument("--admin-pass", default="", help="Initial admin user password (required)")
    args = parser.parse_args()

    build_database(
        csv_path=args.csv,
        db_path=args.db,
        letras_dir=args.letras,
        admin_pass=args.admin_pass,
    )


if __name__ == "__main__":
    main()
