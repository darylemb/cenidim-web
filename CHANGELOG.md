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
- Phase 3 (commit pending): 135 tests pass at 95.17% coverage,
  ruff clean, 95% gate, plus the docker-compose-fastapi overlay and
  multi-stage Dockerfile.
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

### Changed
- The FastAPI test conftest now shares a single `StaticPool`
  in-memory engine between the FastAPI app and direct ORM seed
  helpers so a row inserted in test setup is visible to subsequent
  API calls.
- Public router raw-SQL paths were replaced with SQLAlchemy 2.0
  ORM constructs (`select`, `func`, `case`, `cast`, `in_`,
  `order_by`, `replace`, `lower`, `trim`); no behaviour change.
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
