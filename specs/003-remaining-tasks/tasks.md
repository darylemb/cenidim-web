# Tasks: Dashboard Improvements and Docker Security

**Input**: Design documents from `/specs/003-remaining-tasks/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing project structure and prepare for changes

- [x] T001 [P] Verify Go module structure in `backend/go.mod`
- [x] T002 [P] Verify Vue project structure in `frontend/package.json`
- [x] T003 Verify Trivy availability in CI environment

---

## Phase 2: Foundational (Critical Data Fixes)

**Purpose**: Fix critical bugs before user story implementation

**⚠️ CRITICAL**: These fixes are prerequisites for accurate testing

### Backend Data Fixes

- [x] T004 [P] Fix `letra` → `lyrics` column name in `backend/handlers/stats.go:181`
- [x] T005 Add `avg_lyrics_length` field to `StatsResponse` struct in `backend/handlers/stats.go`
- [x] T006 Add `songs_with_lyrics` field to `StatsResponse` struct in `backend/handlers/stats.go`
- [x] T007 Add `songs_by_oov_level` field to `StatsResponse` struct in `backend/handlers/stats.go`
- [x] T008 Add `songs_by_indigena` field to `StatsResponse` struct in `backend/handlers/stats.go`
- [x] T009 Add `songs_without_year` field to `StatsResponse` struct in `backend/handlers/stats.go`
- [x] T010 [P] Add SQL queries for new stats fields in `backend/handlers/stats.go`
- [x] T011 [P] Update `StatsResponse` JSON tags to match frontend expectations
- [x] T012 Add `songs_by_oov_level` query (JOIN with song_stats table) in `backend/handlers/stats.go`
- [x] T013 Add `songs_by_indigena` query (from song_stats table) in `backend/handlers/stats.go`
- [x] T014 Verify `backend/models/song.go` has `Tema` field for theme classification
- [x] T015 [P] Run `go build ./...` to verify backend compiles
- [x] T016 Run database queries to verify stats match expected values

**Checkpoint**: All stats data must be accurate before frontend work

---

## Phase 3: User Story 1 - Interactive Timeline with Animation (Priority: P1)

**Goal**: Redesign timeline chart with animation and interactivity

**Independent Test**: Load dashboard and verify timeline responds to hover/click with smooth animations

### Implementation for User Story 1

- [x] T017 [P] [US1] Update Chart.js animation config in `frontend/src/views/DashboardView.vue`
- [x] T018 [P] [US1] Add hover tooltip with animated transition for year data points
- [x] T019 [P] [US1] Add click handler to highlight selected year with animation
- [x] T020 [US1] Verify timeline excludes "s/d" year entries (already fixed in backend)
- [x] T021 [US1] Test timeline animation on initial page load
- [x] T022 [US1] Verify tooltip shows year and song count on hover

**Checkpoint**: Timeline animates smoothly and responds to interactions within 200ms

---

## Phase 4: User Story 2 - Accurate Analytics Data (Priority: P1)

**Goal**: Ensure all KPI values match database queries exactly

**Independent Test**: Compare displayed values against direct SQL queries

### Implementation for User Story 2

- [x] T023 [P] [US2] Verify `frontend/src/types/index.ts` Stats interface matches backend response
- [x] T024 [P] [US2] Update DashboardView.vue to use new stats fields (avg_lyrics_length, songs_with_lyrics)
- [x] T025 [US2] Remove fake placeholder data from OOV chart (use real data or "No data" state)
- [x] T026 [US2] Verify total songs KPI matches `SELECT COUNT(*) FROM songs`
- [x] T027 [US2] Verify total albums KPI matches `SELECT COUNT(*) FROM fonogramas`
- [x] T028 [US2] Verify songs_by_year data sum equals total songs (excluding s/d)
- [x] T029 [US2] Verify songs_by_clasificacion data matches GROUP BY query
- [x] T030 [US2] Run Playwright test to verify KPI accuracy

**Checkpoint**: All displayed values match database queries (100% accuracy)

---

## Phase 5: User Story 3 - Docker Image Security Scanning (Priority: P2)

**Goal**: Add Trivy vulnerability scanning after Docker builds

**Independent Test**: Run `speckit implement` and verify Trivy scan executes with report generated

### Implementation for User Story 3

- [x] T031 [P] [US3] Add Trivy installation and scan step to CI workflow in `.github/workflows/ci.yml`
- [x] T032 [P] [US3] Configure Trivy to scan HIGH,CRITICAL vulnerabilities
- [x] T033 [US3] Add SARIF report upload as build artifact with 30-day retention
- [x] T034 [US3] Verify CI fails when critical vulnerabilities found (simulate test)

**Checkpoint**: Trivy scans run automatically and fail CI on critical vulnerabilities

---

## Phase 6: User Story 4 - Separate Section for Songs with Missing Year (Priority: P1)

**Goal**: Show count of songs with "s/d" year in separate indicator

**Independent Test**: Query songs with year="s/d" and verify dashboard shows same count

### Implementation for User Story 4

- [x] T038 [P] [US4] Add `songs_without_year` to StatsResponse in `backend/handlers/stats.go`
- [x] T039 [P] [US4] Add query to count songs with year="s/d" or empty/null year
- [x] T040 [US4] Create "Songs without year data" indicator widget in `frontend/src/views/DashboardView.vue`
- [x] T041 [US4] Style indicator to show count prominently
- [x] T042 [US4] Verify indicator shows correct count from database
- [ ] T043 [US4] Add breakdown capability showing which albums contain s/d songs (optional enhancement)

**Checkpoint**: Dashboard displays accurate count of songs with missing year data

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and improvements

- [x] T044 [P] Run `npm run lint` and fix any linting errors in frontend
- [x] T045 [P] Run `go build ./...` to verify backend still compiles
- [x] T046 Run `npm run build` to verify frontend builds successfully
- [x] T047 [P] Update WordCloud.vue to work with fixed backend (lyrics column fix)
- [x] T048 Verify all 4 user stories work independently
- [x] T049 Run full Playwright test suite to verify integration
- [x] T050 Update AGENTS.md to point to new feature plan

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Critical data fixes - BLOCKS all user stories
- **User Stories (Phase 3-6)**: Can proceed in parallel after Foundational
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Phase 2 completion - Timeline visualization
- **US2 (P1)**: Depends on Phase 2 completion - Analytics accuracy
- **US3 (P2)**: Depends on Phase 2 completion - Trivy integration
- **US4 (P1)**: Depends on Phase 2 completion - s/d indicator

### Parallel Opportunities

- T001, T002, T003 can run in parallel (different parts of stack)
- T004-T016 can run in parallel (independent files)
- T017-T019 can run in parallel (US1 frontend components)
- T023-T024 can run in parallel (US2 frontend components)
- T031-T032 can run in parallel (CI setup)
- T038-T039 can run in parallel (backend queries for US4)
- T044-T047 can run in parallel (final verification)

---

## Independent Test Criteria

| User Story | Test |
|------------|------|
| US1 | Timeline animates on load, hover shows tooltip, click highlights year |
| US2 | All KPIs match `SELECT` queries from quickstart.md |
| US3 | `docker build` triggers Trivy scan, report generated, CI fails on CRITICAL |
| US4 | Songs without year indicator shows `SELECT COUNT(*) WHERE year='s/d'` |

---

## Implementation Strategy

### MVP First (US1 + US2 + US4)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational data fixes
3. Complete Phase 3: US1 Interactive Timeline
4. Complete Phase 4: US2 Accurate Analytics
5. **STOP and VALIDATE**: Deploy/demo if ready
6. Complete Phase 6: US4 s/d Indicator
7. Deploy complete feature set

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 → Timeline animation (deploy/demo)
3. US2 → Accurate data (deploy/demo)
4. US4 → s/d indicator (deploy/demo)
5. US3 → Trivy scanning (separate PR, more risk)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US1, US2, US4 are P1 (MVP critical)
- US3 is P2 (DevOps, can follow after MVP)
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently