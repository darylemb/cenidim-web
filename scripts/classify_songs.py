#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
classify_songs.py
Clasifica las canciones en la BD SQLite.

Importante: para el TEMA se respeta el valor literal del campo "Tema:" al
final de cada archivo de LetrasTXT/*.txt. NO se infiere por keywords: el
campo "Tema: ..." es la fuente de verdad (escrito por los autores del
cancionero). Solo se aplica limpieza (paréntesis de "Subtema:", recorte en
la primera coma para obtener el tema principal, colapso de espacios).

Para CLASIFICACIÓN (ESPAÑOL_ESTANDAR / REGIONAL / LENGUA_INDIGENA) y OOV
se usa spaCy (es_core_news_md) como antes.

Uso:
    python3 scripts/classify_songs.py --db letras.db
"""

import argparse
import re
import sqlite3
import sys
from collections import Counter

try:
    import spacy
except ImportError:
    print("ERROR: spacy no está instalado. Ejecuta: pip install spacy")
    sys.exit(1)

try:
    nlp = spacy.load("es_core_news_md")
except OSError:
    print("ERROR: modelo es_core_news_md no encontrado.")
    print("Ejecuta: python -m spacy download es_core_news_md")
    sys.exit(1)

PALABRAS_INDIGENAS = {
    "ihuatsï", "misitu", "sapichu", "turhípiti", "pireri",
    "kukuta", "uarhi", "uichu", "túkuru", "auani",
    "kani", "jarhámuta", "uátsï", "uátsi",
    "axuni", "kuini", "tzintzun", "kuaraki",
    "kurhikaueri", "kutsi", "kutzi", "koki", "kuanasi",
    "kuiris", "japunda", "japonda", "akuitse"
}

STOPWORDS_EXTRA = {
    "el", "la", "los", "las", "lo", "uno", "este", "ese", "esta", "eso", "él",
    "a", "de", "del", "al", "en", "con", "por", "para", "sin", "sobre", "entre", "hasta",
    "y", "o", "ni", "pero", "porque", "si", "como", "cuando",
    "yo", "tú", "tu", "me", "te", "se", "le", "nos", "mi", "mis", "su", "sus",
    "otros", "que", "qué", "ya", "muy", "más", "tan", "todo", "todos",
    "bien", "así", "donde", "ay", "un", "una", "no", "es", "ir", "ser",
    "lai", "ver", "hay"
}

PALABRAS_CORTE = ["Dura:", "Tema:", "Personajes:"]

RE_AUTOR = re.compile(r'^autor\s*[:\.]?\s*', re.IGNORECASE)
RE_PARENTESIS = re.compile(r'\([^)]*\)', re.DOTALL)
RE_TEMA = re.compile(
    r'(?im)^Tema:\s*(.+?)(?=\nPersonajes:|\nDura:|\Z)',
    re.DOTALL | re.MULTILINE,
)
RE_FIRST = re.compile(r'[,;]')


def extract_raw_theme(texto: str) -> str:
    """Extrae el tema literal del campo 'Tema: ...' al final del archivo.

    Devuelve el PRIMER valor (antes de la primera coma o punto y coma),
    con paréntesis de "(Subtema: ...)" eliminados, colapsado, sin
    puntuación final. Si no hay 'Tema:', devuelve ''.
    """
    m = RE_TEMA.search(texto)
    if not m:
        return ''
    raw = m.group(1).strip()
    raw = RE_PARENTESIS.sub('', raw)        # quitar (Subtema: ...)
    raw = RE_FIRST.split(raw, maxsplit=1)[0]
    raw = raw.strip().rstrip('.').strip()
    raw = re.sub(r'\s+', ' ', raw)
    return raw


def extract_all_themes(texto: str) -> list[str]:
    """Devuelve TODOS los temas del campo 'Tema: ...' (split por coma),
    normalizados. Útil para filtrado fino y para construir el catálogo."""
    m = RE_TEMA.search(texto)
    if not m:
        return []
    raw = m.group(1).strip()
    raw = RE_PARENTESIS.sub('', raw)
    parts = [p.strip().rstrip('.').strip() for p in raw.split(',')]
    parts = [re.sub(r'\s+', ' ', p) for p in parts if p]
    return parts


def preprocess_text(texto_raw, song_title=""):
    lineas = texto_raw.split("\n")
    idx_inicio = 0

    if song_title:
        for i, linea in enumerate(lineas):
            if linea.strip().lower() == song_title.strip().lower():
                idx_inicio = i + 1
                break

    while idx_inicio < len(lineas) and not lineas[idx_inicio].strip():
        idx_inicio += 1

    if idx_inicio < len(lineas) and RE_AUTOR.match(lineas[idx_inicio].strip()):
        idx_inicio += 1
        while idx_inicio < len(lineas) and not lineas[idx_inicio].strip():
            idx_inicio += 1

    texto = "\n".join(lineas[idx_inicio:])

    def reemplazar(match):
        return match.group(0) if len(match.group(0)) >= 19 else ""

    texto = RE_PARENTESIS.sub(reemplazar, texto)

    for marca in PALABRAS_CORTE:
        if marca in texto:
            texto = texto.split(marca)[0]

    texto = re.sub(r"\s+", " ", texto.strip())
    texto = texto.replace("|", "").replace("-", "")

    return texto


def clasificacion_oov(texto_raw, song_title="", umbral_estandar=5.0, umbral_regional=18.0):
    texto = preprocess_text(texto_raw, song_title)
    texto = str(texto).lower()
    doc = nlp(texto)

    n_total = 0
    n_oov = 0
    contiene_indigena = False

    for token in doc:
        if (
            token.is_alpha
            and len(token) > 2
            and not token.is_stop
            and token.lemma_ not in STOPWORDS_EXTRA
            and token.text not in STOPWORDS_EXTRA
        ):
            n_total += 1
            if token.is_oov:
                n_oov += 1
            if token.text in PALABRAS_INDIGENAS or token.lemma_ in PALABRAS_INDIGENAS:
                contiene_indigena = True

    pct_oov = (100 * n_oov / n_total) if n_total > 0 else 0

    if contiene_indigena:
        categoria = "LENGUA_INDIGENA"
    elif pct_oov < umbral_estandar:
        categoria = "ESPAÑOL_ESTANDAR"
    elif pct_oov < umbral_regional:
        categoria = "ESPAÑOL_REGIONAL"
    else:
        categoria = "LENGUA_INDIGENA"

    return {
        "pct_oov": pct_oov,
        "categoria": categoria,
        "contiene_indigena": contiene_indigena,
        "n_tokens": n_total,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Clasifica canciones en la BD SQLite (respetando el Tema literal)."
    )
    parser.add_argument("--db", default="letras.db", help="Ruta a la BD SQLite (default: letras.db)")
    args = parser.parse_args()

    con = sqlite3.connect(args.db)
    cur = con.cursor()

    cur.execute("SELECT id, title, lyrics FROM songs WHERE lyrics IS NOT NULL AND lyrics != ''")
    rows = cur.fetchall()

    total = len(rows)
    if total == 0:
        print("No hay canciones con letra para clasificar.")
        con.close()
        return

    cur.execute("CREATE TABLE IF NOT EXISTS song_stats (song_id INTEGER PRIMARY KEY, pct_oov REAL, categoria TEXT, contiene_indigena INTEGER, n_tokens INTEGER)")
    for ddl in [
        "ALTER TABLE songs ADD COLUMN clasificacion TEXT",
        "ALTER TABLE songs ADD COLUMN tema TEXT",
        # Temas crudos: lista completa separada por '||' (no aparece en los
        # 'Tema:' originales), preserva el orden original.
        "ALTER TABLE songs ADD COLUMN temas_raw TEXT",
    ]:
        try:
            cur.execute(ddl)
        except sqlite3.OperationalError:
            pass

    print(f"Procesando {total} canciones con letra (Tema literal + clasificación OOV)...")

    stats_clasificacion = {"ESPAÑOL_ESTANDAR": 0, "ESPAÑOL_REGIONAL": 0, "LENGUA_INDIGENA": 0}
    stats_tema = Counter()
    sin_tema = 0

    for i, (song_id, song_title, lyrics) in enumerate(rows, 1):
        resultado = clasificacion_oov(lyrics, song_title)
        categoria = resultado["categoria"]
        stats_clasificacion[categoria] += 1

        # Tema: literal, no inferido. Se preserva la forma en que aparece
        # en el .txt (después de limpiar "(Subtema: ...)" y cortar en la
        # primera coma).
        tema = extract_raw_theme(lyrics)
        temas_todos = extract_all_themes(lyrics)
        if not tema:
            sin_tema += 1
        else:
            stats_tema[tema] += 1

        cur.execute(
            "UPDATE songs SET clasificacion = ?, tema = ?, temas_raw = ? WHERE id = ?",
            (categoria, tema, '||'.join(temas_todos), song_id),
        )

        cur.execute(
            "INSERT OR REPLACE INTO song_stats (song_id, pct_oov, categoria, contiene_indigena, n_tokens) VALUES (?, ?, ?, ?, ?)",
            (song_id, resultado["pct_oov"], categoria, 1 if resultado["contiene_indigena"] else 0, resultado["n_tokens"]),
        )
        if i % 50 == 0 or i == total:
            print(f"  {i}/{total} procesadas...", flush=True)

    con.commit()
    con.close()

    print("\nClasificación por tipo de español:")
    for cat, count in stats_clasificacion.items():
        print(f"  {cat}: {count}")

    print(f"\nCanciones sin 'Tema:': {sin_tema}")
    print(f"Canciones con 'Tema:' clasificado: {sum(stats_tema.values())}")
    print(f"\nTop 30 temas (literales, normalizados):")
    for tema, count in stats_tema.most_common(30):
        print(f"  {count:3d}  {tema}")


if __name__ == "__main__":
    main()
