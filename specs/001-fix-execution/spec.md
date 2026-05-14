# Feature Specification: Fix Execution Issues

**Feature Branch**: `001-fix-execution`
**Created**: 2026-05-13
**Status**: Draft
**Input**: User description: "fix execution issues"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fix Dashboard Test Failures (Priority: P1)

Dashboard view tests fail with Chart.js errors in jsdom environment. When tests run, unhandled rejections occur in `src/views/__tests__/DashboardView.test.ts` due to Chart.js calling `getComputedStyle` on detached DOM elements.

**Why this priority**: Tests must pass for CI to succeed and to ensure reliable quality gates per constitution.

**Independent Test**: Can be fully tested by running `npm test -- --run` and verifying all 8 tests pass with no errors.

**Acceptance Scenarios**:

1. **Given** DashboardView has chart components, **When** tests run in jsdom environment, **Then** no unhandled promise rejections should occur
2. **Given** Chart.js components are rendered, **When** the DOM is cleaned up, **Then** Chart instances should be properly destroyed before detach
3. **Given** KPI cards display statistics, **When** the component mounts, **Then** charts should initialize without errors

---

### User Story 2 - Fix API Service TypeScript Inconsistency (Priority: P2)

The project uses TypeScript but `src/services/api.js` is plain JavaScript with no type safety. This creates inconsistency and potential runtime errors.

**Why this priority**: TypeScript strict mode is enabled per constitution; inconsistent typing weakens type safety.

**Independent Test**: Can be fully tested by running `npm run build` and verifying `vue-tsc --noEmit` passes with no errors.

**Acceptance Scenarios**:

1. **Given** the frontend uses TypeScript strict mode, **When** api.js is imported, **Then** it should provide proper type definitions
2. **Given** api.js exists alongside api.ts potential exports, **When** build runs, **Then** there should be no duplicate export conflicts

---

### User Story 3 - Fix Timeline View Test Errors (Priority: P3)

TimelineView tests have similar Chart.js errors as DashboardView.

**Why this priority**: All tests should pass cleanly to meet constitution quality gates.

**Independent Test**: Can be fully tested by running `npm test -- --run` and verifying TimelineView tests complete without unhandled rejections.

**Acceptance Scenarios**:

1. **Given** TimelineView contains chart components, **When** tests run, **Then** no DOM-related errors should occur
2. **Given** TimelineView renders timeline visualization, **When** component unmounts, **Then** Chart.js instances should be destroyed cleanly

---

### Edge Cases

- What happens when Chart.js is loaded in a non-browser environment? Should use chart.js auto-detect or explicit platform fallback
- How does the system handle multiple chart instances being created and destroyed rapidly?
- What happens when API calls fail during test runs?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST fix unhandled promise rejections in DashboardView tests
- **FR-002**: System MUST fix Chart.js initialization errors in jsdom test environment
- **FR-003**: System MUST ensure all frontend tests pass with zero errors
- **FR-004**: System MUST maintain TypeScript consistency for api.js if it remains JavaScript
- **FR-005**: System MUST ensure vue-tsc --noEmit passes without type errors

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `npm test -- --run` completes with 0 errors (all 8 tests pass cleanly)
- **SC-002**: `npm run build` completes successfully with no type errors
- **SC-003**: `npm run lint` passes with no warnings on affected files
- **SC-004**: DashboardView and TimelineView tests complete without unhandled promise rejections

## Assumptions

- The Chart.js errors are due to jsdom not supporting certain DOM APIs that Chart.js expects in a browser environment
- The fix involves properly destroying Chart instances before DOM cleanup or mocking Chart.js in tests
- api.js was created before the TypeScript migration and should either be converted to api.ts or have proper type declarations