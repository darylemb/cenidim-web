# Cenidim Web Application

This repository contains the full stack web application for **Cenidim** (Centro Nacional de Investigación, Documentación e Información Musical "Carlos Chávez").

The application serves a digital archive of musical lyrics — the CENIDIM children's songbook collection — and lets researchers search by title, album, or lyric content, browse statistical dashboards, and (for admins) manage the catalog and user accounts. The frontend follows a single design-token reference (Fraunces + Outfit + JetBrains Mono on a vino/mostaza/crema palette) so every page is visually consistent.

**Glossary & terminology**: see [`docs/GLOSARIO.md`](docs/GLOSARIO.md) for the canonical definitions of every chart, KPI, and category shown on the dashboard. The frontend's `ⓘ` info buttons on each chart source their long-form text from `frontend/src/config/chartInfo.ts`.

## Architecture

1. **Backend (Go – Gin)**: high-performance REST API written in Go. Runs on a **Distroless** image for minimum attack surface. Search latency is single-digit milliseconds on the full ~4,000 song catalog.
2. **Frontend (Vue 3 + TypeScript)**: SPA served via an **unprivileged Nginx** container. State is managed with Pinia; routing with Vue Router; charts with vue-chartjs. Build tool is Vite. Requires **Node 24**.
3. **Data management**: a two-step pipeline that parses the raw songbook and lyrics into a structured SQLite database.
   - `cmd/build-db/main.go` walks `db_fonografia.csv` + `LetrasTXT/`, normalises titles, and inserts fonogramas + songs into `letras.db`.
   - `scripts/classify_songs.py` then uses **spaCy** (`es_core_news_md`) to compute OOV percentages, classify each song as `ESPAÑOL_ESTANDAR` / `ESPAÑOL_REGIONAL` / `LENGUA_INDIGENA`, and assign a canonical **theme** (see below).
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

Copy the example file and edit it:

```bash
cp backend/.env.example backend/.env
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET` | **Yes** | none | Secret key for signing JWTs. The backend fatals on startup if this is missing in production. Use at least 256 bits of entropy. |
| `CORS_ALLOWED_ORIGINS` | No | `http://localhost,http://localhost:3000,http://localhost:8000` | Comma-separated list of allowed CORS origins. |
| `DB_PATH` | No | `letras.db` | Path to the SQLite database file. |
| `PORT` | No | `8080` | HTTP port the backend listens on. |
| `GOOGLE_CLIENT_ID` | For Google sign-in | none | OAuth 2.0 client ID from the Google Cloud console. |
| `GOOGLE_CLIENT_SECRET` | For Google sign-in | none | OAuth 2.0 client secret paired with `GOOGLE_CLIENT_ID`. |
| `GOOGLE_REDIRECT_URL` | For Google sign-in | none | The exact callback URL registered in the Google Cloud console. For local dev: `http://localhost:8000/api/auth/google/callback` (Docker) or `http://localhost:8080/api/auth/google/callback` (vite dev). For production: `https://<your-domain>/api/auth/google/callback`. Must match the path registered as an "Authorized redirect URI" in your OAuth client. |
| `FRONTEND_BASE_URL` | For Google sign-in | `http://localhost:3000` | The SPA origin used to build the post-callback redirect target. For local dev: `http://localhost` (Docker) or `http://localhost:5173` (vite dev). For production: `https://<your-domain>`. The Google callback redirects here with `?google=ok` (or `?google=err=<code>` on failure). |

**Security note for production**: never commit `backend/.env`. The `.gitignore` already excludes it. Generate a real `JWT_SECRET` with `openssl rand -hex 32` (or equivalent) and use a different secret per environment.

### 3. Running with Docker (Recommended)

```bash
docker compose up --build -d
```

- **Frontend**: `http://localhost` (served via unprivileged Nginx).
- **Backend API**: internal port 8080, exposed at `http://localhost:8000` for local dev.
- **Health check**: `http://localhost:8000/health`.

The multi-stage `backend/Dockerfile` runs the Go builder, then the spaCy classifier, then the distroless final image with a separate healthcheck binary. The `db-init` sidecar regenerates `letras.db` from `LetrasTXT/` + `db_fonografia.csv` on every `docker compose up` and exits; the backend waits for it via `depends_on.condition: service_completed_successfully` so the API never serves a stale database.

`frontend/Dockerfile` uses `nginx-unprivileged:alpine` (no root, port 80).

### 4. Local development (no Docker)

**Backend (Go):**
```bash
cd backend
go run main.go
# server on :8080
```

