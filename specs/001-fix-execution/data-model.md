# Data Model: Fix Execution Issues

## Overview

This feature does not introduce new data entities or modify existing data models. The changes are limited to:
- Test infrastructure fixes (mocking Chart.js in jsdom)
- TypeScript consistency for the API service layer

## Key Entities (No Changes)

No new entities introduced. The feature addresses:
1. **Test Configuration**: Mocking external dependencies (Chart.js) in test environment
2. **API Service Types**: Adding TypeScript type safety to existing api.js

## API Service Type Definitions

The api.ts (migration target) provides types for:

```typescript
interface SearchParams {
  query: string;
  field: string;
  page: number;
  limit: number;
  clasificacion?: string;
  orderBy?: string;
  orderDir?: string;
}

interface SearchResult {
  results: Song[];
  total: number;
}

interface Song {
  id: number;
  titulo: string;
  artista: string;
  album: string;
  año: number;
  clasificacion?: string;
}

interface Stats {
  totalSongs: number;
  totalAlbums: number;
  totalArtists: number;
  // ... other stats fields
}
```

## State Transitions

No state transitions affected. Tests handle component lifecycle (mount/unmount) only.

## Validation Rules

No new validation rules introduced. Existing API validation remains unchanged.