# Cenidim Web Application Constitution

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)

All features MUST be supported by tests before implementation is considered complete. The backend MUST pass `go test ./...` and the frontend MUST pass `npm test` before merging. TDD discipline: write failing tests first, then implement to make them pass. This ensures reliability and enables safe refactoring.

### II. API-First Design

Every capability is exposed through a RESTful API consumed by the frontend. APIs define contracts between services and clients. API changes that break contracts require a migration plan. The backend exposes well-defined endpoints at `/api/*` with proper versioning consideration.

### III. Security by Design

Authentication uses JWT with appropriate secret management. Role-based access control protects admin endpoints at `/api/admin/*`. CORS origins are explicitly configured via environment variables. Security events MUST be logged. Secrets MUST NOT be committed to the repository.

### IV. Operational Observability

All services expose health check endpoints (`GET /health`). Structured logging enables debugging in production. Docker containers use distroless images for minimal attack surface. Health checks are implemented as separate binaries to verify runtime integrity.

### V. Continuous Delivery

Every change MUST pass CI before merging: backend lint and tests, frontend lint/typecheck/build and tests. Docker builds are verified with health checks. The database is built deterministically from source CSV and lyrics files. Deployments use `docker compose up --build -d`.

## Technology Stack

The system is built with:

- **Backend**: Go 1.21+ with Gin framework, SQLite database
- **Frontend**: Vue 3 with Vite, TypeScript strict mode, Pinia state, Vue Router
- **Infrastructure**: Docker with multi-stage builds, unprivileged nginx
- **Quality**: golangci-lint for Go, ESLint + vue-tsc for frontend, Vitest for unit tests, Playwright for E2E tests

Technology choices are fixed unless approved through the amendment process.

## Development Workflow

### Prerequisites

- Database initialization: `./scripts/build_db.sh` (requires Go + spaCy `es_core_news_md` model)
- Backend dev: `cd backend && go run main.go` (port 8080)
- Frontend dev: `cd frontend && npm install && npm run dev` (port 5173)

### Quality Gates

1. **Backend**: `golangci-lint run` and `go test ./...`
2. **Frontend**: `npm run lint`, `npm run build` (includes typecheck), `npm run test -- --run`, `npm run test:e2e`
3. **Docker**: Health check at `localhost:8000/health`

### Git Workflow

Features use branch-based workflow. Commits MUST be atomic and reference feature context. Use `speckit.git` hooks for automated commits at workflow boundaries.

## Governance

This constitution is the authoritative source for development practices. It supersedes informal conventions.

**Amendment Procedure**:
1. Propose change with rationale and migration impact
2. Document compliance requirements
3. Require approval from project maintainers
4. Version bump follows semantic versioning:
   - MAJOR: Backward-incompatible governance or principle changes
   - MINOR: New principles or materially expanded guidance
   - PATCH: Clarifications, wording, typo fixes

**Compliance**:
- All PRs MUST verify adherence to these principles
- Complexity deviations MUST be justified in plan documents
- Runtime guidance is in `README.md`

**Version**: 1.0.0 | **Ratified**: 2026-05-13 | **Last Amended**: 2026-05-13