# Implementation Plan: Dashboard Improvements and Docker Security

**Branch**: `003-remaining-tasks` | **Date**: 2026-05-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-remaining-tasks/spec.md`

## Summary

Rediseñar el dashboard con: (1) línea de tiempo interactiva y animada que excluya canciones "s/d" y las muestre en sección separada, (2) corregir los datos analíticos que no coinciden con la base de datos, (3) agregar escaneo de imágenes Docker con Trivy después de cada implementación.

## Technical Context

**Language/Version**: Go 1.21+ (backend), Vue 3 + TypeScript (frontend)**
**Primary Dependencies**: Gin framework, vue-chartjs, Chart.js, Playwright, Trivy
**Storage**: SQLite database (`letras.db`)
**Testing**: Go tests (`go test ./...`), Vitest (`npm run test`), Playwright E2E
**Target Platform**: Linux server (Docker container)
**Project Type**: Web application (backend API + frontend SPA)
**Performance Goals**: Timeline animation <2s, interactions <200ms
**Constraints**: Exclude "s/d" year entries from timeline, 100% accuracy for KPI values
**Scale/Scope**: ~4000 songs, ~280 albums

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Test-First Development | ⚠️ GATE | Must add backend tests for new stats queries |
| API-First Design | ✓ PASS | All stats via `/api/stats` endpoint |
| Security by Design | ✓ PASS | Trivy scanning adds vulnerability detection |
| Operational Observability | ✓ PASS | Health checks already exist |
| Continuous Delivery | ✓ PASS | Trivy integration in CI |

## Project Structure

### Documentation (this feature)

```text
specs/003-remaining-tasks/
├── plan.md              # This file
├── research.md          # Phase 0 output (data issues found)
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── handlers/
│   └── stats.go         # MODIFY: Fix data issues, add missing stats
├── models/
│   └── song.go          # MODIFY: Already has `tema` field added
├── cmd/build-db/
│   └── main.go          # VERIFY: Schema correct
└── tests/
    └── stats_test.go    # ADD: Tests for new stats queries

frontend/
├── src/
│   ├── views/
│   │   └── DashboardView.vue   # MODIFY: Timeline animation, s/d handling
│   ├── components/
│   │   └── WordCloud.vue       # VERIFY: Works with fixed backend
│   └── types/
│       └── index.ts            # VERIFY: Stats interface correct
└── tests/
    └── e2e/
        └── app.spec.ts        # ADD: Dashboard E2E tests

.github/workflows/
└── ci.yml             # MODIFY: Add Trivy scanning step

docker-compose.yaml    # VERIFY: Trivy available in CI
```

**Structure Decision**: Web application with separate backend (Go/Gin) and frontend (Vue 3/Vite). Stats are exposed via REST API at `/api/stats` and `/api/word-cloud`.

## Complexity Tracking

> Not applicable - no constitutional violations

## Phase 0: Research Findings

### Critical Data Issues Found

| # | Issue | Severity | File | Fix Required |
|---|-------|----------|------|--------------|
| 1 | `letra` vs `lyrics` column name bug | **CRITICAL** | `stats.go:181` | Change `letra` to `lyrics` in query |
| 2 | Missing `avg_lyrics_length` field | HIGH | `stats.go` | Add AVG(LENGTH(lyrics)) query |
| 3 | Missing `songs_with_lyrics` field | HIGH | `stats.go` | Add COUNT query for non-empty lyrics |
| 4 | Missing `songs_by_oov_level` field | MEDIUM | `stats.go` | Add JOIN with song_stats table |
| 5 | Missing `songs_by_indigena` field | MEDIUM | `stats.go` | Add query from song_stats table |

### Database Schema (Verified)

**`songs` table columns:**
- `id`, `fonograma_id`, `title`, `filename`, `lyrics`, `clasificacion`, `tema`, `created_at`

**`song_stats` table (created by classify_songs.py):**
- `song_id`, `pct_oov`, `categoria`, `contiene_indigena`, `n_tokens`

**`fonogramas` table columns:**
- `clave_fonograma`, `titulo`, `subtitulo`, `interprete_principal`, `anio`, etc.

## Phase 1: Design

### Changes Required

#### Backend (handlers/stats.go)

1. **Fix GetWordCloud query** - Change `letra` to `lyrics`
2. **Add GetStats fields** - `avg_lyrics_length`, `songs_with_lyrics`, `songs_by_oov_level`, `songs_by_indigena`
3. **Fix year query** - Already has s/d exclusion (verified working)

#### Frontend (DashboardView.vue)

1. **Timeline chart** - Add animation (Chart.js animation config), hover/click interactions
2. **Separate s/d indicator** - Show count of songs with year="s/d" in separate widget
3. **Remove fake placeholder data** - Use real data or show "No data" state

#### CI/CD (GitHub Actions + Trivy)

1. **Add Trivy scan step** - Run after Docker image is built
2. **Fail on critical vulnerabilities** - CVSS >= 7.0
3. **Archive reports** - Store as build artifacts for 30 days