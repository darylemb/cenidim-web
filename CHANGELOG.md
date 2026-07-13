# Changelog

All notable changes to this project are documented here. The format
is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## Unreleased

### Added
- FastAPI backend (`backend-fastapi/`) under `feature/fastapi-backend`.
  Phase 1 (commit `2a19551`): initial scaffold, config module, real
  ORM models, and the auth service.
- Phase 2 (commit `bbdc768`): ORM-ified public router + 20 tests at
  92% coverage.
- Phase 3 (commit `e40eea3`): 135 tests at 95.17% coverage, ruff
  clean, 95% gate, plus the docker-compose-fastapi overlay and
  multi-stage Dockerfile.
- Phase 4 (commit `b03f24d`): frontend parity (search ?query alias,
  /api/auth/me, AuthResponse token field, admin song create returns
  SongOut) + OpenAPI drift guard (openapi.json checked in,
  scripts/generate_openapi.py, tests/api/test_openapi.py).
- Phase 5 (commit `9fd2e66`): end-to-end integration test that boots
  real uvicorn (`tests/integration/test_uvicorn_smoke.py`) +
  `scripts/smoke.sh` post-deploy health check + GitHub Actions
  `fastapi-checks` and `docker-build-fastapi` jobs.
- Phase 6 (commit `e21ed14`): Alembic migrations (alembic.ini +
  env.py + initial_schema revision), hand-rolled Prometheus metrics
  (`app/observability.py` + `/metrics` endpoint), structured JSON
  logging (`app/logging_config.py`).
- Phase 7 (commit `9ba5cd1`): **cut-over**. `docker-compose.yaml`
  now points at the FastAPI service. `docker-compose-go.yaml` is
  kept as the rollback target. `docker-compose-fastapi.yaml`
  remains as a development overlay. `docker-compose-coolify.yaml`
  updated for the production stack. `docs/adr/0001-fastapi-replaces-go.md`
  documents the decision; `docs/CUTOVER.md` is the operator
  playbook. GitHub Actions adds a `docker-build-go-rollback` job
  that boots the Go stack to ensure the rollback path stays
  green.
- Phase 8 (commit pending): Google OAuth identity management in
  the dashboard. The Users tab now shows each row's linked
  identities (provider + subject) with an inline
  `Desvincular <provider>` action that calls the FastAPI
  `/api/admin/users/{id}/identity` DELETE. Backend test coverage
  for the identity-admin endpoints; frontend tests for the new
  column + unlink flow. (`UserIdentity` type added to the
  frontend's `src/types/index.ts`; `apiService.adminListIdentities`
  and `apiService.adminUnlinkIdentity` added to `src/services/api.ts`.)
- New `RefreshTokenRevocation` and `AuditLog` tables matching the
  planned schema (mirrored from the Go-side design).
- `/api/auth/refresh` rotates the refresh token's `jti` so stolen
  cookies cannot be replayed.
- `session_scope_cm` async-context-manager so non-FastAPI callers
  (the email service, the Google OAuth helper) can use the same
  `async with session_scope_cm() as db:` idiom the FastAPI deps use.
- `StubIDTokenVerifier` test seam for the Google OAuth verifier.
- `docker-compose-fastapi.yaml` overlay that runs the FastAPI
  backend alongside the existing spaCy classifier and frontend.
- `backend-fastapi/Dockerfile` (multi-stage, uv-managed,
  non-root runtime, exposes 8000).
- `tests/conftest.py` helpers (`make_user`, `make_admin`,
  `make_identity`, `make_email_outbox`) for end-to-end admin tests.
- Audit-log endpoints (`GET /api/admin/audit`, filtered by
  `actor_id` + `action`).
- Emails-outbox endpoint (`GET /api/admin/emails`, filtered by
  `only_failures`).
- OpenAPI 3.1 spec auto-generated and committed
  (`openapi.json`); drift guarded by `tests/api/test_openapi.py`.
- `scripts/smoke.sh` (curl-driven post-boot health check).
- `scripts/generate_openapi.py` to refresh the spec after router
  changes.

### Changed
- The FastAPI test conftest now shares a single `StaticPool`
  in-memory engine between the FastAPI app and direct ORM seed
  helpers so a row inserted in test setup is visible to subsequent
  API calls.
- Public router raw-SQL paths were replaced with SQLAlchemy 2.0
  ORM constructs (`select`, `func`, `case`, `cast`, `in_`,
  `order_by`, `replace`, `lower`, `trim`); no behaviour change.
- `/api/search` accepts both `?query=` (Vue convention) and `?q=`
  (FastAPI default) via FastAPI's `alias=` mechanism.
- `/api/auth/{login,register,refresh}` responses now include a
  `token` field that mirrors the access-token JWT.
- `POST /api/admin/songs` returns the created `SongOut` (with id)
  so the Vue dashboard can use it directly.
- AGENTS.md updated to document the FastAPI branch + commands.

### Security
- JWT `sub` claim is `str()` on mint and `int()` on verify
  (python-jose requires the spec-compliant string form).
- Reset-token verify mirrors the create-side SHA-256 pre-hash so
  round-trips work after we replaced `passlib` with direct
  `bcrypt`.
- `EmailService.enqueue` catches every exception (was catching
  only `SQLAlchemyError`) so an outbox failure can never break the
  caller.

## [0.0.0] - Initial Go release (legacy)

The Go backend (`backend/`) predates this changelog. Its
post-Phase-0 history is captured in the git log on `main`.
