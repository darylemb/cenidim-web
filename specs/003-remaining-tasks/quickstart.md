# Quickstart: Dashboard Improvements and Docker Security

## Prerequisites

- Go 1.21+
- Node.js 24+
- Docker & Docker Compose
- Trivy (for security scanning)
- Python 3 with spaCy (`es_core_news_md` model)

## Local Development Setup

### 1. Database Build

```bash
./scripts/build_db.sh
```

This runs:
1. `go run cmd/build-db/main.go` - Builds SQLite from CSV + lyrics
2. `python3 scripts/classify_songs.py` - Classifies songs with spaCy

### 2. Backend Development

```bash
cd backend
go run main.go
# API available at http://localhost:8080
# Health check: http://localhost:8080/health
```

### 3. Frontend Development

```bash
cd frontend
npm install
npm run dev
# App available at http://localhost:5173
```

## Testing

### Backend Tests

```bash
cd backend
go test ./...
```

### Frontend Tests

```bash
cd frontend
npm test -- --run        # Unit tests (Vitest)
npm run test:e2e         # E2E tests (Playwright)
npm run lint             # Linting
npm run build            # TypeScript check + build
```

### Docker Health Check

```bash
docker compose up --build -d
curl http://localhost:8000/health
```

## Key API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stats` | GET | Dashboard statistics |
| `/api/word-cloud` | GET | Word frequency data |
| `/health` | GET | Backend health check |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | - | Required for authentication |
| `CORS_ALLOWED_ORIGINS` | `http://localhost,http://localhost:3000,http://localhost:8000` | CORS origins |
| `GIN_MODE` | `debug` | Gin mode (debug/release) |

## Docker Security Scanning (Trivy)

Trivy scans run automatically in CI after Docker image builds. To run manually:

```bash
# Scan local Docker image
trivy image --severity HIGH,CRITICAL --exit-code 1 cenidim-backend:latest

# Scan and save report
trivy image --format sarif --output trivy-report.sarif cenidim-backend:latest

# Scan filesystem (for docker-compose)
trivy config --severity HIGH,CRITICAL .
```

## Database Queries for Verification

```sql
-- Total songs
SELECT COUNT(*) FROM songs;

-- Total albums
SELECT COUNT(*) FROM fonogramas;

-- Songs by year (excluding s/d)
SELECT f.anio, COUNT(*) as count
FROM songs s
JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma
WHERE f.anio IS NOT NULL AND f.anio != '' AND f.anio != 's/d'
GROUP BY f.anio
ORDER BY f.anio;

-- Songs with s/d year
SELECT COUNT(*) FROM songs s
JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma
WHERE f.anio = 's/d' OR f.anio IS NULL OR f.anio = '';

-- Average lyrics length
SELECT AVG(LENGTH(lyrics)) FROM songs WHERE lyrics IS NOT NULL AND lyrics != '';

-- Songs with lyrics
SELECT COUNT(*) FROM songs WHERE lyrics IS NOT NULL AND lyrics != '';
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Word cloud shows empty | Check that `lyrics` column is used (not `letra`) in stats.go |
| KPI shows "0" | Backend missing fields - check StatsResponse struct |
| Trivy scan fails | Check Trivy is installed in CI environment |
| s/d still appears in timeline | Verify backend query filters `f.anio != 's/d'` |