# Cenidim Web Application

This repository contains the full stack web application for **Cenidim** (Centro Nacional de Investigación, Documentación e Información Musical "Carlos Chávez").

The application serves a digital archive of musical lyrics — the CENIDIM children's songbook collection — and lets researchers search by title, album, or lyric content, browse statistical dashboards, and (for admins) manage the catalog and user accounts. The frontend follows a single design-token reference (Fraunces + Outfit + JetBrains Mono on a vino/mostaza/crema palette) so every page is visually consistent.

**Glossary & terminology**: see [`docs/GLOSARIO.md`](docs/GLOSARIO.md) for the canonical definitions of every chart, KPI, and category shown on the dashboard. The frontend's `ⓘ` info buttons on each chart source their long-form text from `frontend/src/config/chartInfo.ts`.

## Architecture

1. **Backend (FastAPI – Pydantic v2)**: the production backend since Phase 7 of the Go → FastAPI cut-over. SQLAlchemy 2.0 ORM, JWT auth with HttpOnly cookies + CSRF double-submit, refresh-token rotation via `RefreshTokenRevocation`, Prometheus `/metrics`, structured JSON logging, Alembic migrations. See `backend-fastapi/` and `docs/adr/0001-fastapi-replaces-go.md`. The Go / Gin backend was **retired in Phase 9** (the `backend/` tree and rollback compose are gone).
2. **Frontend (Vue 3 + TypeScript)**: SPA served via an **unprivileged Nginx** container. State is managed with Pinia; routing with Vue Router; charts with vue-chartjs. Build tool is Vite. Requires **Node 24**.
3. **Data management**: a three-step Python pipeline that parses the raw songbook and lyrics into a structured SQLite database.
   - `scripts/build_db.py` seeds `letras.db` from `db_fonografia.csv` + `LetrasTXT/` (Python port of the old Go builder, byte-compatible) inside the `db-init` Docker sidecar.
   - `scripts/classify_songs.py` uses **spaCy** (`es_core_news_md`) to compute OOV percentages, classify each song as `ESPAÑOL_ESTANDAR` / `ESPAÑOL_REGIONAL` / `LENGUA_INDIGENA`, and assign a canonical **theme** (see below).
   - `scripts/normalize_db.py` cleans lyrics, normalizes themes, and re-validates the lyric↔title match.
4. **Canonical themes**: the classifier reduces the free-text `Tema: ...` lines at the end of each `LetrasTXT/*.txt` file into one of these categories:

   | Theme         | What it covers                                                  |
   |---------------|----------------------------------------------------------------|
   | `Amor`        | Love, romance, affection, heartbreak-as-absence-of-love        |
   | `Despecho`    | Betrayal, abandonment, heartbreak, "adiós"                      |
   | `Fiesta`      | Dancing, celebrations, carnival, "jarana"                       |
   | `Navidad`     | Christmas, Reyes, "nochebuena", "villancico"                    |
   | `Animales`    | Named animals (perro, gato, caballo, etc.)                      |
   | `Naturaleza`  | Sol, luna, mar, río, árbol, lluvia, etc.                       |
   | `Religión`    | Dios, virgen, iglesia, oración, "alma"                          |
   | `Patria`      | Patria, México, independencia, soldado, "honor"                |
   | `Drogas`      | Droga, marijuana, "cocaína"                                    |
   | `Política`    | Presidente, gobierno, congreso, ley                            |
   | `General`     | Default fallback when no theme keyword matches                 |

   The same list is the **single source of truth** across the codebase: see `scripts/classify_songs.py` TEMA_KEYWORDS, `frontend/src/config/themes.ts`, the `KNOWN_THEMES` array in `DashboardFilters.vue`, the `CANONICAL_THEMES` exported from `ThemeBadge.vue`, the `--theme-color-*` tokens in `frontend/src/assets/tokens.css`, and the chart palette in `DashboardView.vue`. **Keep all five in sync** if a new theme is added.

## Setup Instructions

### 1. Database initialization

Before running the application, build the database from the raw metadata + lyrics:

