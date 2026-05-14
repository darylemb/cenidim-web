# Tasks: Fix Execution Issues

**Input**: Design documents from `/specs/001-fix-execution/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`

---

## Phase 1: Setup (Test Infrastructure Fix)

**Purpose**: Add Chart.js mock to Vitest test setup to fix jsdom environment issues

- [x] T001 Add Chart.js mock in frontend/src/test/setup.ts using vi.mock('chart.js') and vi.mock('vue-chartjs')

---

## Phase 2: User Story 1 - Fix Dashboard Test Failures (Priority: P1)

**Goal**: DashboardView tests run without Chart.js unhandled promise rejections

**Independent Test**: `npm test -- --run` shows 8 tests pass with 0 errors

### Implementation for User Story 1

- [x] T002 [US1] Verify frontend/src/views/__tests__/DashboardView.test.ts passes without Chart.js errors

---

## Phase 3: User Story 2 - Fix API Service TypeScript Inconsistency (Priority: P2)

**Goal**: api.js converted to api.ts with proper TypeScript types; vue-tsc passes

**Independent Test**: `npm run build` completes without type errors

### Implementation for User Story 2

- [x] T003 [P] [US2] Create frontend/src/services/api.ts with type definitions (SearchParams, SearchResult, Song, Stats interfaces)
- [x] T004 [US2] Update all imports in frontend/src to use api.ts instead of api.js
- [x] T005 [US2] Delete frontend/src/services/api.js after successful migration

---

## Phase 4: User Story 3 - Fix Timeline View Test Errors (Priority: P3)

**Goal**: TimelineView tests run without Chart.js unhandled promise rejections

**Independent Test**: `npm test -- --run` shows TimelineView tests complete without errors

### Implementation for User Story 3

- [x] T006 [US3] Verify frontend/src/views/__tests__/TimelineView.test.ts passes without Chart.js errors

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final verification that all quality gates pass

- [x] T007 Run npm test -- --run to verify all 8 tests pass with 0 errors
- [x] T008 Run npm run build to verify TypeScript compilation succeeds
- [x] T009 Run npm run lint to verify no warnings or errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - runs first to establish Chart.js mock
- **Phase 2 (US1)**: Depends on Phase 1 completion
- **Phase 3 (US2)**: Depends on Phase 1 completion (independent of US1)
- **Phase 4 (US3)**: Depends on Phase 1 completion (independent of US1 and US2)
- **Phase 5 (Polish)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: After Chart.js mock setup - tests DashboardView specifically
- **User Story 2 (P2)**: After Chart.js mock setup - migrates api.js to api.ts
- **User Story 3 (P3)**: After Chart.js mock setup - tests TimelineView specifically

### Within Each User Story

- US1: T001 (setup mock) → T002 (verify tests)
- US2: T003 (create api.ts) → T004 (update imports) → T005 (delete old file)
- US3: T001 (setup mock) → T006 (verify tests)
- Polish: T007 → T008 → T009 in sequence

### Parallel Opportunities

- US1, US2, US3 can all start after Phase 1 (T001) is complete
- T003 and T002 can run in parallel (different files)
- T003 and T006 can run in parallel (different files)

---

## Parallel Example

```bash
# After Phase 1 complete, run these in parallel:
Task: "T003 - Create api.ts with type definitions"
Task: "T002 - Verify DashboardView tests pass"
Task: "T006 - Verify TimelineView tests pass"
```

---

## Implementation Strategy

### MVP First (User Story 1 Focus)

1. Complete Phase 1: Add Chart.js mock (T001)
2. Complete Phase 2: Verify DashboardView tests (T002)
3. **STOP and VALIDATE**: npm test -- --run shows 0 errors
4. Deploy/demo if DashboardTest fix is sufficient

### Incremental Delivery

1. Complete Phase 1: Chart.js mock → All tests no longer crash with Chart.js errors
2. Add Phase 2 (US1): Dashboard tests verified → SC-001 and SC-004 achieved
3. Add Phase 3 (US2): api.ts migration → SC-002 and SC-004 achieved (TypeScript consistency)
4. Add Phase 4 (US3): Timeline tests verified → SC-003 achieved
5. Add Phase 5 (Polish): Full quality gate verification

---

## Notes

- T001 (Chart.js mock) is CRITICAL - it fixes the root cause for both US1 and US3
- US2 (api.ts migration) is independent and can run in parallel with US1/US3 testing
- All user stories are independently testable
- Commit after each phase completion
- Stop at any checkpoint to validate independently

---

## Phase 6: Docker Authentication Bug Fix (Priority: P1)

**Goal**: Fix login endpoint returning empty reply in Docker environment

**Root Cause**: JWT_SECRET environment variable was not set in docker-compose.yaml

### Implementation

- [x] T010 [P1] Diagnose why /api/auth/login returns empty reply in Docker
- [x] T011 [P1] Add JWT_SECRET to backend service environment in docker-compose.yaml
- [x] T012 [P1] Rebuild Docker containers with JWT_SECRET configured
- [x] T013 [P1] Verify login works via curl to backend :8000
- [x] T014 [P1] Verify login works via Playwright browser test
- [x] T015 [P1] Verify /api/auth/me endpoint works with Bearer token
- [x] T016 [P1] Run frontend tests (8 passed) and backend tests (all passed)

### Key Findings

1. **Problem**: `jwtSecret()` in `backend/middleware/auth.go` calls `log.Fatal("JWT_SECRET environment variable is required")` when JWT_SECRET is not set. This happens BEFORE the request is processed, causing the server to return empty response (not even a proper error) for POST requests.

2. **Why GET /health worked**: The health endpoint doesn't use any JWT functionality - it's defined directly in main.go without middleware dependencies.

3. **Solution**: Added `JWT_SECRET=cenidim-dev-secret-2024` to backend service environment in docker-compose.yaml.

4. **Verification**:
   - Login endpoint returns valid JWT token and user data
   - /api/auth/me returns user info with valid token
   - Frontend login form works via Playwright
   - All 8 frontend tests pass
   - All backend tests pass

### Files Modified

- `docker-compose.yaml`: Added JWT_SECRET and GIN_MODE environment variables
- `backend/middleware/auth.go`: (no change, but now properly configured via env var)