**Frontend (Vue 3 + Vite, Node 24):**
```bash
cd frontend
npm install
npm run dev   # Vite dev server on :5173, proxies /api to :8080
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

## Google sign-in

The login page exposes a **"Continuar con Google"** button. Clicking it kicks off an OAuth 2.0 Authorization Code flow against Google's consent screen; after the user approves, the backend verifies the `state` cookie (CSRF protection), verifies the ID token signature against Google's JWKS, and either signs in the matching user or auto-provisions a new one.

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
| Local dev (vite + go run) | `backend/.env` | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URL=http://localhost:8080/api/auth/google/callback`, `FRONTEND_BASE_URL=http://localhost:5173` |
| Local dev (docker compose) | `docker-compose.yaml` | The same four vars; `GOOGLE_REDIRECT_URL` is `http://localhost:8000/api/auth/google/callback` and `FRONTEND_BASE_URL=http://localhost`. Already present with empty placeholders — fill them in. |
| Production (Coolify) | `docker-compose-coolify.yaml` | Same four vars. `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` come from Coolify's secret store via `${GOOGLE_CLIENT_ID}` interpolation; the redirect + frontend URLs default to the production domain. Override per environment if you use a non-default host. |
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

- **Backend**: `go test ./...` (unit + integration). The repo also has `golangci-lint` config; run with `golangci-lint run`.
- **Frontend**: `npm run test -- --run` (Vitest + Vue Test Utils + Testing Library). The frontend uses **strict TypeScript** — `vue-tsc --noEmit` runs in CI.
- **Design tokens**: `bash scripts/audit_design_tokens.sh frontend/src 0.05` verifies that no more than 5 % of style-bearing lines use hard-coded hex colors or px values outside `tokens.css`. SC-009 of the spec requires this drift to stay below 2 % at the end of the project.
- **End-to-end CI**: `scripts/run_ci_local.sh` runs the full sequence (backend lint + test → frontend lint + typecheck + test → docker compose build + health check).
- **Code review**: `scripts/run_code_review_all.sh` is the pre-merge gate (FR-027 of spec 004 / SC-010). It batches all source files and invokes the `/code-review` command on each batch. **This is opt-in**: the agent never runs it automatically. To run it before opening a PR:
  ```bash
  ./scripts/run_code_review_all.sh
  # review-reports/code-review-<timestamp>/summary.md will list OK / failed / skipped batches
  ```

## API Endpoints

### Public
- `GET /` — API welcome message
- `GET /health` — health check (used by the Docker healthcheck)
- `GET /api/search` — paginated song search (`q`, `field`, `page`, `limit`, `clasificacion`, `orderBy`, `orderDir`)
- `GET /api/song/:song_id` — song details + lyrics
- `GET /api/timeline` — songs grouped by year
- `GET /api/stats` — aggregate dashboard metrics; honors the shared filter query parameters (`theme`, `year_from`, `year_to`, `clasificacion`, `album`, `q`)
- `GET /api/word-cloud` — word frequencies for the dashboard's word cloud

### Authentication (`/api/auth/*`)
- `POST /api/auth/login` — password sign-in
- `POST /api/auth/register` — open self-registration (if enabled)
- `GET /api/auth/me` — current user profile (requires JWT)
- `GET /api/auth/google/start` — kicks off the Google OAuth flow, sets a CSRF `state` cookie
- `GET /api/auth/google/callback` — Google redirects here; the backend verifies `state`, verifies the ID token against Google's JWKS, finds-or-creates the user, issues a JWT, and finally redirects to `FRONTEND_BASE_URL?google=ok` (or `?google=err=<code>`).

### Admin (`/api/admin/*`, requires JWT + role)
- Fonogramas CRUD: `/fonogramas`, `/fonogramas/:id`
- Songs CRUD: `/songs`, `/songs/:id`
- Users management: `/users`, `/users/:id`
- Identity unlink (admin only): `DELETE /users/:id/identity` — removes a linked Google identity from a user so they can no longer sign in with Google.

Role hierarchy: `viewer` (read) < `editor` (write) < `admin` (delete + user management).

## Deployment

The repo ships two compose files:

- **`docker-compose.yaml`** — local development. Builds the images, mounts the source for `db-init`, exposes the backend on `http://localhost:8000` and the frontend on `http://localhost`.
- **`docker-compose-coolify.yaml`** — production. Used by Coolify to deploy on a server. The Google OAuth env vars are loaded from Coolify's secret store; the redirect + frontend URLs default to the production domain. Do not modify volumes, networking, or other non-essential values when changing the OAuth configuration.

When changing the Google OAuth env vars, only the `environment:` block of the `backend` service needs to change in either compose file.

## License

See `LICENSE` (not included in this README; check the repository root).
