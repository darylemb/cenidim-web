# Research: Data Quality & Visualization Fixes

**Feature**: 002-remaining-tasks
**Date**: 2026-05-24

## Decision 1: Word Cloud Library

**Choice**: `vue-wordcloud` (vue-cloudword) or custom Canvas implementation

**Rationale**: Vue 3 compatible word cloud libraries are limited. Options:
- `vue-wordcloud` - Vue 3 wrapper around d3-cloud, maintained
- Manual implementation using Canvas API + word-freq calculation

**Alternatives considered**:
- d3-cloud (original library) - requires Vue wrapper
- manual Canvas - more control but more code

**Recommendation**: Start with `vue-wordcloud` if available, fallback to manual Canvas

---

## Decision 2: Spanish Stop Words

**Choice**: Use common Spanish stop words list for filtering

**Rationale**: Need to filter articles (el, la, los, las), prepositions (de, en, a, con), conjunctions (y, o, u), common verbs (ser, estar, tener)

**Stop words to exclude**:
```
el, la, los, las, un, una,unos,unas
de, del, al
en, a, ante, bajo, con, contra, de, desde, entre, hacia, hasta, para, por, sin, sobre, tras
y, o, u, e
ser, estar, haber, tener, hacer, poder, querer, saber
es, son, está, están, fue, fueron, era, eran
lo, que, como, cuando, donde, quien
```

**Implementation**: Filter at word frequency calculation stage (backend), not in database

---

## Decision 3: Theme Classification (Rule-based)

**Choice**: Keyword-based classification with pattern matching

**Rationale**: Deterministic, auditable, reproducible without ML infrastructure

**Theme categories and keywords**:

| Theme | Keywords |
|-------|----------|
| Navidad | navidad, nochebuena, reyes, belén, villancico |
| Amor | amor, corazón, beso, querer, te amo, mi amor |
| Animal | gato, perro, pájaro, pez, león, animal |
| Escuela | escuela, maestro, aprender, libro, clase |
| Fiesta | fiesta, bailar, música, celebrate |
| Familia | mamá, papá, abuelito, hermano, familia |
| Miedo | miedo, susto, oscuro, fantasma |
| Naturaleza | sol, luna, estrella, mar, río, árbol |
| Tradicional | ronda, juego, jugar, amigos |

**Classification rules**:
1. Count keyword matches per theme
2. Assign highest-scoring theme
3. If no matches, assign "General"
4. Store theme string in songs table

**Note**: This replaces spaCy NER-based classification for themes only. Spanish type classification (ESPAÑOL_ESTANDAR, etc.) uses spaCy and is working correctly.

---

## Decision 4: Classification Verification

**Verification query**:
```sql
SELECT
  (SELECT COUNT(*) FROM songs) as total_songs,
  (SELECT COUNT(*) FROM song_stats WHERE classification = 'ESPAÑOL_ESTANDAR') as estandar,
  (SELECT COUNT(*) FROM song_stats WHERE classification = 'ESPAÑOL_REGIONAL') as regional,
  (SELECT COUNT(*) FROM song_stats WHERE classification = 'LENGUA_INDIGENA') as indigena,
  (SELECT COUNT(*) FROM song_stats WHERE classification IS NULL) as unclassified;
```

**Expected**: total = estandar + regional + indigena, unclassified = 0

---

## Decision 5: s/d Handling in Charts

**Problem**: Songs with "s/d" (sin datos) year appear in timeline charts as year "s/d" or "1111" (if converted)

**Solution**:
1. In backend `/api/stats`, filter out "s/d" year from timeline aggregation
2. In frontend DashboardView.vue, filter data points where year === "s/d"
3. Display "s/d" count separately if needed

**SQL to verify**:
```sql
SELECT COUNT(*) FROM songs WHERE year = 's/d' OR year = '1111';
```

---

## Decision 6: Playwright E2E Testing

**Choice**: Install `@playwright/test` as dev dependency

**Critical flows to test**:
1. Login flow (success + failure)
2. Navigation between pages
3. Search functionality
4. Dashboard rendering (charts load)
5. Admin panel access (authenticated)

**Constitution update**: Add "Playwright E2E tests must pass before merge" to Test-First Development principle

**CI Integration**: Add to GitHub Actions after npm install + npm run test:e2e

---

## Summary of Changes

1. **No new dependencies** for classification - reusing existing spaCy for Spanish types only
2. **Word cloud**: New Vue component + new API endpoint `/api/word-cloud`
3. **Theme classification**: Remove ML, use keyword rules in Python script
4. **Dashboard fixes**: Filter s/d in both backend and frontend
5. **Playwright**: New test suite + constitution update