# Cenidim Web Application

This repository contains the full stack web application for **Cenidim** (Centro Nacional de Investigación, Documentación e Información Musical "Carlos Chávez").

The application serves a digital archive of musical lyrics — the CENIDIM children's songbook collection — and lets researchers search by title, album, or lyric content, browse statistical dashboards, and (for admins) manage the catalog and user accounts. The frontend follows a single design-token reference (Fraunces + Outfit + JetBrains Mono on a vino/mostaza/crema palette) so every page is visually consistent.

**Glossary & terminology**: see [`docs/GLOSARIO.md`](docs/GLOSARIO.md) for the canonical definitions of every chart, KPI, and category shown on the dashboard. The frontend's `ⓘ` info buttons on each chart source their long-form text from `frontend/src/config/chartInfo.ts`.

## Architecture

1. **Backend (FastAPI – Pydantic v2)**: the production backend since Phase 7 of the Go → FastAPI cut-over. SQLAlchemy 2.0 ORM, JWT auth with HttpOnly cookies + CSRF double-submit, refresh-token rotation via `RefreshTokenRevocation`, Prometheus `/metrics`, structured JSON logging, Alembic migrations. See `backend-fastapi/` and `docs/adr/0001-fastapi-replaces-go.md`. The Go / Gin backend was **retired in Phase 9** (the `backend/` tree and rollback compose are gone).
2. **Frontend (Vue 3 + TypeScript)**: SPA served via an **unprivileged Nginx** container. State is managed with Pinia; routing with Vue Router; charts with vue-chartjs. Build tool is Vite. Requires **Node 24**.
3. **Data management**: a three-step Python pipeline that parses the raw songbook and lyrics into a structured SQLite database.
   - `scripts/build_db.py` seeds `letras.db` from `db_fonografia.csv` + `LetrasTXT/` (Python port of the old Go builder, byte-compatible) inside the `db-init` Docker sidecar.
   - `scripts/classify_songs.py` uses **spaCy** (`es_core_news_md`) to compute OOV percentages and classify each song as `ESPAÑOL_ESTANDAR` / `ESPAÑOL_REGIONAL` / `LENGUA_INDIGENA`.
   - `scripts/normalize_db.py` cleans lyrics, normalizes themes, and re-validates the lyric↔title match.
4. **Themes**: the `Tema: ...` line at the end of each `LetrasTXT/*.txt` file is the single source of truth — themes are written by the human cataloguers, **not** inferred by keyword matching. The backend folds case / whitespace variants and curated typos into canonical buckets via `canonical_tema` (`backend-fastapi/app/models/theme_normalization.py`, mirrored by the API's `_tema_filter_variants`). The UI cycles a curated palette of swatches by hashing the theme key (`frontend/src/config/themes.ts`), so any new theme gets a colour automatically and nothing crashes on an unknown value.

## Setup Instructions

### 1. Database initialization

Before running the application, build the database from the raw metadata + lyrics:

```bash
./scripts/build_db.sh
```

This requires Python with `bcrypt` and spaCy + `es_core_news_md` (for `scripts/classify_songs.py`). The three steps run sequentially: `build_db.py` creates `letras.db` from the CSV + lyrics, Python/spaCy classifies every song and writes the `song_stats` table, then `normalize_db.py` cleans lyrics, normalizes themes and re-validates the lyric↔title match. The script also sets the `ADMIN_PASS` env var to seed the initial admin user.

When using the **Docker Compose** stack (recommended), the `db-init` sidecar service regenerates the DB from the current source tree on every `docker compose up`. You don't need to run `build_db.sh` manually in that case.

### 2. Environment configuration

The FastAPI service reads configuration from environment variables prefixed with `CENIDIM_` (plus `CORS_ALLOWED_ORIGINS` and a few un-prefixed aliases). The compose files set sane dev defaults; for production override at the Coolify secret store.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CENIDIM_JWT_SECRET` | **Yes** | dev-only fallback | Secret key for signing JWTs. The backend refuses to boot in production without this. Use at least 256 bits of entropy (`openssl rand -hex 32`). |
| `CENIDIM_DB_PATH` | No | `letras.db` | Path to the SQLite database file. |
| `CENIDIM_ENV` | No | `dev` | `dev` enables the auto-create-schema fallback. Production must be `prod` and run Alembic migrations explicitly. |
| `CENIDIM_LOG_FORMAT` | No | `json` | `json` for production (Promtail / Grafana friendly) or `text` for human-readable. |
| `CENIDIM_WORKERS` | No | `2` | uvicorn worker count (production). |
| `CENIDIM_EMAIL_FROM` | For Resend | `no-reply@cenidim.local` | Sender for outbound password-reset emails. |
| `CORS_ALLOWED_ORIGINS` | No | `http://localhost,http://localhost:3000,http://localhost:8000` | Comma-separated list of allowed CORS origins. |
| `FRONTEND_BASE_URL` / `CENIDIM_FRONTEND_BASE_URL` | For email links | `http://localhost` | SPA origin used to build the redirect target in password-reset emails. |
| `RESEND_API_KEY` | For outbound email | empty (dev outbox) | Resend API key; when empty, `email_outbox` table receives every send instead. |

Operators set the env vars via their platform's secret store (Coolify,
Kubernetes, etc.). The `.gitignore` already excludes any local `.env`.

