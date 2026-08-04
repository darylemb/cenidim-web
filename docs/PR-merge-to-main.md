# PR: feature/fastapi-backend → main (cut-over PR; retires the Go tree)

## Summary

This PR merges the `feature/fastapi-backend` branch (Phases 1–8)
into `main`, replaces the Go service with the FastAPI service as
the production backend, and prepares Phase 9 (retiring the Go
tree in a follow-up PR).

**TL;DR**: `docker compose up` now boots the FastAPI backend on
port 8000. The Go backend lives under `backend/` and
`docker-compose-go.yaml` as the deterministic rollback target, kept
in the repo until Phase 9.

## Why

The Go / Gin backend grew past its sweet spot:

- JWT refresh tokens could not be revoked (no `RefreshTokenRevocation`
  table was added because the rotation would have required a DB
  migration that the Go tree didn't carry).
- SQL was inlined as `?`-placeholder strings. SQLAlchemy 2.0's
  stricter `text()` handling already breaks us.
- No OpenAPI spec — the front-end test suite mocks fetch with
  string-matched URLs.
- No metrics endpoint, no structured logs, no migrations, no
  schema versioning.

Phase 0 (commit `2aab765`) froze the Go tree at the last working
state so we could build the cut-over without blocking Phase 0
deliverables. Phase 1 started `feature/fastapi-backend` and the
remaining phases migrated surface by surface. Phase 7 flipped the
default `docker-compose.yaml` to the FastAPI service.

## Phases

| Phase | Branch                  | Commit  | Result                                                          |
| ---: | :---------------------- | :------ | :-------------------------------------------------------------- |
| 1    | `feature/fastapi-backend` | `2a19551` | Scaffold + auth service + real ORM models + tests              |
| 2    | `feature/fastapi-backend` | `bbdc768` | Public router ORM-ified                                      |
| 3    | `feature/fastapi-backend` | `e40eea3` | 95% coverage + Docker multi-stage wiring                      |
| 4    | `feature/fastapi-backend` | `b03f24d` | Frontend ↔ FastAPI parity + OpenAPI drift guard               |
| 5    | `feature/fastapi-backend` | `9fd2e66` | uvicorn smoke test + CI jobs + `scripts/smoke.sh`              |
| 6    | `feature/fastapi-backend` | `e21ed14` | Alembic + Prometheus metrics + structured JSON logging        |
| 7    | `feature/fastapi-backend` | `9ba5cd1` | Cut-over: default docker-compose points at FastAPI            |
| 8    | `feature/fastapi-backend` | `d58d6aa` | Admin Google-OAuth identity management UI                     |

## What this PR contains

- **`backend-fastapi/`** — new directory containing:
  - 178 source files, ~4k LOC of Python.
  - `app/` with the routers (admin / auth / public / google_oauth),
    services (auth / email / filters / google_oauth), models
    (mirrors the Go schema), schemas (Pydantic v2), and observability
    (Counter, Histogram, JSON formatter).
  - `tests/` with 177 tests at 96.05% coverage (95% gate met).
  - `Dockerfile` (multi-stage uv-managed, non-root runtime).
  - `scripts/` (smoke.sh, generate_openapi.py, alembic config).
  - `docs/PARITY.md` (the frontend ↔ FastAPI endpoint table).
  - `openapi.json` committed; drift guarded by CI.

- **`docker-compose.yaml`** — `backend` service now uses
  `backend-fastapi/Dockerfile`; env renamed to `CENIDIM_*`;
  healthcheck is a python+urllib one-liner.

- **`docker-compose-fastapi.yaml`** — kept as a development overlay
  (the Phase 5 CI job still references it).

- **`docker-compose-coolify.yaml`** — FastAPI service, Coolify
  conventions (named volume, secret placeholders).

- **`docker-compose-go.yaml`** — **NEW**, kept as the rollback compose
  (one `docker compose -f docker-compose-go.yaml up -d` away from
  flipping back to the Go tree).

- **`docs/adr/0001-fastapi-replaces-go.md`** — ADR for the cut-over
  decision.

- **`docs/CUTOVER.md`** — operator playbook with TL;DR, rollback,
  Phase 7 checklist, and "things to watch" during the 24h
  monitoring window.

- **`.github/workflows/ci.yml`** — `docker-build` now boots the
  FastAPI stack + runs `scripts/smoke.sh`; new
  `docker-build-go-rollback` job boots the Go stack to keep the
  rollback path green.

- **`README.md`** + **`AGENTS.md`** — rewritten architecture + setup
  sections to reflect the FastAPI default. Google OAuth section
  updated to document the Phase 7+ admin-only visibility change.

- **`frontend/src/types/index.ts`** — added `UserIdentity`.

- **`frontend/src/services/api.ts`** — added `adminListIdentities`
  and `adminUnlinkIdentity`.

- **`frontend/src/views/AdminPanel.vue`** — new "Identidades"
  column in the Users tab with per-identity unlink actions.

- **`frontend/src/assets/main.css`** — `.btn-warning`,
  `.identity-list`, `.identity-empty`, `.identity-subject` styles.

## What this PR deliberately does **not** do

- **It does not delete `backend/`.** That cleanup is Phase 9 (a
  follow-up PR after 1 week of green production metrics — see
  `docs/CUTOVER.md` Step "After 24h of green metrics, retire the Go
  tree in Phase 8" → which renumbered to Phase 9 in the final
  plan).
- **It does not delete `docker-compose-go.yaml`.** Same reason.
- **It does not delete the `fix/critical-bugs-dashboard-and-oauth`
  or `ux/dashboard-fixes-2026-07` branches.** These are reference
  branches per the user's "no borres ninguna rama" instruction.

## Test plan

- [x] 177 backend tests pass at 96.05% coverage, ruff clean
  (`backend-fastapi/pyproject.toml` gate = 95%)
- [x] 277 frontend tests pass (`cd frontend && npm run test -- --run`)
- [x] OpenAPI drift guard (`tests/api/test_openapi.py`) green
- [x] uvicorn smoke test (`tests/integration/test_uvicorn_smoke.py`) green
- [x] Docker FastAPI compose smoke (`./scripts/smoke.sh http://localhost:8000`) green
- [x] Docker Go rollback compose healthcheck green
- [x] Trivy vulnerability scan passes (high+critical gates set in CI)

## Rollback procedure (operator-facing)

```bash
docker compose down
docker compose -f docker-compose-go.yaml up -d
```

The Go backend is frozen at commit `2aab765` (Phase 0), so the
rollback image is deterministic.

## Post-merge checklist (Phase 9, in a separate PR)

1. Delete `backend/` (Go service + Dockerfile + Dockerfile.init + main + handlers + middleware + models + database).
2. Delete `docker-compose-go.yaml`.
3. Delete `backend/cmd/build-db/main.go`. **But** replace it with
   a Python equivalent inside `backend-fastapi/` or `scripts/`
   so the `db-init` Docker sidecar still works (it currently uses
   the Go CLI to seed `letras.db`).
4. After Phase 9, the FastAPI compose's `db-init` step should run
   `backend-fastapi/scripts/init_db.py` (or similar) instead of
   `backend/Dockerfile.init`.
5. Drop the `fix/critical-bugs-dashboard-and-oauth` and
   `ux/dashboard-fixes-2026-07` branches if no longer relevant.
6. Update `docker-compose-coolify.yaml` to use the same db-init
   path as `docker-compose.yaml`.

## Risk assessment

- **Low**: the FastAPI service has been live-tested in the CI
  pipeline via `docker-build-fastapi` for two PRs.
- **Low**: parity is verified by `docs/PARITY.md` and the OpenAPI
  drift guard.
- **Low**: rollback is one `docker compose` command away.
- **Medium**: the db-init sidecar still uses the Go CLI. If that
  becomes a problem, we have to rewrite it in Python before
  Phase 9. This PR doesn't change that.

## References

- `docs/adr/0001-fastapi-replaces-go.md`
- `docs/CUTOVER.md`
- `backend-fastapi/docs/PARITY.md`
- `backend-fastapi/openapi.json`
- `CHANGELOG.md`
- The 9 commits on `feature/fastapi-backend` since the cut-over was
  planned; this PR squashes them into the merge.
