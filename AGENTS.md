# AGENTS.md

## Project Structure
- `backend/` — Go API (Gin + SQLite). Entry point: `main.go`. **Live** through Phase 6.
- `backend-fastapi/` — FastAPI/Pydantic v2 cut-over (Phase 1 scaffold, **live on `feature/fastapi-backend`**). Reads the same `letras.db` schema.
- `frontend/` — Vue 3 app (Vite + TypeScript). Entry point: `frontend/src/`.
- `scripts/build_db.sh` — Builds `letras.db` from CSV + lyrics. Must run before `docker compose up`.
- `scripts/classify_songs.py` — Classifies songs in DB using spaCy (`es_core_news_md`). Runs **after** the Go builder inside `build_db.sh`.

## Active Branches
- `fix/phase-0-admin-google-recovery-tests` (commit `2aab765`) — admin edits, password recovery, demote Google from login. Lives on `main`. Frontend coverage 95.4%.
- `feature/fastapi-backend` — Phase 1+2 of the Go→FastAPI cut-over (commit `2a19551`+). 97 tests passing at 92% coverage, ruff clean, 90% gate. **All work happens here**; `backend/` stays untouched until Phase 7.
- `fix/critical-bugs-dashboard-and-oauth` — Go-era backup branch (do not delete; rollback target per user instruction).
- `ux/dashboard-fixes-2026-07` — reviewer-feedback branch.

## Backend (FastAPI — work in progress)
```bash
cd backend-fastapi
uv sync                              # one-time install + lock
PYTHONPATH=. uv run pytest tests/    # 97 tests, 92% coverage (90% gate)
uv run ruff check app/ tests/        # lint (clean)
uv run mypy app/                     # type check (strict, ignore_missing_imports)
uv run uvicorn app.main:app --port 8000 --reload
```
- Read the same `letras.db` SQLite schema as the Go backend
  (snake_case column names; SQLAlchemy ORM models under
  `app/models/`).
- Auth: `app/services/auth.py` (password hashing via sha256+bcrypt,
  JWT issue/verify via python-jose, refresh-token rotation via
  `RefreshTokenRevocation` table).
- Admin: `app/routers/admin.py` mirrors `backend/handlers/admin.go`;
  viewer/editor/admin tiers backed by `require_role("...")` factory
  in `app/deps.py`.
- Google OAuth: `app/routers/google_oauth.py` with a
  `StubIDTokenVerifier` test seam; production verifier in
  `app/services/google_oauth.py` (google-auth, lazy import).
- Resend + dev outbox: `app/services/email.py`.
- Test conftest (`tests/conftest.py`) shares a single StaticPool
  in-memory engine between the FastAPI app and direct ORM seed
  helpers (`make_user`, `make_admin`, `make_identity`,
  `make_email_outbox`).
- Coverage gate is `90%` (Phase 2); master plan still calls for
  `95%` by Phase 7 (post-cutover). Phase 2 replaced the public
  router's raw-SQL paths with ORM (`/api/search`, `/api/song/{id}`,
  `/api/timeline`, `/api/stats`, `/api/word-cloud`); the remaining
  ~8% lives in the production google-oauth verifier (lazy import)
  and a few error branches in services.

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
`specs/004-interactive-themes-oauth/plan.md`

For additional context about the dashboard improvements and Trivy scanning, read:
- `specs/004-interactive-themes-oauth/research.md`
- `specs/004-interactive-themes-oauth/quickstart.md`
- `specs/004-interactive-themes-oauth/data-model.md`
- `specs/004-interactive-themes-oauth/spec.md`
- `specs/004-interactive-themes-oauth/tasks.md` (generated by `/speckit.tasks`)
<!-- SPECKIT END -->
