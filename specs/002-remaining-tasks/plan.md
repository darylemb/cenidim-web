# Implementation Plan: Data Quality & Visualization Fixes

**Branch**: `002-remaining-tasks` | **Date**: 2026-05-24 | **Spec**: [link](./spec.md)
**Input**: Feature specification from `/specs/002-remaining-tasks/spec.md`

## Summary

Fix data quality issues and add visualization features:
1. Verify Spanish classification counts match total songs
2. Create word cloud visualization for lyrics
3. Implement rule-based theme classification (no ML inference)
4. Fix dashboard charts to exclude "s/d" entries and verify album counts
5. Add Playwright E2E testing to constitution

## Technical Context

**Language/Version**: Go 1.21+ (backend), Node 24 (frontend), TypeScript (frontend)
**Primary Dependencies**: Gin (backend), Vue 3 + Vite (frontend), Chart.js/vue-chartjs (charts), spaCy (classification only - will remove for themes)
**Storage**: SQLite (`letras.db`)
**Testing**: Go tests (`go test ./...`), Vitest (`npm test`), Playwright (E2E - to be added)
**Target Platform**: Linux server (Docker), Web browser (frontend)
**Performance Goals**: Dashboard loads in <2s, word cloud renders in <3s
**Constraints**: Theme classification must be deterministic (no ML inference)
**Scale/Scope**: 367 songs, 280 albums, ~5.4MB timeline data

## Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| Test-First Development | ⚠️ | Need to add Playwright E2E tests |
| API-First Design | ✅ | API endpoints exist for data |
| Security by Design | ✅ | JWT auth working, roles enforced |
| Operational Observability | ✅ | Health checks in place |
| Continuous Delivery | ⚠️ | Need to add Playwright to CI |

**Violations to justify**: None

## Project Structure

### Documentation (this feature)

```text
specs/002-remaining-tasks/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (if needed)
└── checklists/           # Quality checklists
    └── requirements.md
```

### Source Code (repository root)

```text
backend/
├── main.go
├── handlers/           # API handlers
├── models/             # Data models
├── database/           # DB connection
├── scripts/
│   └── classify_songs.py  # Classification logic (MODIFY: remove ML for themes)
└── lyrics_classifier/     # EXISTING - spaCy classification (KEEP for Spanish types)

frontend/
├── src/
│   ├── views/
│   │   └── DashboardView.vue  # MODIFY: add word cloud, fix s/d charts
│   ├── components/
│   │   └── WordCloud.vue      # NEW: word cloud component
│   └── services/
│       └── api.ts             # API calls
└── tests/
    └── e2e/                   # NEW: Playwright tests
```

**Structure Decision**: Web application with Go backend + Vue frontend. Word cloud is a frontend component. Classification verification is a data integrity check.

## Phase 0: Research

### Unknowns to Research

1. **Word cloud library**: Best Vue 3 compatible word cloud library?
   - vue-wordcloud vs manual canvas implementation
   - License considerations

2. **Stop word list**: Spanish stop words for filtering lyrics
   - Common Spanish articles, prepositions, conjunctions

3. **Theme classification rules**: How to classify themes without ML?
   - Keyword-based rules (e.g., "navidad" → Christmas)
   - Pattern matching for common themes

### Research Tasks

- Task 1: Research Vue 3 word cloud components (vue-wordcloud, d3-cloud, etc.)
- Task 2: Identify Spanish stop words to exclude from word cloud
- Task 3: Define theme classification keywords/patterns
- Task 4: Verify classification counts via SQL query

### Consolidation

Research findings will be documented in `research.md`

## Phase 1: Design & Contracts

### Data Model

**Entities**:
- **Song**: id, title, album_id, year, lyrics, classification_type (ESPAÑOL_ESTANDAR/ESPAÑOL_REGIONAL/LENGUA_INDIGENA), theme
- **Album**: id, clave, titulo, interprete, year, pais, editora, song_count
- **Classification**: song_id, type (enum), confidence (not used for themes)

### Interface Contracts

No external API changes needed. Frontend will consume existing `/api/stats` endpoint with potential new fields for word cloud data.

### Quickstart

```bash
# Verify classification counts
sqlite3 backend/letras.db "SELECT COUNT(*) FROM songs; SELECT COUNT(*) FROM song_stats WHERE classification IS NOT NULL;"

# Run local CI
./scripts/run_ci_local.sh
```

## Implementation Phases

### Phase 1: Classification Verification
- Write SQL query to verify song count matches classification sum
- Run query against database
- Document any discrepancies

### Phase 2: Word Cloud
- Research and select Vue word cloud library
- Create WordCloud.vue component
- Add endpoint `/api/word-cloud` to serve word frequency data
- Integrate into DashboardView

### Phase 3: Theme Classification (Rule-based)
- Remove spaCy ML dependency for themes
- Implement keyword-based theme classification
- Update classify_songs.py script
- Re-run classification on database

### Phase 4: Dashboard Fixes
- Fix timeline chart to exclude "s/d" entries
- Fix album distribution to show correct counts
- Verify counts match actual database

### Phase 5: Playwright Testing
- Install Playwright
- Write E2E tests for critical flows (login, navigation, dashboard)
- Add to constitution.md
- Add to CI pipeline