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

# Keywords para clasificación de temas (sin ML - solo palabras clave)
TEMA_KEYWORDS = {
    "NAVIDAD": [
        "navidad", "navideña", "navideño", "reyes", "rey magos", "nochebuena",
        "santa claus", "santa", "papa noel", "villancico", "estrella",
        "belén", "portal", "advent", "winter christmas",
    ],
    "AMOR": [
        "amor", "te amo", "te quiero", "corazón", "besos", "beso", "cariño",
        "querer", "amar", "enamorado", "enamorada", "amorosa", "amoros",
        "mi amor", "mi cielo", "mi vida", "corazón", "sentimientos",
        "pasión", "apasionado", "dulce", "ternura", "caricia", "abrazo",
        "amor mio", "te adoro", "adoro", "amor eterno", "amor infinito",
    ],
    "DESPECHO": [
        "despecho", "traición", "traicionado", "engañado", "engañada",
        "mentiras", "mentiroso", "mentirosa", "infiel", "por qué",
        "me dejó", "me deja", "me abandono", "abandono", "llanto",
        "llorar", "dolor", "sufrimiento", "sufrir", "corazón roto",
        "heartbreak", "broken heart", "despedida", "adiós", "adios",
    ],
    "FIESTA": [
        "fiesta", "bailar", "baile", "danza", "danzar", "celebrar",
        "celebración", "fiesta", "festejo", "festejar", "rumba",
        "botellón", "copa", "brindis", "champagne", "vino", "cerveza",
        "carnaval", "feria", "verbena", "verbena", "jarana", "juerga",
        "pedas", "peda", "borrachera", "borracho", "borracha",
    ],
    "ANIMALES": [
        "perro", "gato", "caballo", "vaca", "cerdo", "gallina",
        "pájaro", "pajaro", "ave", "pez", "pez", "mariposa",
        "mariposa", "abeja", "hormiga", "león", "tigre", "oso",
        "lobo", "zorro", "conejo", "ratón", "raton", "elefante",
        "mono", "loro", "paloma", "tortuga", "serpiente", "cobra",
        "burro", "mula", "buey", "cabra", "oveja", "pato", "ganso",
    ],
    "NATURALEZA": [
        "sol", "luna", "estrella", "estrellas", "cielo", "mar",
        "playa", "montaña", "río", "rio", " lago", "campo", "flor",
        "flores", "árbol", "arbol", "bosque", "selva", "jungla",
        "lluvia", "lloviendo", "nube", "nubes", "viento", "tormenta",
        "trueno", "rayo", "amanecer", "atardecer", "anochecer",
        "amanata", "flor de", "flores de", "planta", "verde",
    ],
    "RELIGIOSO": [
        "dios", "Señor", "Santo", "santo", "virgen", "María", "maria",
        "Jesús", "jesus", "cristo", "cruz", "iglesia", "iglesia",
        "oración", "oracion", "rezar", "rezando", "bendición", "bendicion",
        "alma", "ánima", "anima", "esperanza", "fe", "gloria",
        "aleluya", "amen", "padre nuestro", "ave maría", "padre",
    ],
    "PATRIOTICO": [
        "patria", "país", "pais", "méxico", "mexico", "bander", "himno",
        "independencia", "revolución", "revolucion", "revolucionario",
        "patriota", "patriotismo", "nacional", "viva", "honor",
        "libertad", "libre", "libertad", "soldado", "ejército", "ejercito",
        "guerrero", "heroico", "heroes", "héroes", "meth", "meth",
    ],
    "DROGAS": [
        "droga", "drogas", "cocaína", "cocaina", "marihuana", "marijuana",
        "weed", "cocaine", "heroína", "heroina", "crack", "metanfetamina",
        "cristal", "meth", "fentanilo", "oxicodona", "pastillas", "pastilla",
        "barbital", " LSD", "ácido", "acido", "trip", "high", "colocón",
        "colocada", "colocado", "drogado", "drogada", "pedo", "borracho",
    ],
    "POLITICA": [
        "presidente", "gobierno", "gobiern", "político", "politico",
        "votar", "voto", "elección", "eleccion", "democracia", "partido",
        "congreso", "senado", "ley", "leyes", "reforma", "reformas",
        "corrupción", "corrupcion", "corrupto", "narco", "narcotráfico",
        "narcotrafico", "cartel", "violencia", "militares", "militares",
    ],
}

# Palabras comunes a excluir de matching
TEMA_STOP_WORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del",
    "al", "a", "en", "con", "por", "para", "sin", "sobre", "entre",
    "es", "son", "está", "estan", "ser", "estar", "fue", "fueron",
    "lo", "que", "y", "e", "o", "u", "pero", "porque", "como",
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


def clasificar_tema(texto):
    """
    Clasifica el tema de una canción usando keywords (sin ML).
    Returns: tema string (e.g., "AMOR", "NAVIDAD", "DESPECHO") or "GENERAL" si no hay match.
    """
    texto_lower = texto.lower()

    theme_scores = {}
    for tema, keywords in TEMA_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw.lower() in texto_lower:
                score += 1
        if score > 0:
            theme_scores[tema] = score

    if not theme_scores:
        return "GENERAL"

    return max(theme_scores, key=theme_scores.get)


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

    # Create tables if not exist
    update_cur = con.cursor()
    update_cur.execute("CREATE TABLE IF NOT EXISTS song_stats (song_id INTEGER PRIMARY KEY, pct_oov REAL, categoria TEXT, contiene_indigena INTEGER, n_tokens INTEGER)")
    try:
        update_cur.execute("ALTER TABLE songs ADD COLUMN clasificacion TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists
    try:
        update_cur.execute("ALTER TABLE songs ADD COLUMN tema TEXT")
    except sqlite3.OperationalError:
        pass  # Column already exists

    print(f"Clasificando {total} canciones con letra...")

    stats_clasificacion = {"ESPAÑOL_ESTANDAR": 0, "ESPAÑOL_REGIONAL": 0, "LENGUA_INDIGENA": 0}
    stats_tema = {}

    for i, (song_id, lyrics) in enumerate(rows, 1):
        resultado = clasificacion_oov(lyrics)
        categoria = resultado["categoria"]
        stats_clasificacion[categoria] += 1

        tema = clasificar_tema(lyrics)
        if tema not in stats_tema:
            stats_tema[tema] = 0
        stats_tema[tema] += 1

        update_cur.execute(
            "UPDATE songs SET clasificacion = ?, tema = ? WHERE id = ?",
            (categoria, tema, song_id),
        )

        update_cur.execute(
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

    print("\nClasificación por tema:")
    for tema, count in sorted(stats_tema.items(), key=lambda x: -x[1]):
        print(f"  {tema}: {count}")


if __name__ == "__main__":
    main()