### 3. Running with Docker (Recommended)

```bash
docker compose up --build -d
```

- **Frontend**: `http://localhost` (served via unprivileged Nginx).
- **Backend API**: `http://localhost:8000/healthz` (FastAPI / uvicorn on port 8000).
- **Metrics**: `http://localhost:8000/metrics` (Prometheus text format).
- **OpenAPI**: `http://localhost:8000/openapi.json` (auto-generated).

`db-init` is a single Python+spaCy stage (`docker/db-init.Dockerfile`) that
seeds `letras.db` from `LetrasTXT/` + `db_fonografia.csv` (build → classify →
normalize). The backend waits for it via `depends_on.condition:
service_completed_successfully`. The FastAPI service then applies any pending
Alembic migrations against the freshly-produced DB on first boot.

`backend-fastapi/Dockerfile` is multi-stage: it installs Python deps via `uv`
(no `pip install` wheel-build headaches) and runs the API as a non-root user
on `0.0.0.0:8000`.

`frontend/Dockerfile` uses `nginx-unprivileged:alpine` (no root, port 80).

### 4. Local development (no Docker)

**Backend (FastAPI):**
```bash
cd backend-fastapi
uv sync
PYTHONPATH=. uv run pytest tests/    # 235 tests, 96% coverage
PYTHONPATH=. uv run uvicorn app.main:app --port 8000 --reload
```

**Frontend (Vue 3 + Vite, Node 24):**
```bash
cd frontend
npm install
npm run dev   # Vite dev server on :5173, proxies /api to the backend
```

Other useful frontend scripts:
```bash
npm run typecheck   # vue-tsc --noEmit
npm run lint        # ESLint
npm run test        # Vitest watch mode
npm run test -- --run   # one-shot (CI)
npm run test:coverage    # coverage report
npm run build      # typecheck + Vite production build
```

Backend scripts:
```bash
./scripts/build_db.sh         # regenerates letras.db from CSV + lyrics (used in db-init container too)
backend-fastapi/scripts/smoke.sh http://localhost:8000   # post-boot health check
backend-fastapi/scripts/generate_openapi.py              # refresh openapi.json
(cd backend-fastapi && uv run alembic upgrade head)      # apply migrations
```

## Authentication

The login flow is username + password only. Google OAuth was removed in
the Go → FastAPI cut-over: there are no `/api/auth/google/*` endpoints,
no `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URL`
env vars, and the login page renders only the password form.

- `POST /api/auth/register` — open self-registration (if enabled).
- `POST /api/auth/forgot` / `POST /api/auth/reset` — password recovery via Resend (or the dev `email_outbox` table).
- `POST /api/auth/login` — sets `cenidim_session` (HttpOnly access JWT) + `cenidim_refresh` + `cenidim_csrf` cookies.
- `POST /api/auth/refresh` / `POST /api/auth/logout` — rotate/revoke the refresh token.
- `GET /api/auth/me` — current user profile (requires JWT).

Roles: `viewer` (read) < `editor` (write) < `admin` (delete + user management). Password-reset emails are sent via Resend when `RESEND_API_KEY` is set; otherwise they land in the `email_outbox` table for dev.

## Testing and Quality