```bash
./scripts/build_db.sh
```

This requires Go (for `cmd/build-db/main.go`) and Python with spaCy + `es_core_news_md` (for `scripts/classify_songs.py`). The two steps run sequentially: the Go builder creates `letras.db` from the CSV + lyrics, then Python classifies every song and writes the `song_stats` table. The script also sets the `ADMIN_PASS` env var to seed the initial admin user.

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
| `GOOGLE_CLIENT_ID` | For Google sign-in (admin-only after Phase 7) | none | OAuth 2.0 client ID from the Google Cloud console. |
| `GOOGLE_CLIENT_SECRET` | For Google sign-in | none | OAuth 2.0 client secret paired with `GOOGLE_CLIENT_ID`. |
| `GOOGLE_REDIRECT_URL` | For Google sign-in | none | The exact callback URL registered in the Google Cloud console. Local Docker: `http://localhost:8000/api/auth/google/callback`. Production: `https://<your-domain>/api/auth/google/callback`. |
| `FRONTEND_BASE_URL` | For Google sign-in | `http://localhost:3000` | The SPA origin used to build the post-callback redirect target. |
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
PYTHONPATH=. uv run pytest tests/    # 229 tests, 96% coverage
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

## Google sign-in

> **Phase 7+**: the login page **hides** the "Continuar con Google" button. The Vue dashboard's AuthPage no longer renders it, so end users see only the username + password flow. The Google OAuth endpoints (`/api/auth/google/*`) are still fully wired for the admin path: an operator with `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` / `GOOGLE_REDIRECT_URL` set can still link / unlink identities via the admin dashboard's **Usuarios** tab → **Identidades** column.

### Who is authorized?

The backend has two modes of access for Google sign-in. Pick the one that matches your security posture; the only thing that changes is **how you seed the `users` table** before the first Google sign-in.

#### Mode A — Open registration (default)

Any person with a verified Google email can sign in. The first time an email is seen, the backend creates a new `viewer` account with that email and a randomized `username` (e.g. `viewer_a3f9c1`). Subsequent visits reuse the same account.

**Best for**: internal demos, pilot deployments, or any environment where the catalog itself is public and you just want a low-friction login.

**To enable**: nothing. As soon as `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` + `GOOGLE_REDIRECT_URL` are set, this mode is live. To avoid surprise sign-ups you still want to gate this with Mode B below.

#### Mode B — Invite only (recommended for any real deployment)

The backend only accepts Google sign-ins from **pre-existing users**. If a Google email does not match any row in `users`, the callback fails with `?google=err=unknown_user` and the user lands back on the login page with a "no tiene acceso al archivo" message.

**Best for**: any production deployment. Combined with the admin API this gives you full control of who can access the catalog and at what role.

**To enable**:

1. Log in to CENIDIM as the initial admin (created by `build_db.sh` from `ADMIN_PASS`).
2. For every person you want to grant access, call the admin API to pre-create their row. You only need `username`, `email`, `role` — the password is never used because they will sign in via Google. The backend's OAuth flow will then match by email and use the pre-existing role.

   ```bash
   # 1) Get an admin JWT
   curl -s -X POST http://localhost:8000/api/auth/login \
     -H 'Content-Type: application/json' \
     -d '{"username":"admin","password":"<ADMIN_PASS>"}'
   # → {"token":"eyJ…","user":{…}}

   # 2) Pre-create the user (role: viewer / editor / admin)
   curl -s -X POST http://localhost:8000/api/admin/users \
     -H "Authorization: Bearer $ADMIN_JWT" \
     -H 'Content-Type: application/json' \
     -d '{
       "username":"ana.investigadora",
       "email":"ana@cenidim.unam.mx",
       "password":"x",            # unused — they sign in with Google
       "role":"editor"
     }'
   ```

3. The user clicks "Continuar con Google" on the login page. Google redirects them through the consent screen, the backend matches the email, and the user is signed in with the pre-assigned role. The Google identity is then linked to the user account (`user_identities` table) so the email match only needs to happen on the first login.

