# Implementation Plan: Fix Execution Issues

**Branch**: `001-fix-execution` | **Date**: 2026-05-13 | **Spec**: [link](../spec.md)
**Input**: Feature specification from `/specs/001-fix-execution/spec.md`

## Summary

Fix execution issues in the frontend test suite and TypeScript consistency. The primary problem is Chart.js throwing unhandled promise rejections in jsdom environment during tests, and a secondary issue is the api.js file being plain JavaScript in a TypeScript project.

## Technical Context

**Language/Version**: TypeScript 5.x (Vue 3 + Vite + Vitest)
**Primary Dependencies**: vue-chartjs, chart.js, vitest, @vue/test-utils
**Storage**: N/A (no database changes)
**Testing**: Vitest with @vue/test-utils and jsdom environment
**Target Platform**: Web browser (frontend)
**Project Type**: Vue 3 web application with TypeScript strict mode
**Performance Goals**: N/A (bug fix, not performance work)
**Constraints**: Must not break existing functionality; must pass all quality gates
**Scale/Scope**: Small scope - test fixes and type consistency across ~4 test files and 1 service file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ COMPLIANT | Fixing tests to pass; tests define the acceptance criteria |
| II. API-First Design | ✅ N/A | No API changes |
| III. Security by Design | ✅ N/A | No security changes |
| IV. Operational Observability | ✅ N/A | No observability changes |
| V. Continuous Delivery | ⚠️ VIOLATION | CI blocks on test errors; must fix |

**Gate Result**: Phase 0 can proceed. Constitution V (Continuous Delivery) is blocked by failing tests - fixing this is the core purpose of this feature.

## Project Structure

### Documentation (this feature)

```text
specs/001-fix-execution/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (N/A - internal only)
└── tasks.md             # Phase 2 output (/speckit.tasks - not this command)
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── services/
│   │   ├── api.ts          # Will replace api.js
│   │   └── api.js          # To be removed after migration
│   ├── views/
│   │   ├── __tests__/
│   │   │   ├── DashboardView.test.ts
│   │   │   ├── TimelineView.test.ts
│   │   │   ├── AuthPage.test.ts
│   │   │   └── CancionesView.test.ts
│   │   ├── DashboardView.vue
│   │   └── TimelineView.vue
│   └── components/
│       └── Chart components using vue-chartjs
└── test/
    └── setup.ts            # Vitest setup with jsdom
```

**Structure Decision**: Web application (Option 2) - Vue 3 frontend with backend API. Changes are confined to frontend test fixes and TypeScript migration for api service.

## Complexity Tracking

No complexity deviations. Simple bug fixes within existing architecture.

## Phase 0: Research

See `research.md` for detailed findings on Chart.js jsdom mocking and api.js TypeScript migration strategy.

## Phase 1: Design & Contracts

See `data-model.md` and `quickstart.md` for type definitions and implementation guidance.

## Post-Phase 1 Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | ✅ COMPLIANT | Tests will pass after fix |
| V. Continuous Delivery | ✅ FIXED | Test errors resolved |

**Re-check Result**: All gates pass. Ready for `/speckit.tasks`.