- **Backend (FastAPI)**: `cd backend-fastapi && PYTHONPATH=. uv run pytest tests/`. **235 tests pass at 96% coverage** with ruff clean. Coverage gate: 95% (`--cov-fail-under=95` in `pyproject.toml`).
- **Frontend**: `cd frontend && npm run test -- --run` (Vitest + Vue Test Utils). **265 tests pass** (9 skipped). Strict TypeScript — `npm run typecheck` runs in CI.
- **End-to-end backend smoke**: `cd backend-fastapi && PYTHONPATH=. uv run pytest tests/integration/test_uvicorn_smoke.py`. Boots a real uvicorn subprocess and exercises /healthz, /metrics, /openapi.json, /api/auth/register, /api/auth/login, /api/auth/me, /api/auth/logout, /api/search, /api/stats, /api/admin/* 401, and the 422 validation path.
- **Post-deploy smoke script**: `backend-fastapi/scripts/smoke.sh http://localhost:8000`. Returns non-zero on the first failing check; intended to run after every `docker compose up`.
- **Design tokens**: `bash scripts/audit_design_tokens.sh frontend/src 0.05` verifies that no more than 5 % of style-bearing lines use hard-coded hex colors or px values outside `tokens.css`. SC-009 of the spec requires this drift to stay below 2 % at the end of the project.
- **End-to-end CI**: `scripts/run_ci_local.sh` runs the full sequence (backend lint + test → frontend lint + typecheck + test → docker compose build + health check).
- **Code review**: `scripts/run_code_review_all.sh` is the pre-merge gate (FR-027 of spec 004 / SC-010). It batches all source files and invokes the `/code-review` command on each batch. **This is opt-in**: the agent never runs it automatically. To run it before opening a PR:
  ```bash
  ./scripts/run_code_review_all.sh
  # review-reports/code-review-<timestamp>/summary.md will list OK / failed / skipped batches
  ```

## API Endpoints

The full FastAPI surface is documented as an OpenAPI 3.1 spec at `backend-fastapi/openapi.json` (regenerable via `backend-fastapi/scripts/generate_openapi.py`; CI guards drift). The condensed list:

### Public
- `GET /healthz` — health check (used by the Docker healthcheck)
- `GET /metrics` — Prometheus metrics (text format 0.0.4)
- `GET /openapi.json` — OpenAPI 3.1 spec
- `GET /api/search` — paginated song search; accepts `?query=` (Vue convention) or `?q=`
- `GET /api/song/{song_id}` — song details + lyrics
- `GET /api/timeline` — songs grouped by year
- `GET /api/stats` — aggregate dashboard metrics; honors the shared filter query parameters (`tema`, `year_from`, `year_to`, `clasificacion`, `album`, `q`)
- `GET /api/word-cloud` — word frequencies for the dashboard's word cloud

### Authentication (`/api/auth/*`)
- `POST /api/auth/login` — password sign-in; sets `cenidim_session` (HttpOnly access JWT) + `cenidim_refresh` + `cenidim_csrf` cookies, returns `{token, user}` in the body so the SPA can mirror to localStorage.
- `POST /api/auth/register` — open self-registration (if enabled).
- `POST /api/auth/forgot` — always 200; sends a one-shot reset link via Resend (or writes to `email_outbox` in dev).
- `POST /api/auth/reset` — consume a reset token + new password.
- `POST /api/auth/refresh` — rotate the refresh token (old `jti` is revoked).
- `POST /api/auth/logout` — revoke the current refresh token + clear cookies.
- `GET /api/auth/me` — current user profile (requires JWT).

### Admin (`/api/admin/*`, requires JWT + role)
- Fonogramas CRUD: `GET /fonogramas`, `POST /fonogramas`, `GET /fonogramas/{id}`, `PUT /fonogramas/{id}`, `DELETE /fonogramas/{id}`
- Songs CRUD: `GET /songs`, `POST /songs`, `PUT /songs/{id}`, `DELETE /songs/{id}`
- Users CRUD: `GET /users`, `POST /users`, `PUT /users/{id}`, `DELETE /users/{id}`
- Operational: `GET /emails` (email outbox), `GET /audit` (audit log)

Role hierarchy: `viewer` (read) < `editor` (write) < `admin` (delete + user management).

The `docs/PARITY.md` table inside `backend-fastapi/` is the contract between the Vue dashboard and the FastAPI service — every `apiService.<x>` call has a row.

## Deployment

The repo ships two compose files:

- **`docker-compose.yaml`** — **default**. Boots the FastAPI backend, the spaCy-seeded `letras.db`, and the frontend. Use for local dev **and** production (Coolify reads this file).
- **`docker-compose-coolify.yaml`** — Coolify production shape: named volume, secret placeholders, internal bridge network. Used by the `coolify` deployment target; defaults to FastAPI but pins the env vars Coolify needs.

The Go rollback compose (`docker-compose-go.yaml`) and the Phase 1
overlay (`docker-compose-fastapi.yaml`) were removed in Phase 9.

When changing the backend env vars, only the `environment:` block of the `backend` service needs to change in whichever compose file you target.

## License

See `LICENSE` (not included in this README; check the repository root).
# retrigger ci
<!-- CI: Tue Jul 14 22:23:24 CST 2026 -->
