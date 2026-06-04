# -*- coding: utf-8 -*-
"""
classify_songs.py
Clasifica las canciones en la BD SQLite usando spaCy (es_core_news_md).
Debe ejecutarse DESPUÉS de build-db (Go), sobre la misma BD resultante.

Uso:
    python3 scripts/classify_songs.py --db letras.db
"""

import argparse
import re
import sqlite3
import sys

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
RE_PARENTESIS = re.compile(r'\(.*?\)', re.DOTALL)

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
        "playa", "montaña", "río", "rio", "lago", "campo", "flor",
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
        "libertad", "libre", "soldado", "ejército", "ejercito",
        "guerrero", "heroico", "heroes", "héroes",
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


def preprocess_text(texto_raw, song_title=""):
    """
    Preprocesa el texto de la canción aplicando filtros mejorados.
    1. Elimina encabezados (título + autor)
    2. Elimina paréntesis cortos (< 19 chars)
    3. Corta metadatos finales (Dura:, Tema:, Personajes:)
    4. Limpieza general
    """
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
    """
    Clasifica un texto según porcentaje de palabras fuera de vocabulario (OOV)
    y presencia de palabras indígenas.

    Returns dict con:
        - pct_oov: float
        - categoria: ESPAÑOL_ESTANDAR | ESPAÑOL_REGIONAL | LENGUA_INDIGENA
        - contiene_indigena: bool
        - n_tokens: int
    """
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


def clasificar_tema(texto):
    texto_lower = texto.lower()

    theme_scores = {}
    for tema, keywords in TEMA_KEYWORDS.items():
        score = 0
        for kw in keywords:
            pattern = r'\b' + re.escape(kw.lower()) + r'\b'
            if re.search(pattern, texto_lower):
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

    cur.execute("SELECT id, title, lyrics FROM songs WHERE lyrics IS NOT NULL AND lyrics != ''")
    rows = cur.fetchall()

    total = len(rows)
    if total == 0:
        print("No hay canciones con letra para clasificar.")
        con.close()
        return

    cur.execute("CREATE TABLE IF NOT EXISTS song_stats (song_id INTEGER PRIMARY KEY, pct_oov REAL, categoria TEXT, contiene_indigena INTEGER, n_tokens INTEGER)")
    try:
        cur.execute("ALTER TABLE songs ADD COLUMN clasificacion TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cur.execute("ALTER TABLE songs ADD COLUMN tema TEXT")
    except sqlite3.OperationalError:
        pass

    print(f"Clasificando {total} canciones con letra...")

    stats_clasificacion = {"ESPAÑOL_ESTANDAR": 0, "ESPAÑOL_REGIONAL": 0, "LENGUA_INDIGENA": 0}
    stats_tema = {}

    for i, (song_id, song_title, lyrics) in enumerate(rows, 1):
        resultado = clasificacion_oov(lyrics, song_title)
        categoria = resultado["categoria"]
        stats_clasificacion[categoria] += 1

        tema = clasificar_tema(lyrics)
        if tema not in stats_tema:
            stats_tema[tema] = 0
        stats_tema[tema] += 1

        cur.execute(
            "UPDATE songs SET clasificacion = ?, tema = ? WHERE id = ?",
            (categoria, tema, song_id),
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

    print("\nClasificación por tema:")
    for tema, count in sorted(stats_tema.items(), key=lambda x: -x[1]):
        print(f"  {tema}: {count}")


if __name__ == "__main__":
    main()