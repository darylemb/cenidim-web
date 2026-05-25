# Quickstart: Fix Execution Issues

## Overview

This feature fixes test failures in the frontend and ensures TypeScript consistency for the API service.

## Prerequisites

- Node 24+
- npm

## Commands

### Run Tests

```bash
cd frontend
npm test -- --run
```

**Expected outcome**: 8 tests pass with 0 errors

### Build Frontend

```bash
cd frontend
npm run build
```

**Expected outcome**: Successful build with no type errors

### Lint Frontend

```bash
cd frontend
npm run lint
```

**Expected outcome**: No warnings or errors

## Files to Modify

1. **`frontend/src/test/setup.ts`** - Add Chart.js mock
2. **`frontend/src/services/api.js`** → **`api.ts`** - Convert to TypeScript
3. **`frontend/src/views/__tests__/DashboardView.test.ts`** - Verify fix
4. **`frontend/src/views/__tests__/TimelineView.test.ts`** - Verify fix

## Verification

After implementing fixes:

1. Run `npm test -- --run` - should show 4 test files, 8 tests, 0 errors
2. Run `npm run build` - should complete without type errors
3. Run `npm run lint` - should pass cleanly