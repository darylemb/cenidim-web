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

3.  (Opcional) Re-validar el match letra↔título (``--fix-lyrics-match``):
    el antiguo builder Go asignaba la letra con un umbral de similitud
    demasiado laxo (0.6), de modo que "Los perritos" recibía la letra
    de "LOS PUERQUITOS.txt" (score ~0.7). Este paso re-evalúa cada
    letra contra los archivos de ``LetrasTXT/`` con el mismo criterio
    del builder corregido (normalización + Levenshtein, umbral 0.85):
    si el match no es fiable, la letra se vacía (mejor sin letra que
    con la letra equivocada).

Uso:
    python3 scripts/normalize_db.py --db letras.db
    python3 scripts/normalize_db.py --db letras.db --lyrics-only
    python3 scripts/normalize_db.py --db letras.db --fix-lyrics-match --letras-dir LetrasTXT
"""

import argparse
import importlib.util
import os
import re
import sqlite3
import unicodedata

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


# ---------------------------------------------------------------------------
# Match letra ↔ título (replica el normalize + score del builder Go)
# ---------------------------------------------------------------------------
_ARTICLES = ("el ", "la ", "los ", "las ", "un ", "una ", "unos ", "unas ")


def _normalize_title(s: str) -> str:
    """Mirror of the Go builder's ``normalize``.

    IMPORTANT: the article removal uses the article WITH its trailing
    space (``" la "``), exactly like Go's ``strings.ReplaceAll(s, " "+a,
    " ")`` with ``a="la "``. Dropping the trailing space turns "lado"
    into "do" (the " la " inside " lado" gets removed), which made the
    matcher attach the wrong lyrics.
    """
    s = re.sub(r"\s*\(.*?\)", "", s)
    s = re.sub(r"\s*\[.*?\]", "", s)
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = unicodedata.normalize("NFC", s)
    for a in _ARTICLES:
        if s.startswith(a):
            s = s[len(a):]
        s = s.replace(" " + a, " ")
    s = re.sub(r"[^\w\s]", "", s)
    # Go's normalize collapses whitespace but does NOT strip internal
    # spaces; the score runs over those strings, so we must too.
    return re.sub(r"\s+", " ", s).strip()


def _levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _match_score(s1: str, s2: str) -> float:
    if s1 == s2:
        return 1.0
    dist = _levenshtein(s1, s2)
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 0.0
    score = 1.0 - dist / max_len
    if s1 in s2 or s2 in s1:
        score += 0.1
    return score


_MATCH_THRESHOLD = 0.85


def _index_lyrics_files(letras_dir: str) -> list[tuple[str, str]]:
    """Return (path, normalized_stem) for every .txt under letras_dir."""
    indexed: list[tuple[str, str]] = []
    for root, _dirs, files in os.walk(letras_dir):
        for f in files:
            if not f.lower().endswith(".txt"):
                continue
            path = os.path.join(root, f)
            stem = os.path.splitext(os.path.basename(f))[0]
            norm = _normalize_title(stem)
            if len(norm) >= 3:
                indexed.append((path, norm))
    return indexed


def fix_lyrics_match(con: sqlite3.Connection, letras_dir: str) -> int:
    """Re-validate every assigned lyric against the .txt files.

    Lyrics whose best match scores below ``_MATCH_THRESHOLD`` are
    cleared (the old fuzzy builder attached wrong lyrics, e.g. "Los
    perritos" got "LOS PUERQUITOS.txt"). Confident matches are kept and
    re-read from the source file so the stored text is the canonical
    one. Returns the number of songs whose lyrics changed.
    """
    indexed = _index_lyrics_files(letras_dir)
    if not indexed:
        raise RuntimeError(f"No hay archivos .txt en {letras_dir}")

    cur = con.cursor()
    cur.execute(
        "SELECT id, title, filename FROM songs "
        "WHERE (lyrics IS NOT NULL AND lyrics != '') "
        "OR (filename IS NOT NULL AND filename != '')"
    )
    rows = cur.fetchall()
    changed = 0
    for song_id, title, _filename in rows:
        nt = _normalize_title(title or "")
        if not nt or len(nt) < 3:
            # Can't evaluate -> clear to avoid wrong lyrics.
            cur.execute("UPDATE songs SET lyrics = '', filename = '' WHERE id = ?", (song_id,))
            changed += 1
            continue

        best_score = 0.0
        best_path = ""
        for path, norm in indexed:
            sc = _match_score(nt, norm)
            if sc > best_score:
                best_score = sc
                best_path = path

        if best_score < _MATCH_THRESHOLD or not best_path:
            cur.execute("UPDATE songs SET lyrics = '', filename = '' WHERE id = ?", (song_id,))
            changed += 1
            continue

        # Confident match: re-read the source file, strip its own header
        # and metadata, and store the cleaned body + canonical filename.
        try:
            with open(best_path, encoding="utf-8", errors="replace") as fh:
                raw = fh.read()
        except OSError:
            continue
        body = clean_lyrics_body(raw, title or "")
        base = os.path.basename(best_path)
        cur.execute(
            "UPDATE songs SET lyrics = ?, filename = ? WHERE id = ?",
            (body, base, song_id),
        )
        changed += 1
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description="Limpia y normaliza letras.db.")
    parser.add_argument("--db", default="letras.db", help="Ruta a la BD SQLite")
    parser.add_argument(
        "--lyrics-only",
        action="store_true",
        help="Solo limpiar lyrics, sin normalizar temas",
    )
    parser.add_argument(
        "--fix-lyrics-match",
        action="store_true",
        help="Re-validar el match letra↔título contra LetrasTXT (umbral 0.85)",
    )
    parser.add_argument(
        "--letras-dir",
        default="LetrasTXT",
        help="Directorio raíz con los archivos .txt de letras",
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

    # ---- Re-validación del match letra↔título (opcional) ----
    if args.fix_lyrics_match:
        n_fixed = fix_lyrics_match(con, args.letras_dir)
        print(f"Letras re-validadas (match < 0.85 -> vaciadas o corregidas): {n_fixed}")

    con.commit()
    con.close()
    print("Listo.")


if __name__ == "__main__":
    main()
