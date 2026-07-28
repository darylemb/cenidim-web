# ADR 0001: FastAPI replaces Go as the primary backend

- **Status:** Accepted (Phase 7 cut-over)
- **Date:** 2026-07-13
- **Authors:** @darylemb

## Context

The CENIDIM Archivo Musical backend was originally a Go / Gin
service (`backend/`) reading from `letras.db` via the
``backend/cmd/build-db`` CLI. By Phase 0 it had grown to:
  - 13 admin endpoints (fonogramas / songs / users CRUD + audit
    log + email outbox + Google identity link)
  - 7 auth endpoints (login / register / forgot / reset / refresh
    / logout / Google OAuth)
  - 5 public endpoints (search / song-detail / stats / timeline /
    word-cloud)
  - Refresh-token rotation via `RefreshTokenRevocation`
  - HttpOnly cookies + CSRF + Bearer fallback

The original Go stack's drawbacks:
  - 3-tier auth role gate is encoded by string-comparison against
    magic constants (`viewer` / `editor` / `admin`); no schema-
    enforced contract.
  - Refresh tokens are JWT-only with no rotation table — a stolen
    refresh cookie replays indefinitely until expiry.
  - SQL lives inline as `?`-placeholder strings; SQLAlchemy 2.0's
    stricter `text()` handling was already breaking us on the
    next dependency upgrade.
  - No OpenAPI spec; the front-end test suite mocks fetch with
    string-matched URLs and never asserts a real contract.

## Decision

Adopt `backend-fastapi/` as the production backend. The Go
service is retained **only as a rollback target** under
`docker-compose-go.yaml` so operators can flip back at any time
without rebuilding images.

`docker-compose.yaml` (the default `docker compose up`) now points
at the FastAPI service.

## Consequences

### Positive

- ORM throughout (SQLAlchemy 2.0) — schema-as-source-of-truth.
- Alembic migrations replace the `db-builder` Go CLI.
- 171 tests pass at 95.93% coverage, ruff clean, 95% gate met.
- OpenAPI spec is auto-generated and committed; CI regenerates
  and asserts no diff.
- Refresh-token rotation table (`RefreshTokenRevocation`) closes
  the stolen-cookie replay window.
- `/api/auth/me` + a body-level `token` field on
  `AuthResponse` removes the dashboard's reliance on
  `document.cookie` reads.
- Prometheus `/metrics` + JSON logging give Coolify / Grafana
  the operational surface the Go stack never had.
- Multi-stage `Dockerfile` (uv-managed deps, non-root) keeps the
  image lean.

### Negative

- Two stacks to maintain during the transition window (Go is
  frozen but still in the repo for rollback).
- Python ops surface (uv, alembic, ``backend-fastapi/`` tests) is
  new for operators used to ``go test ./...`` / single binary.
- Some Go-specific behaviours were re-implemented (manual
  cascade delete in `admin_delete_fonograma`, refresh cookie path
  ``/api/auth/refresh``) instead of relying on driver-level FKs.

### Neutral

- The frontend did **not** need to change: every call site
  (`apiService.*`) keeps its URL + payload shape. The alias
  ``?query=`` on `/api/search` lets the Vue convention work
  unchanged.
- The cut-over is gated on the docker-compose-fastapi overlay
  passing its smoke script end-to-end (see CUTOVER.md).

## Rollback

If the cut-over fails, revert with:

```bash
docker compose down
docker compose -f docker-compose-go.yaml up -d
```

The Go stack is frozen at commit `2aab765` (Phase 0) so the
rollback has a deterministic image.

## Phases

| Phase | Branch | Status | Result |
| --- | --- | --- | --- |
| 1 | `feature/fastapi-backend` | Merged | Scaffold + auth service skeleton |
| 2 | `feature/fastapi-backend` | Merged | Public router ORM-ified |
| 3 | `feature/fastapi-backend` | Merged | 95% coverage + Docker wiring |
| 4 | `feature/fastapi-backend` | Merged | Frontend parity + OpenAPI drift guard |
| 5 | `feature/fastapi-backend` | Merged | uvicorn smoke test + CI + scripts/smoke.sh |
| 6 | `feature/fastapi-backend` | Merged | Alembic + metrics + structured logging |
| 7 | `feature/fastapi-backend` | **This PR** | Cut-over: docker-compose points at FastAPI |

After Phase 7 lands, Phase 8 (post-cutover) retires the Go tree
in a follow-up PR.

## References

- `docs/PARITY.md` — full frontend ↔ FastAPI endpoint table.
- `docs/CUTOVER.md` — operator playbook for the cut-over.
- `backend-fastapi/openapi.json` — committed OpenAPI spec.
- `feature/fastapi-backend` — implementation branch.