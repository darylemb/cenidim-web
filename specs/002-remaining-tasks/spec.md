# Feature Specification: Data Quality & Visualization Fixes

**Feature Branch**: `002-remaining-tasks`
**Created**: 2026-05-24
**Status**: Draft
**Input**: "Verificar la correcta clasificación de tipos de español, crear nube de palabras, revisar tematica de canciones sin inferencia, corregir dashboards, y agregar playwright al constitution"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Verify Spanish Classification Accuracy (Priority: P1)

As a data analyst, I need the Spanish language classification of songs to be accurate so that I can trust the statistics shown in dashboards.

**Why this priority**: Classification errors cause incorrect reporting and decisions based on wrong data.

**Independent Test**: Run SQL query to sum classified songs and compare with total song count. All songs must be classified into exactly one category.

**Acceptance Scenarios**:

1. **Given** 367 songs in database, **When** querying classification counts, **Then** sum of (ESPAÑOL_ESTANDAR + ESPAÑOL_REGIONAL + LENGUA_INDIGENA) MUST equal 367
2. **Given** classified songs, **When** checking classification type field, **Then** each song MUST have exactly one classification (not null, not multiple)

---

### User Story 2 - Word Cloud Visualization (Priority: P2)

As a user, I want to see a word cloud of the most common words found in song lyrics so I can quickly understand the vocabulary used in the collection.

**Why this priority**: Provides visual insight into song content without reading all lyrics.

**Independent Test**: Access the dashboards page and verify word cloud renders with words from lyrics.

**Acceptance Scenarios**:

1. **Given** songs with lyrics in database, **When** visiting dashboards page, **Then** word cloud displays with words extracted from lyrics
2. **Given** word cloud component, **When** rendering, **Then** words are sized proportionally to their frequency
3. **Given** words extracted from lyrics, **When** processing, **Then** common stop words (the, a, el, la, etc.) are excluded from cloud

---

### User Story 3 - Song Theme Classification Without Inference (Priority: P3)

As a data manager, I need song thematic classification to be deterministic (based on rules, not statistical inference) so that classification can be explained and audited.

**Why this priority**: Inferential classification is opaque and cannot be audited or reproduced without the same ML model state.

**Independent Test**: Run classification on same database multiple times and verify identical results. Check that no spaCy or ML model is used for theme assignment.

**Acceptance Scenarios**:

1. **Given** song lyrics database, **When** classifying themes, **Then** results are deterministic (same input = same output)
2. **Given** song themes, **When** reviewing classification logic, **Then** I can explain classification as rule-based (keywords, patterns)
3. **Given** theme classification output, **When** querying, **Then** no ML model inference is required to reproduce results

---

### User Story 4 - Dashboard Data Corrections (Priority: P1)

As a dashboard viewer, I need accurate charts that exclude songs with missing data ("s/d") and correctly show song distribution by album so I can trust the visualizations.

**Why this priority**: Charts with missing data create misleading visual representation of the actual dataset.

**Independent Test**: Open dashboards and verify charts exclude s/d entries. Verify album song counts match actual database counts.

**Acceptance Scenarios**:

1. **Given** song data with "s/d" year entries, **When** rendering timeline chart, **Then** songs with "s/d" are excluded from year distribution
2. **Given** album song distribution chart, **When** checking counts, **Then** sum of songs per album equals total songs (excluding s/d albums)
3. **Given** song data, **When** calculating statistics, **Then** "s/d" entries are handled consistently (excluded from charts but counted in total)

---

### User Story 5 - Add Playwright E2E Testing to Constitution (Priority: P2)

As a developer, I want E2E UI testing with Playwright documented in the constitution so that testing practices are consistent and automated.

**Why this priority**: Constitution defines development standards. E2E testing ensures UI functionality across browsers.

**Independent Test**: Run `npm run test:e2e` and verify all critical user flows are tested.

**Acceptance Scenarios**:

1. **Given** Playwright installed, **When** running `npm run test:e2e`, **Then** all defined E2E tests execute against the application
2. **Given** CI pipeline, **When** running on push/PR, **Then** Playwright tests execute headless and pass
3. **Given** constitution.md, **When** reading development practices, **Then** Playwright E2E testing is documented as mandatory for UI validation

---

### Edge Cases

- What happens when a song has no lyrics? (Word cloud should still render with available data)
- What happens when all songs are "s/d" in a year? (Chart should show empty state, not error)
- What happens when classification totals don't match? (Must log discrepancy and report)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST verify Spanish classification counts sum to total song count with 0 discrepancy
- **FR-002**: System MUST display word cloud on dashboards using lyrics data with stop word filtering
- **FR-003**: System MUST use rule-based classification for song themes (no ML inference)
- **FR-004**: System MUST exclude "s/d" entries from timeline/year distribution charts
- **FR-005**: System MUST verify album song counts match actual database totals
- **FR-006**: Constitution MUST document Playwright as mandatory E2E testing tool
- **FR-007**: System MUST run lint, tests, and local CI pipeline after every speckit implement

### Key Entities

- **Song**: Has title, album reference, year (can be "s/d"), lyrics, classification type, theme
- **Album**: Has name, year, song count (must match actual songs)
- **Classification**: ESPAÑOL_ESTANDAR, ESPAÑOL_REGIONAL, or LENGUA_INDIGENA per song
- **Theme**: Deterministic category derived from lyrics via rules (not ML)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Classification verification query returns 0 discrepancy (sum = total)
- **SC-002**: Word cloud renders with minimum 50 most frequent words from lyrics
- **SC-003**: Theme classification is 100% reproducible (same database = same themes)
- **SC-004**: Dashboard charts show correct song counts (verified via SQL query)
- **SC-005**: `npm run test:e2e` passes with all critical user flows covered
- **SC-006**: Constitution includes Playwright testing requirement
- **SC-007**: Local CI (`./scripts/run_ci_local.sh`) executes successfully after every feature implementation

## Assumptions

- Word cloud will use client-side JavaScript library (vue-wordcloud or similar)
- Theme classification rules will be based on keyword matching (e.g., "navidad" → holiday theme)
- "s/d" represents "sin datos" (no data) and is a string value, not null
- Playwright tests will cover: login flow, navigation, search, dashboard rendering
- Classification verification will be done via direct SQLite query against database