# Cutover Playbook — Phase 7

This document is the operator-facing runbook for swapping the
production backend from the Go / Gin service to the FastAPI /
Pydantic v2 service.

## TL;DR

```bash
# 1. Stop the existing Go-backed stack.
docker compose down

# 2. Boot the FastAPI-backed stack (default compose file).
docker compose up -d --build

# 3. Verify.
docker compose ps
curl -sf http://localhost:8000/healthz
./backend-fastapi/scripts/smoke.sh http://localhost:8000
```

That's it. The frontend container already targets ``/api`` via
the nginx proxy; no rebuild needed.

## What changes for operators

| | Before | After |
| --- | --- | --- |
| Default compose | `docker compose.yaml` (Go) | `docker compose.yaml` (FastAPI) |
| Backend port | 8080 (Go) | 8000 (FastAPI) |
| Healthcheck | `./healthcheck` (Go binary) | `python -c "...urlopen('/healthz')..."` |
| DB init | `backend/Dockerfile.init` (Go CLI) | `alembic upgrade head` |
| Login form | `username + password` | unchanged |
| Google OAuth | visible on login page | **removed** (no SSO in this deployment) |
| Metrics | none | `GET /metrics` (Prometheus) |
| Logs | plain text to stderr | structured JSON to stdout |

## Rollback

If anything goes wrong, revert to the Go backend:

```bash
docker compose down
docker compose -f docker-compose-go.yaml up -d
```

The Go backend is frozen at commit ``2aab765`` (the Phase 0
delivery) so the rollback image is reproducible. Operators keep
both compose files in the repo so flipping back is one command.

## Phase 7 checklist

1. `docker compose down` — stop the Go-backed stack.
2. `docker compose -f docker-compose-fastapi.yaml up -d --build`
   — boot the FastAPI overlay alongside the existing frontend.
3. `curl -sf http://localhost:8000/healthz` returns 200.
4. `./backend-fastapi/scripts/smoke.sh http://localhost:8000`
   exits 0.
5. Browse to the dashboard; log in with the existing admin
   credentials; verify search, admin CRUD, and password reset.
6. `docker compose down` then `docker compose up -d --build` — the
   default compose file now points at FastAPI.
7. Monitor `/metrics` for the first 24h:
   - `cenidim_http_requests_total{status="500"}` should stay at 0.
   - `cenidim_http_request_duration_seconds` p99 should be under
     1s for /api/search.
8. After 24h of green metrics, retire the Go tree in Phase 8.

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

The Go backend's migration script writes the same tables with the
same columns. The first ``alembic upgrade head`` against a
Go-produced ``letras.db`` should be a no-op (version stamped,
no DDL). If you see DDL emitted, double-check the schema mapping
in ``alembic/versions/``.

## Phase 8 (post-cutover) — Go tree retirement

After 1 week of green production metrics, retire the Go tree in a
follow-up PR:

1. Delete ``backend/`` (Go service + Dockerfile + Dockerfile.init).
2. Delete ``docker-compose-go.yaml`` (the rollback compose file).
3. Delete ``backend/Dockerfile.healthcheck`` (Go-specific).
4. Drop the ``fix/critical-bugs-dashboard-and-oauth`` and
   ``ux/dashboard-fixes-2026-07`` branches if no longer relevant.

Until then, both stacks live in the repo and the cut-over is one
``docker compose down && docker compose up -d`` away from being
reversed.