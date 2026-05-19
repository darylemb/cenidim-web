# AGENTS.md

## Project Structure
- `backend/` — Go API (Gin + SQLite). Entry point: `main.go`.
- `frontend/` — Vue 3 app (Vite + TypeScript). Entry point: `frontend/src/`.
- `scripts/build_db.sh` — Builds `letras.db` from CSV + lyrics. Must run before `docker compose up`.
- `scripts/classify_songs.py` — Classifies songs in DB using spaCy (`es_core_news_md`). Runs **after** the Go builder inside `build_db.sh`.

## Database Build
```bash
./scripts/build_db.sh
```
Requires: Go (for `cmd/build-db/main.go`) and Python with spaCy (`es_core_news_md` model).
Sets `ADMIN_PASS` env var to create initial admin user.
The two-step process: (1) Go builds SQLite from `db_fonografia.csv` + `LetrasTXT/`, (2) Python/spaCy classifies each song + writes `song_stats` table.

## Backend (Go)
```bash
cd backend
go run main.go          # Dev server on :8080
go test ./...           # Tests (unit + integration)
golangci-lint run       # Lint (config in .golangci.yml)
```
- Swaggo for Swagger. After modifying `main.go` or handler comments: `cd backend && go install github.com/swaggo/swag/cmd/swag@v1.16.6 && swag init -g main.go`
- CORS origins via `CORS_ALLOWED_ORIGINS` env var (defaults to `http://localhost,http://localhost:3000,http://localhost:8000`)
- Auth: JWT-based. Admin routes at `/api/admin/*` require role middleware (`viewer`, `editor`, `admin`).

## Frontend (Vue 3 + TypeScript)
```bash
cd frontend
npm install              # Install dependencies
npm run dev             # Dev server on :5173 (Vite)
npm run build           # TypeScript check + Vite build
npm run typecheck       # vue-tsc --noEmit only
npm run lint            # ESLint
npm run lint:fix        # ESLint --fix
npm run test            # Vitest watch mode
npm run test -- --run   # Tests once (CI)
npm run test:coverage   # Coverage report
```
- **Node 24** required
- Build tool: **Vite** (replaces react-scripts)
- Charts: **vue-chartjs** (Chart.js wrapper)
- State: **Pinia** stores (`src/stores/`: auth, search, ui)
- Routing: **Vue Router 4** (routes in `src/router/`)
- TypeScript **strict mode**
- Tests: **Vitest + Vue Test Utils**
- CSS: global `src/assets/main.css` + `<style scoped>` per component

## Validación Local (Simula CI)
```bash
./scripts/run_ci_local.sh
```
Secuencia: backend lint+test → frontend lint+typecheck+test → Docker build+health

## CI (GitHub Actions)
- **Frontend**: `npm ci` → `npm run lint` → `npm run build` (includes typecheck) → `npm run test -- --run`
- **Backend**: `go mod download` → `golangci-lint run` → `go test -v ./...`
- **Docker**: `docker compose build` → `docker compose up -d` → `curl localhost:8000/health` → `docker compose down`

## Docker
- Multi-stage build: Go builder → spaCy classifier → distroless final image
- `docker compose up --build -d` builds everything including DB initialization
- Frontend served via nginx-unprivileged on port 80
- Backend healthcheck binary compiled separately (distroless has no curl)
- spaCy model changed from `es_core_news_sm` to `es_core_news_md`

## Pre-commit Hooks
- Ruff (lint + format) for Python files
- Mypy for Python type checking (requires `pydantic`, `fastapi`, `uvicorn` as extra deps)
- Standard hooks: trailing whitespace, end-of-file fixer, YAML check, large-file check

<!-- SPECKIT START -->
## Current Plan
`specs/001-fix-execution/plan.md`

For additional context about the fix execution feature, read:
- `specs/001-fix-execution/research.md`
- `specs/001-fix-execution/quickstart.md`
<!-- SPECKIT END -->
