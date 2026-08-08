# Cenidim Backend (FastAPI)

FastAPI / Pydantic v2 service for the Cenidim Web Application. It reads
the `letras.db` SQLite database produced by the data pipeline
(`scripts/build_db.py` → `scripts/classify_songs.py` →
`scripts/normalize_db.py`, orchestrated by `scripts/build_db.sh` and the
`db-init` Docker sidecar).

This is the **production backend** — the Go / Gin backend was retired in
Phase 9 of the cut-over (see `docs/adr/0001-fastapi-replaces-go.md` in
the repo root). There is no rollback service.

## Stack

- **FastAPI** (Pydantic v2, Python 3.12+) with async SQLAlchemy 2.0 ORM.
- **SQLite** via `aiosqlite`; schema managed with **Alembic** migrations.
- **Auth**: JWT (python-jose) with HttpOnly access cookie +
  `cenidim_refresh` (rotated, old `jti` revoked via
  `RefreshTokenRevocation`) + `cenidim_csrf` double-submit cookie.
  Passwords hashed with sha256+bcrypt (`app/security/`).
- **Email**: Resend provider; falls back to a dev **outbox** table when
  `RESEND_API_KEY` is empty (`app/services/email.py`).
- **Rate limiting**: slowapi (per-route limits on login/forgot).
- **Observability**: Prometheus `/metrics` (custom registry), structured
  JSON logging.
- **Deps**: `uv` (pyproject + uv.lock), `ruff` (lint + format), `mypy`
  (strict), `pytest` + coverage gate.

## Layout

```
app/
  config.py            # Settings (CENIDIM_* env vars, pydantic-settings)
  main.py              # app factory, CORS, CSRF seed, rate limiting, metrics
  db/                  # async engine + session
  models/              # SQLAlchemy ORM (fonograma, song, song_stats, user,
                       #   email_outbox, audit_log, refresh_revocation, …)
  routers/             # public.py, auth.py, admin.py
  schemas/             # Pydantic request/response models
  security/            # JWT, CSRF, password hashing
  services/            # auth.py, email.py, filters.py (shared search filters)
alembic/               # migration scripts + alembic.ini
scripts/               # entrypoint.sh, smoke.sh, generate_openapi.py, …
tests/                 # api / unit / integration / security / smoke + factories
openapi.json           # generated spec (CI guards drift)
```

## Local development

Requires Python 3.12+ and [`uv`](https://docs.astral.sh/uv/).

```bash
cd backend-fastapi
uv sync                        # install + lock
PYTHONPATH=. uv run uvicorn app.main:app --port 8000 --reload
```

The app reads `letras.db` (default) or `CENIDIM_DB_PATH`. In dev it
auto-creates the schema on an empty DB; in production Alembic migrations
run on boot (see `scripts/entrypoint.sh`).

### Quality gates

```bash
PYTHONPATH=. uv run pytest tests/      # 235 tests, ~96% coverage (gate 80%)
uv run ruff check app/ tests/          # lint
uv run ruff format --check app/        # format
uv run mypy app/                       # strict type checking
uv run python scripts/generate_openapi.py   # refresh openapi.json
uv run alembic upgrade head            # apply migrations
./scripts/smoke.sh http://localhost:8000    # post-boot health check
```

## Environment variables

All settings are `CENIDIM_`-prefixed (see `app/config.py` for the full
list and defaults). Key ones:

| Variable | Default | Purpose |
|----------|---------|---------|
| `CENIDIM_DB_PATH` | `letras.db` | SQLite file path |
| `CENIDIM_JWT_SECRET` | dev fallback | JWT signing key; **required** in prod |
| `CENIDIM_ENV` | `dev` | `prod` disables `/docs` and the dev auto-schema |
| `CENIDIM_WORKERS` | `2` | uvicorn worker count |
| `CENIDIM_LOG_FORMAT` | `json` | `json` (prod) or `text` |
| `CENIDIM_EMAIL_FROM` | `no-reply@cenidim.local` | Sender for reset emails |
| `CENIDIM_FRONTEND_BASE_URL` | `http://localhost:3000` | SPA origin for email links |
| `RESEND_API_KEY` | empty | Resend key; empty → dev `email_outbox` |
| `CENIDIM_EMAIL_DEMO_PRINT_BODY` | `0` | Dev: echo reset link in `/forgot` response |
| `CORS_ALLOWED_ORIGINS` | local trio + Hoppscotch | comma-separated allow-list |

## API surface

- **Public**: `/healthz`, `/metrics`, `/openapi.json`, `/api/search`,
  `/api/song/{id}`, `/api/timeline`, `/api/stats`, `/api/word-cloud`
  (see `app/routers/public.py`).
- **Auth**: `/api/auth/login|register|forgot|reset|refresh|logout|me`
  (see `app/routers/auth.py`).
- **Admin** (`/api/admin/*`, role-gated): fonogramas CRUD, songs CRUD
  (with `has_lyrics` / `sort` / `dir` params), users CRUD, `/emails`,
  `/audit` (see `app/routers/admin.py`).

The authoritative spec is `openapi.json`. The `docs/PARITY.md` table is
the contract between the Vue frontend and this service — every
`apiService.<x>` call has a row.

## Docker

`Dockerfile` is multi-stage (uv-managed deps, non-root `app` user).
`scripts/entrypoint.sh` fixes volume permissions, runs
`alembic upgrade head`, then starts uvicorn as the non-root user. The
database itself is produced by the `db-init` sidecar
(`docker/db-init.Dockerfile`) and mounted into `/data`.
