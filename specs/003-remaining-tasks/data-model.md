# Data Model: Dashboard Improvements and Docker Security

## Entities

### Song
Represents a musical track in the database.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | INTEGER | Primary key | Auto-increment |
| fonograma_id | INTEGER | Foreign key to fonograma | NOT NULL |
| title | TEXT | Song title | NOT NULL |
| filename | TEXT | Lyrics file reference | Optional |
| lyrics | TEXT | Song lyrics content | Optional, can be empty |
| clasificacion | TEXT | Spanish type classification | ENUM: ESPAÑOL_ESTANDAR, ESPAÑOL_REGIONAL, LENGUA_INDIGENA |
| tema | TEXT | Theme classification | Rule-based keywords (AMOR, NAVIDAD, etc.) |
| created_at | DATETIME | Record creation timestamp | DEFAULT CURRENT_TIMESTAMP |

### Fonograma (Album)
Represents an album/collection of songs.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| clave_fonograma | INTEGER | Primary key | Auto-increment |
| titulo | TEXT | Album title | NOT NULL |
| subtitulo | TEXT | Album subtitle | Optional |
| interprete_principal | TEXT | Main artist | Optional |
| interpretes_invitados | TEXT | Guest artists | Optional |
| interprete_participante | TEXT | Participating artist | Optional |
| soporte_fisico | TEXT | Physical format | Optional |
| editora | TEXT | Publisher | Optional |
| numero_catalogo | TEXT | Catalog number | Optional |
| ciudad_edicion | TEXT | Edition city | Optional |
| pais_edicion | TEXT | Edition country | Optional |
| anio | TEXT | Release year | Can be "s/d" (sin dato) |
| pistas | TEXT | Track list | Optional |
| observaciones | TEXT | Notes | Optional |

### SongStats
Classification statistics for each song (created by classify_songs.py).

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| song_id | INTEGER | Foreign key to songs | NOT NULL |
| pct_oov | REAL | Percentage of out-of-vocabulary words | 0-100 |
| categoria | TEXT | Classification result | ESPAÑOL_ESTANDAR, ESPAÑOL_REGIONAL, LENGUA_INDIGENA |
| contiene_indigena | BOOLEAN | Contains indigenous words | TRUE/FALSE |
| n_tokens | INTEGER | Number of tokens processed | >= 0 |

## Key Metrics (Dashboard)

### StatsResponse (API Contract)

```json
{
  "total_songs": 3858,
  "total_albums": 280,
  "songs_by_year": { "1980": 45, "1981": 52, ... },
  "songs_by_clasificacion": {
    "ESPAÑOL_ESTANDAR": 3491,
    "ESPAÑOL_REGIONAL": 365,
    "LENGUA_INDIGENA": 2
  },
  "recently_added": 12,
  "top_albums": [
    { "album": "Album Title", "year": "1980", "count": 25 }
  ],
  "avg_lyrics_length": 850,
  "songs_with_lyrics": 3200,
  "songs_by_oov_level": {
    "BAJA": 1500,
    "MEDIA": 2000,
    "ALTA": 358
  },
  "songs_by_indigena": {
    "CON_INDIGENA": 45,
    "SIN_INDIGENA": 3813
  },
  "songs_without_year": 1111
}
```

### WordCloudResponse (API Contract)

```json
{
  "words": [
    { "text": "amor", "size": 150 },
    { "text": "corazón", "size": 120 }
  ],
  "totalWords": 50000,
  "excludedStopWords": 12000
}
```

## Relationships

```
fonogramas (1) ──── (N) songs
songs (1) ──── (1) song_stats
```

## Validation Rules

1. **Year field**: Can be "s/d" string or a valid year (1950-2025). Timeline excludes "s/d".
2. **Clasificacion**: Must be one of the three enum values or NULL
3. **Tema**: Must match one of the defined theme keywords or "GENERAL"
4. **Lyrics**: Can be NULL or empty string, both treated as "no lyrics"
5. **OOV Level**: Derived from pct_oov - BAJA (<5%), MEDIA (5-18%), ALTA (>18%)

## Assumptions

- All statistics queries exclude soft-deleted records
- Year "s/d" indicates missing/unknown year data
- Song stats table is populated by classify_songs.py and may be empty if script hasn't run
- Trivy reports follow the standard SARIF format for CI integration