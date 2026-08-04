# Cutover Playbook — Phase 7 + 9 (Go → FastAPI, Go retired)

This document is the operator-facing runbook for swapping the
production backend from the Go / Gin service to the FastAPI /
Pydantic v2 service, and for the Phase 9 retirement of the Go tree.

## TL;DR

```bash
# Boot the FastAPI stack (default compose file).
docker compose up -d --build

# Verify.
docker compose ps
curl -sf http://localhost:8000/healthz
./backend-fastapi/scripts/smoke.sh http://localhost:8000
```

That's it. The frontend container already targets ``/api`` via
the nginx proxy; no rebuild needed.

## What changed for operators

| | Before (Go) | After (FastAPI) |
| --- | --- | --- |
| Default compose | `docker compose.yaml` (Go) | `docker compose.yaml` (FastAPI) |
| Backend port | 8080 (Go) | 8000 (FastAPI) |
| Healthcheck | `./healthcheck` (Go binary) | `python -c "...urlopen('/healthz')..."` |
| DB init | `backend/Dockerfile.init` (Go CLI) | `docker/db-init.Dockerfile` (Python+spaCy) |
| DB volume | `./backend/data:/data` | `./data:/data` |
| Login form | `username + password` | unchanged |
| Google OAuth | visible on login page | **removed** (no SSO in this deployment) |
| Metrics | none | `GET /metrics` (Prometheus) |
| Logs | plain text to stderr | structured JSON to stdout |

## Rollback

The Go backend is retired (Phase 9): the ``backend/`` tree and
``docker-compose-go.yaml`` were removed from the repo. The frozen Go
backend still exists at commit ``2aab765`` in git history if an
emergency rebuild is ever needed.

## Phase 7 checklist

1. `docker compose down` — stop any existing stack.
2. `docker compose up -d --build` — boot the FastAPI stack.
3. `curl -sf http://localhost:8000/healthz` returns 200.
4. `./backend-fastapi/scripts/smoke.sh http://localhost:8000`
   exits 0.
5. Browse to the dashboard; log in with the existing admin
   credentials; verify search, admin CRUD, and password reset.
6. Monitor `/metrics` for the first 24h:
   - `cenidim_http_requests_total{status="500"}` should stay at 0.
   - `cenidim_http_request_duration_seconds` p99 should be under
     1s for /api/search.

## Phase 9 — Go tree retirement (done)

The Go tree was retired: ``backend/``, ``docker-compose-go.yaml``,
``docker-compose-fastapi.yaml``, ``scripts/retire-go.sh`` and the Go
CI job were removed. The db build now runs entirely on Python
(``scripts/build_db.py`` → ``scripts/classify_songs.py`` →
``scripts/normalize_db.py``) from a single-stage ``db-init`` image.

## Things to watch

- The dashboard reads the access JWT from the response **body**,
  not the cookie. If you see "Logged out unexpectedly" right after
  login, the response body field is missing — check the FastAPI
  logs for an auth exception.
- `EmailService.enqueue` writes to `email_outbox` even when Resend
  is unconfigured; `/api/admin/emails?only_failures=true` lists
  anything that bounced.
- Refresh tokens are stored in
  ``refresh_token_revocations`` so a stolen refresh cookie can
  only be used until its next rotation (15s after first use).
- Alembic is the source of truth for schema changes. ``Base.metadata.create_all``
  is only used for local dev / unit tests.

## Migration: applying Alembic on an existing letras.db

The first ``alembic upgrade head`` against a Go-era ``letras.db``
should be a no-op (version stamped, no DDL). If you see DDL emitted,
double-check the schema mapping in ``alembic/versions/``.