**To change a user's role or remove their access**: use the existing admin endpoints at `/api/admin/users/:id` (PUT/DELETE) or `/api/admin/users/:id/identity` (DELETE) to unlink a Google identity. A user whose identity is unlinked falls back to password login if they have one; otherwise they can no longer sign in.

#### Switching modes

Mode A is the default and the cheapest to operate. To move to Mode B you do **not** need to change any code — just stop pre-creating new rows and any new Google sign-in will fail. To re-open Mode A simply skip the pre-create step in your onboarding flow. There is no flag to toggle.

### End-to-end flow (visualised)

```
┌────────────────┐ 1. click "Continuar"   ┌──────────────────┐
│ /login (SPA)   │ ──────────────────────▶│ /api/auth/google │
└────────────────┘                         │ /start           │
       ▲                                  └──────┬───────────┘
       │ 5. window.location =                       │ 2. set state cookie
       │    FRONTEND?google=ok                      │    302 → Google
       │                                            ▼
       │                                     ┌──────────────┐
       │                                     │ Google       │
       │                                     │ consent      │
       │                                     └──────┬───────┘
       │                                            │ 3. user approves
       │                                            ▼
┌────────────────┐ 4a. match email in       ┌──────────────────┐
│ <JWT> cookie   │     users → existing     │ /api/auth/google │
│ 24h TTL        │     role kept            │ /callback        │
└────────────────┘ 4b. auto-provision:        └──────────────────┘
                     if !Mode B:
                       new users row
                       (role = viewer)
                     then: link identity
```

### Configuration matrix

| Where | File | What to set |
|-------|------|-------------|
| Local dev (FastAPI) | `backend-fastapi/.env` | `CENIDIM_JWT_SECRET`, `CENIDIM_DB_PATH`, `RESEND_API_KEY` (empty → dev outbox). |
| Local dev (docker compose) | `docker-compose.yaml` | The backend service env vars (`CENIDIM_*`). |
| Production (Coolify) | `docker-compose-coolify.yaml` | Same `CENIDIM_*` vars via Coolify's secret store / `${...}` interpolation. |
| Anywhere | `frontend/.env` (if present) | n/a — the SPA receives the env via the build's runtime env. The Google button itself is a regular anchor to `/api/auth/google/start`, no env needed. |

### Step-by-step: create a Google OAuth client

