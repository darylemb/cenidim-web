# PR: sandbox → main (Phase 9 — retire the Go backend)

## Summary

This PR retires the Go / Gin backend from the repo. Phase 7 already
made FastAPI the production backend and `main` carries that cut-over
(PR #19 / #23). The Go tree (`backend/`) and its rollback compose have
now been removed, and the data-build pipeline is fully Python.

**TL;DR**: `docker compose up` boots the FastAPI stack; the `backend/`
Go tree, `docker-compose-go.yaml` rollback, and the Go CI job are gone.
The db is built by `scripts/build_db.py` (Python port of the old Go
builder, byte-compatible) inside a single-stage `db-init` image.

## What this PR contains

- **`backend/` removed** — the frozen Go service (main.go, handlers,
  middleware, models, database, cmd/build-db, Dockerfile, go.mod) is
  deleted. The build was ported to `scripts/build_db.py` (validated
  byte-compatible with the Go builder), so nothing depends on Go.
- **`docker-compose-go.yaml` removed** (rollback compose).
- **`docker-compose-fastapi.yaml` removed** (Phase 1 overlay; the CI
  job now uses the default compose).
- **`scripts/retire-go.sh` removed** — its job is done.
- **`docker/db-init.Dockerfile` + `docker/db-init-entrypoint.sh`** —
  moved from `backend/`, single Python+spaCy stage (build → classify →
  normalize).
- **`data/`** — the generated `letras.db` now lives at the repo root
  (was `backend/data/letras.db`). Compose volumes updated.
- **`docker-compose.yaml` / `docker-compose-coolify.yaml`** — updated
  db-init dockerfile path + data volume; also fixed a pre-existing
  duplicate `image:` key in the default compose.
- **`backend-fastapi/Dockerfile`** — dropped the Go db-builder + spaCy
  classifier stages (the db now comes from the db-init volume).
- **`.github/workflows/ci.yml`** — removed the `backend-go-checks` and
  `docker-build-go-rollback` jobs; the FastAPI docker job uses the
  default compose.
- **`scripts/run_ci_local.sh`** — removed the Go lint/test step.
- **`README.md`, `AGENTS.md`, `docs/CUTOVER.md`,
  `docs/adr/0001-fastapi-replaces-go.md`** — updated for the retired
  Go tree (Phase 9 documented as done).

## Test plan

- [x] Backend (FastAPI): 229 tests, 96% coverage, ruff clean.
- [x] Frontend: 267/276 tests, vue-tsc + lint clean.
- [x] `docker compose config` validates (default + coolify).
- [x] db-init image builds and regenerates `letras.db` end-to-end
  (build → classify → normalize) with the moved Dockerfile.
- [x] Compose volumes/healthchecks use the new `data/` path.

## Rollback

The Go tree is gone from the repo. If an emergency rebuild is ever
needed, the frozen stack still exists in git history at commit
`2aab765` (Phase 0 delivery).

## References

- `docs/adr/0001-fastapi-replaces-go.md`
- `docs/CUTOVER.md` (Phase 9 section)
- `backend-fastapi/docs/PARITY.md`
