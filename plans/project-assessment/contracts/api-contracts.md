# API Contracts: Project Assessment Implementation

**Date**: 2026-05-10  
**Context**: New `/api/stats` endpoint and existing API contracts for reference

---

## 1. New Stats Endpoint

### GET /api/stats

Returns dashboard statistics for the frontend.

**Authentication**: Not required. Optional bearer tokens may be sent by authenticated clients.

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

**Error Responses**:
- `500 Internal Server Error`: Database error

---

## 2. Existing API Contracts (for reference)

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
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

**Error Responses**:
- `400 Bad Request`: Invalid request body
- `401 Unauthorized`: Invalid credentials

---

### POST /api/auth/register

**Request**:
```json
{
  "username": "string (3-50 chars, alphanumeric and underscore)",
  "email": "string (valid email format)",
  "password": "string (minimum 8 characters)"
}
```

**Response** (201 Created):
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 2,
    "username": "newuser",
    "role": "viewer"
  }
}
```

**Error Responses**:
- `400 Bad Request`: Validation failed (username taken, invalid email, weak password)
- `429 Too Many Requests`: Rate limit exceeded

---

### GET /api/auth/me

**Authentication**: Required (JWT Bearer token)

**Response** (200 OK):
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@cenidim.mx",
  "role": "admin",
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### GET /api/songs

**Authentication**: Optional

**Query Parameters**:
- `page` (int, default: 1): Page number
- `limit` (int, default: 20, max: 100): Items per page

**Response** (200 OK):
```json
{
  "songs": [
    {
      "id": 1,
      "title": "Canción del Sol",
      "album": "Canciones Infantiles Vol. 1",
      "year": "2020",
      "clasificacion": "infantil",
      "interprete_principal": "Coro de Niños"
    }
  ],
  "total": 175,
  "page": 1,
  "limit": 20
}
```

---

### GET /api/songs/search?q={query}

**Authentication**: Optional

**Query Parameters**:
- `q` (string, required): Search query (max 100 chars, alphanumeric + spaces)

**Response** (200 OK):
```json
{
  "songs": [
    {
      "id": 1,
      "title": "Canción del Sol",
      "album": "Canciones Infantiles Vol. 1",
      "year": "2020",
      "clasificacion": "infantil"
    }
  ],
  "count": 1
}
```

**Error Responses**:
- `400 Bad Request`: Query too long or contains invalid characters

---

### GET /api/songs/:id

**Authentication**: Optional

**Response** (200 OK):
```json
{
  "id": 1,
  "title": "Canción del Sol",
  "filename": "cancion_del_sol.txt",
  "album": "Canciones Infantiles Vol. 1",
  "year": "2020",
  "clasificacion": "infantil",
  "lyrics": "Letra de la canción...",
  "interprete_principal": "Coro de Niños"
}
```

**Error Responses**:
- `404 Not Found`: Song does not exist

---

### GET /api/timeline/years

**Authentication**: Optional

Returns list of years with song counts for timeline.

**Response** (200 OK):
```json
{
  "years": [
    {"year": "2023", "count": 40},
    {"year": "2022", "count": 67},
    {"year": "2021", "count": 45},
    {"year": "2020", "count": 23}
  ]
}
```

---

### GET /api/timeline/years/:year/songs

**Authentication**: Optional

**Path Parameters**:
- `year` (string): Year (e.g., "2023")

**Query Parameters**:
- `page` (int, default: 1): Page number
- `limit` (int, default: 20): Items per page

**Response** (200 OK):
```json
{
  "songs": [
    {
      "id": 1,
      "title": "Canción del Sol",
      "album": "Canciones Infantiles Vol. 1",
      "clasificacion": "infantil"
    }
  ],
  "total": 40,
  "page": 1,
  "limit": 20
}
```

---

## 3. Admin API Contracts

### GET /api/admin/users

**Authentication**: Required (admin role only)

**Response** (200 OK):
```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@cenidim.mx",
      "role": "admin",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

### POST /api/admin/users

**Authentication**: Required (admin role only)

**Request**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "role": "viewer | editor | admin"
}
```

**Response** (201 Created):
```json
{
  "id": 2,
  "username": "newuser",
  "email": "newuser@cenidim.mx",
  "role": "viewer",
  "created_at": "2026-05-10T23:00:00Z"
}
```

---

## 4. Authentication Contract

All authenticated endpoints require:

**Header**: `Authorization: Bearer <token>`

**Error Responses**:
- `401 Unauthorized`: Missing, invalid, or expired token
- `403 Forbidden`: Insufficient role permissions

---

## 5. Rate Limiting Contract

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /api/auth/login | 5 requests | per minute |
| POST /api/auth/register | 3 requests | per minute |
| All other endpoints | 100 requests | per minute |

**Rate Limit Response Headers**:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining in window
- `X-RateLimit-Reset`: Unix timestamp when window resets

**Rate Limit Exceeded Response** (429 Too Many Requests):
```json
{
  "error": "Too many requests",
  "retry_after": 60
}
```

---

## 6. Error Response Contract

All endpoints return errors in this format:

```json
{
  "error": "Error message description",
  "code": "ERROR_CODE",
  "details": {} // Optional additional context
}
```

**Error Codes**:
- `VALIDATION_ERROR`: Request validation failed
- `AUTHENTICATION_ERROR`: Authentication failed
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error
