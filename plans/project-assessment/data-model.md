# Data Model: Project Assessment Implementation

**Date**: 2026-05-10  
**Context**: Security hardening, backend optimization, and frontend enhancement

---

## Entities

### 1. User (existing)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | int64 | PK, auto-increment | |
| username | string | UNIQUE, NOT NULL | |
| email | string | UNIQUE, NOT NULL | |
| password_hash | string | NOT NULL | bcrypt |
| role | string | NOT NULL | "viewer" \| "editor" \| "admin" |
| created_at | datetime | NOT NULL | |

### 2. Fonograma (existing)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| clave_fonograma | string | PK | |
| titulo | string | | |
| anio | int | | Year for timeline |
| ... | ... | | Additional metadata |

### 3. Song (existing)

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | int64 | PK, auto-increment | |
| fonograma_id | string | FK → fonograma.clave_fonograma | |
| title | string | NOT NULL | |
| lyrics | text | | |
| clasificacion | string | | Classification category |
| ... | ... | | Additional fields |

### 4. Stats (NEW - API Response)

| Field | Type | Notes |
|-------|------|-------|
| total_songs | int | COUNT(*) from songs |
| total_albums | int | COUNT(DISTINCT fonograma_id) |
| songs_by_year | map[string]int | Grouped by fonograma.anio |
| songs_by_clasificacion | map[string]int | Grouped by clasificacion |
| recently_added | int | Last 30 days count |

---

## Validation Rules

### Song Search Input
- **Pattern**: Alphanumeric + spaces only
- **Max length**: 100 characters
- **Special chars**: `%`, `_`, `\` escaped in SQL LIKE

### User Role Transitions
- **viewer** → **editor**: Requires admin approval
- **editor** → **admin**: Requires admin approval
- No downgrades allowed

---

## State Transitions

### Dashboard Stats State
```
idle → loading → loaded → error
                  ↓
            (retry on error)
```

### Timeline State
```
idle → loading_years → years_loaded → selecting_year
                                          ↓
                              loading_songs → songs_loaded
                                          ↓
                                    song_selected → modal_open
```

---

## Database Schema (SQLite)

```sql
-- New stats view (for dashboard)
CREATE VIEW v_song_stats AS
SELECT 
    (SELECT COUNT(*) FROM songs) AS total_songs,
    (SELECT COUNT(DISTINCT fonograma_id) FROM songs) AS total_albums,
    f.anio,
    COUNT(s.id) AS song_count
FROM fonogramas f
LEFT JOIN songs s ON s.fonograma_id = f.clave_fonograma
GROUP BY f.anio;

-- New indexes for timeline performance
CREATE INDEX idx_songs_fonograma_id ON songs(fonograma_id);
CREATE INDEX idx_fonogramas_anio ON fonogramas(anio);
CREATE INDEX idx_songs_clasificacion ON songs(clasificacion);
```

---

## API Contracts

### GET /api/stats

**Request**: No body

**Response** (200 OK):
```json
{
  "total_songs": 175,
  "total_albums": 14,
  "songs_by_year": {
    "2020": 23,
    "2021": 45,
    "2022": 67,
    "2023": 40
  },
  "songs_by_clasificacion": {
    "infantil": 120,
    "educativo": 55
  },
  "recently_added": 8
}
```

### POST /api/auth/login

**Request**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Response** (200 OK):
```json
{
  "token": "jwt-token-here",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

### POST /api/auth/register

**Request**:
```json
{
  "username": "string (3-50 chars, alphanumeric)",
  "email": "string (valid email)",
  "password": "string (min 8 chars)"
}
```

**Response** (201 Created):
```json
{
  "token": "jwt-token-here",
  "user": {
    "id": 1,
    "username": "newuser",
    "role": "viewer"
  }
}
```

### GET /api/songs/search?q={query}

**Request**: Query parameter `q`

**Response** (200 OK):
```json
{
  "songs": [
    {
      "id": 1,
      "title": "Canción del Sol",
      "fonograma": {
        "clave": "FONO001",
        "titulo": "Canciones Infantiles Vol. 1",
        "anio": 2020
      },
      "lyrics": "...",
      "clasificacion": "infantil"
    }
  ],
  "count": 1
}
```

---

## Security Models

### Rate Limiting

| Endpoint | Limit | Burst |
|----------|-------|-------|
| POST /api/auth/login | 5 req/min | 10 |
| POST /api/auth/register | 3 req/min | 5 |
| GET /api/* | 100 req/min | 200 |

### CORS Origins

From environment variable `CORS_ORIGINS`:
- Development: `http://localhost:3000`
- Production: specific domain(s)

---

## Relationships

```
User (1) ─────< (N) Song
  │               │
  │               │
  └─────> (FK) ──┘
              fonograma_id
              
Fonograma (1) ──< (N) Song
```
