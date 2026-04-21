# -*- coding: utf-8 -*-
"""
classify_songs.py
Clasifica las canciones en la BD SQLite usando spaCy (es_core_news_sm).
Debe ejecutarse DESPUÉS de build-db (Go), sobre la misma BD resultante.

Uso:
    python3 scripts/classify_songs.py --db letras.db
"""

import argparse
import sqlite3
import sys

try:
    import spacy
except ImportError:
    print("ERROR: spacy no está instalado. Ejecuta: pip install spacy")
    sys.exit(1)

try:
    nlp = spacy.load("es_core_news_sm")
except OSError:
    print("ERROR: modelo es_core_news_sm no encontrado.")
    print("Ejecuta: python -m spacy download es_core_news_sm")
    sys.exit(1)

# Diccionario de palabras indígenas (Purépecha/Michoacán)
PALABRAS_INDIGENAS = {
    "ihuatsï", "misitu", "sapichu", "turhípiti", "pireri",
    "kukuta", "uarhi", "uichu", "túkuru", "auani",
    "kani", "jarhámuta", "uátsï", "uátsi",
    "axuni", "kuini", "tzintzun", "kuaraki",
    "kurhikaueri", "kutsi", "kutzi", "koki", "kuanasi",
    "kuiris", "japunda", "japonda", "akuitse",
}


def clasificacion_oov(texto, umbral_regional=5):
    """
    Clasifica un texto según porcentaje de palabras fuera de vocabulario (OOV)
    y presencia de palabras indígenas.

    Returns dict con:
        - pct_oov: float
        - categoria: ESPAÑOL_ESTANDAR | ESPAÑOL_REGIONAL | LENGUA_INDIGENA
        - contiene_indigena: bool
        - n_tokens: int
    """
    texto = str(texto).lower()
    doc = nlp(texto)

    total = 0
    oov = 0
    palabras = []

    for token in doc:
        if token.is_alpha and len(token) > 2 and not token.is_stop:
            total += 1
            palabras.append(token.text)
            if token.is_oov:
                oov += 1

    pct_oov = (oov / total) * 100 if total > 0 else 0
    contiene_indigena = any(p in PALABRAS_INDIGENAS for p in palabras)

    if pct_oov >= umbral_regional and contiene_indigena:
        categoria = "LENGUA_INDIGENA"
    elif pct_oov >= umbral_regional:
        categoria = "ESPAÑOL_REGIONAL"
    else:
        categoria = "ESPAÑOL_ESTANDAR"

    return {
        "pct_oov": pct_oov,
        "categoria": categoria,
        "contiene_indigena": contiene_indigena,
        "n_tokens": total,
    }


def main():
    parser = argparse.ArgumentParser(description="Clasifica canciones en la BD SQLite.")
    parser.add_argument("--db", default="letras.db", help="Ruta a la BD SQLite (default: letras.db)")
    args = parser.parse_args()

    con = sqlite3.connect(args.db)
    cur = con.cursor()

    cur.execute("SELECT id, lyrics FROM songs WHERE lyrics IS NOT NULL AND lyrics != ''")
    rows = cur.fetchall()

    total = len(rows)
    if total == 0:
        print("No hay canciones con letra para clasificar.")
        con.close()
        return

    print(f"Clasificando {total} canciones con letra...")

    update_cur = con.cursor()
    stats = {"ESPAÑOL_ESTANDAR": 0, "ESPAÑOL_REGIONAL": 0, "LENGUA_INDIGENA": 0}

    for i, (song_id, lyrics) in enumerate(rows, 1):
        resultado = clasificacion_oov(lyrics)
        categoria = resultado["categoria"]
        stats[categoria] += 1
        update_cur.execute(
            "UPDATE songs SET clasificacion = ? WHERE id = ?",
            (categoria, song_id),
        )
        if i % 50 == 0 or i == total:
            print(f"  {i}/{total} procesadas...", flush=True)

    con.commit()
    con.close()

    print("\nClasificación completada:")
    for cat, count in stats.items():
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