1. Open the [Google Cloud Console](https://console.cloud.google.com/) and pick (or create) a project.
2. **APIs & Services → Credentials → Create credentials → OAuth 2.0 Client IDs**:
   - Application type: **Web application**.
   - Name: anything descriptive (e.g. `Cenidim dev`).
   - **Authorized JavaScript origins**: at least the backend origin. Local Docker: `http://localhost:8000`. Local vite: `http://localhost:8080`. Production: `https://<your-domain>`.
   - **Authorized redirect URIs**: must include the exact value of `GOOGLE_REDIRECT_URL` for each environment. Local Docker: `http://localhost:8000/api/auth/google/callback`. Local vite: `http://localhost:8080/api/auth/google/callback`. Production: `https://<your-domain>/api/auth/google/callback`.
3. Copy the generated **Client ID** + **Client secret** into the right env (see matrix above). `GOOGLE_REDIRECT_URL` must match the redirect URI you registered character-for-character.
4. Restart the backend. Visit `/login`; the "Continuar con Google" button should redirect to Google's consent screen.
5. After consent, Google redirects back to `GOOGLE_REDIRECT_URL`. The backend verifies `state` (CSRF), verifies the ID token signature against Google's JWKS, finds-or-creates the user, issues a JWT, and finally redirects to `FRONTEND_BASE_URL?google=ok`. Errors are surfaced as `?google=err=<code>` and rendered by the auth store.

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `redirect_uri_mismatch` from Google | `GOOGLE_REDIRECT_URL` does not exactly match what's registered | Compare character-by-character including `http` vs `https`, trailing slash, port |
| "Google (temporalmente no disponible)" button | backend can't read the OAuth env vars | Check `docker logs cenidim-web-backend-1` for `[AUTH] google env not configured`; verify the env block in the compose file or `.env` |
| `email not verified` log on the backend | the Google account has no verified email | Per Google's contract, only verified emails are accepted. The user must verify their email in their Google account settings |
| New Google email gets `?google=err=unknown_user` | Mode B is in effect and the email wasn't pre-created | Have an admin pre-create the user via `POST /api/admin/users` |
| New Google email auto-creates a viewer | Mode A is in effect | Expected; switch to Mode B by pre-creating the row with the desired role |
| User with role `viewer` needs to be promoted to `editor` or `admin` | — | `curl -X PUT /api/admin/users/:id -H "Authorization: Bearer $ADMIN_JWT" -d '{"role":"editor"}'` |

### Identity unlinking

If a user loses access to their Gmail (employee changes institutions, mailbox shut down, etc.) and the password was never set, the admin can unlink the Google identity so the account can be recovered with a fresh password reset:

```bash
curl -X DELETE http://localhost:8000/api/admin/users/<id>/identity \
  -H "Authorization: Bearer $ADMIN_JWT"
```

The user row stays; the `user_identities` row is removed. The user can no longer sign in with Google but can be issued a new password by the admin.

## Testing and Quality

- **Backend (FastAPI, primary)**: `cd backend-fastapi && PYTHONPATH=. uv run pytest tests/`. **177 tests pass at 96.05% coverage** with ruff clean. Coverage gate: 95% (`--cov-fail-under=95` in `pyproject.toml`).
- **Backend (Go, rollback only)**: `cd backend && go test ./...` + `golangci-lint run`. The Go tree is frozen at commit `2aab765`; no new code is accepted there.
- **Frontend**: `cd frontend && npm run test -- --run` (Vitest + Vue Test Utils). **277 tests pass.** Strict TypeScript — `npm run typecheck` runs in CI.
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
- `GET /api/auth/google/start` — kicks off the Google OAuth flow, sets a CSRF `state` cookie. **Phase 7+ is admin-only**: the login page hides the button; admins can still wire the env vars and use the dashboard's "Identidades" tab to manage linked accounts.

### Admin (`/api/admin/*`, requires JWT + role)
- Fonogramas CRUD: `GET /fonogramas`, `POST /fonogramas`, `GET /fonogramas/{id}`, `PUT /fonogramas/{id}`, `DELETE /fonogramas/{id}`
- Songs CRUD: `GET /songs`, `POST /songs`, `PUT /songs/{id}`, `DELETE /songs/{id}`
- Users CRUD: `GET /users`, `POST /users`, `PUT /users/{id}`, `DELETE /users/{id}`
- Identity management: `GET /users/{id}/identities`, `DELETE /users/{id}/identity`
- Operational: `GET /emails` (email outbox), `GET /audit` (audit log)

Role hierarchy: `viewer` (read) < `editor` (write) < `admin` (delete + user management + identities).

The `docs/PARITY.md` table inside `backend-fastapi/` is the contract between the Vue dashboard and the FastAPI service — every `apiService.<x>` call has a row.

## Deployment

The repo ships two compose files:

- **`docker-compose.yaml`** — **default**. Boots the FastAPI backend, the spaCy-seeded `letras.db`, and the frontend. Use for local dev **and** production (Coolify reads this file).
- **`docker-compose-coolify.yaml`** — Coolify production shape: named volume, secret placeholders, internal bridge network. Used by the `coolify` deployment target; defaults to FastAPI but pins the env vars Coolify needs.

The Go rollback compose (`docker-compose-go.yaml`) and the Phase 1
overlay (`docker-compose-fastapi.yaml`) were removed in Phase 9.

When changing the Google OAuth env vars, only the `environment:` block of the `backend` / `backend-fastapi` service needs to change in whichever compose file you target.

## License

See `LICENSE` (not included in this README; check the repository root).
# retrigger ci
<!-- CI: Tue Jul 14 22:23:24 CST 2026 -->
