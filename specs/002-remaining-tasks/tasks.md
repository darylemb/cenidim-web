# Tasks: Data Quality & Visualization Fixes

**Input**: Design documents from `/specs/002-remaining-tasks/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/` (Go API), `frontend/src/` (Vue app)
- Backend handlers: `backend/handlers/`
- Frontend views: `frontend/src/views/`
- Frontend components: `frontend/src/components/`

---

## Phase 1: Classification Verification (US1)

**Goal**: Verify Spanish classification counts match total songs without discrepancy

**Independent Test**: `sqlite3 backend/letras.db "SELECT COUNT(*) FROM songs; SELECT COUNT(*) FROM song_stats;"`

**RESULTS**:
- Total songs: 3858
- ESPAÑOL_ESTANDAR: 3491
- ESPAÑOL_REGIONAL: 365
- LENGUA_INDIGENA: 2
- Total classified: 3491 + 365 + 2 = 3858 ✓ **MATCHES**

- [x] T001 [US1] Run classification verification query in `backend/letras.db`
- [x] T002 [US1] Document classification count discrepancy (if any) in checklist
- [x] T003 [US1] If discrepancy found: identify missing classifications and fix (NO DISCREPANCY FOUND)

---

## Phase 2: Word Cloud Visualization (US2)

**Goal**: Display word cloud on dashboards showing most frequent words from lyrics

**Independent Test**: Access `http://localhost/dashboards` and verify word cloud renders

### Implementation

- [ ] T004 [P] Research Vue 3 word cloud library (vue-wordcloud vs manual Canvas)
- [ ] T005 [US2] Install word cloud package in `frontend/` (`npm install vue-wordcloud --legacy-peer-deps`)
- [ ] T006 [US2] Create `frontend/src/components/WordCloud.vue` component
- [ ] T007 [US2] Define Spanish stop words list for filtering in `frontend/src/components/WordCloud.vue`
- [ ] T008 [P] [US2] Add `/api/word-cloud` endpoint in `backend/handlers/stats.go` to serve word frequency data
- [ ] T009 [US2] Extract word frequencies from lyrics in backend, excluding stop words
- [ ] T010 [US2] Integrate WordCloud component into `frontend/src/views/DashboardView.vue`

---

## Phase 3: Song Theme Classification Without Inference (US3)

**Goal**: Implement rule-based theme classification using keywords (no ML inference)

**Independent Test**: Run classification twice on same database, results must be identical

### Implementation

- [ ] T011 [P] [US3] Define theme keywords mapping in `scripts/classify_songs.py` (NAVIDAD, AMOR, ANIMALES, etc.)
- [ ] T012 [US3] Implement keyword-based theme classification function in `scripts/classify_songs.py`
- [ ] T013 [US3] Add `tema` column to songs table via ALTER TABLE in `backend/cmd/build-db/main.go`
- [ ] T014 [US3] Run theme classification on database and verify determinism
- [ ] T015 [US3] Document that no spaCy or ML inference is used for theme classification

---

## Phase 4: Dashboard Data Corrections (US4)

**Goal**: Fix dashboard charts to exclude "s/d" entries and verify album song counts

**Independent Test**: Verify SQL query counts match chart data

### Implementation

- [ ] T016 [P] [US4] Query songs with year="s/d" in `backend/letras.db`
- [ ] T017 [US4] Modify `/api/stats` handler in `backend/handlers/stats.go` to exclude "s/d" from year distribution
- [ ] T018 [US4] Update `frontend/src/views/DashboardView.vue` timeline chart to filter year === "s/d"
- [ ] T019 [US4] Verify album song counts via SQL match actual distribution
- [ ] T020 [US4] Update chart labels to show "(s/d)" count separately if significant

---

## Phase 5: Playwright E2E Testing (US5)

**Goal**: Add Playwright E2E testing and document in constitution

**Independent Test**: `cd frontend && npx playwright test`

### Implementation

- [ ] T021 [P] [US5] Install Playwright in `frontend/` (`npm install @playwright/test --legacy-peer-deps`)
- [ ] T022 [US5] Install Chromium browser (`npx playwright install chromium`)
- [ ] T023 [P] [US5] Create `frontend/tests/e2e/` directory structure
- [ ] T024 [US5] Write E2E test for login flow in `frontend/tests/e2e/login.spec.ts`
- [ ] T025 [US5] Write E2E test for navigation in `frontend/tests/e2e/navigation.spec.ts`
- [ ] T026 [US5] Write E2E test for dashboard rendering in `frontend/tests/e2e/dashboard.spec.ts`
- [ ] T027 [US5] Add `test:e2e` script to `frontend/package.json`
- [ ] T028 [US5] Update `.specify/memory/constitution.md` to include Playwright E2E testing requirement
- [ ] T029 [US5] Verify E2E tests pass with `npm run test:e2e`

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final verification and documentation

- [ ] T030 Run `./scripts/run_ci_local.sh` to verify all checks pass
- [ ] T031 [P] Update `frontend/package-lock.json` after npm installs
- [ ] T032 Verify all 5 user story independent tests pass
- [ ] T033 Update `specs/002-remaining-tasks/tasks.md` with completed checkpoints

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (US1)**: Independent - no dependencies on other phases
- **Phase 2 (US2)**: Depends on Phase 1 completion (can verify classification first)
- **Phase 3 (US3)**: Independent - can run in parallel with Phase 2
- **Phase 4 (US4)**: Depends on Phase 1 - needs classification verified
- **Phase 5 (US5)**: Independent - can run in parallel with any phase
- **Phase 6 (Polish)**: Depends on all phases complete

### User Story Dependencies

- **US1 (P1)**: No dependencies - start here
- **US2 (P2)**: Can start after US1 verification, runs parallel with US3, US4, US5
- **US3 (P3)**: Independent - runs parallel with US2, US4, US5
- **US4 (P1)**: Depends on US1 (needs classification working)
- **US5 (P2)**: Independent - runs parallel with all

### Parallel Opportunities

- US2 and US3 can run in parallel (different files: WordCloud.vue vs classify_songs.py)
- US5 (Playwright tests) can run parallel with all other phases
- T004, T011 can run in parallel (research tasks)

---

## Implementation Strategy

### MVP First (US1 + US4)

1. Complete Phase 1: Classification verification
2. Complete Phase 4: Dashboard fixes
3. **STOP and VALIDATE**: Classification counts verified, dashboards show correct data

### Incremental Delivery

1. Phase 1 (US1) → Classification counts verified
2. Phase 4 (US4) → Dashboard data correct
3. Phase 2 (US2) → Word cloud added to dashboards
4. Phase 3 (US3) → Theme classification rule-based
5. Phase 5 (US5) → Playwright E2E testing in place

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Stop at any checkpoint to validate story independently
- Classification and dashboard fixes (US1, US4) are data integrity - fix first