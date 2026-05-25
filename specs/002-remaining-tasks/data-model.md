# Data Model: Data Quality & Visualization Fixes

**Feature**: 002-remaining-tasks
**Date**: 2026-05-24

## Entities

### Song (existing, modifying)

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | INTEGER | Primary key | NOT NULL |
| titulo | TEXT | Song title | NOT NULL |
| album_id | INTEGER | Foreign key to album | NOT NULL |
| year | TEXT | Year (can be "s/d") | NOT NULL |
| letra | TEXT | Lyrics content | Can be NULL |
| clasificacion | TEXT | Spanish classification type | ENUM: ESPAÑOL_ESTANDAR, ESPAÑOL_REGIONAL, LENGUA_INDIGENA |
| tema | TEXT | Theme category | NEW: rule-based classification |

### Album (existing)

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER | Primary key |
| clave | TEXT | Album key/code |
| titulo | TEXT | Album title |
| interprete | TEXT | Artist/interpreter |
| year | TEXT | Year (can be "s/d") |
| pais | TEXT | Country |
| editora | TEXT | Publisher |

### SongStats (existing)

| Field | Type | Description |
|-------|------|-------------|
| id | INTEGER | Primary key |
| song_id | INTEGER | Foreign key to song |
| clasificacion | TEXT | Classification type |
| created_at | TIMESTAMP | Record creation |

## New API Responses

### GET /api/word-cloud

Response:
```json
{
  "words": [
    { "text": "amor", "size": 100 },
    { "text": "niño", "size": 85 },
    { "text": "gato", "size": 70 }
  ],
  "totalWords": 1500,
  "excludedStopWords": 4500
}
```

### GET /api/stats (modified)

Additional response field:
```json
{
  "songsWithoutYear": 25,
  "yearDistribution": { ... }
}
```

## Theme Classification Rules

| Theme | Keywords (Spanish) | Priority |
|-------|-------------------|----------|
| NAVIDAD | navidad, nochebuena, reyes, belen, villancico | 1 |
| AMOR | amor, corazon, beso, querer, te amo | 2 |
| ANIMALES | gato, perro, pajaro, pez, leon | 3 |
| ESCUELA | escuela, maestro, aprender, libro, clase | 4 |
| FIESTA | fiesta, bailar, musica, celebrar | 5 |
| FAMILIA | mama, papa, abuelito, hermano, familia | 6 |
| NATURALEZA | sol, luna, estrella, mar, rio, arbol | 7 |
| TRADICIONAL | ronda, juego, jugar, amigos | 8 |
| GENERAL | (default when no keywords match) | 9 |

## Data Integrity Rules

1. All songs MUST have exactly one clasificacion OR be unclassified (0 acceptable)
2. Sum of (ESPAÑOL_ESTANDAR + ESPAÑOL_REGIONAL + LENGUA_INDIGENA) MUST equal total classified songs
3. Songs with year="s/d" MUST be excluded from year-based charts
4. Theme is deterministically computed from lyrics (no randomness)