# Feature Specification: Dashboard Improvements and Docker Security

**Feature Branch**: `[003-remaining-tasks]`
**Created**: 2026-05-24
**Status**: Draft
**Input**: User description: "Rediseña la linea de tiempo para que tenga mas animacion y sea mas interactiva, las cancions s/d ocultarlas de la linea del tiempo y ponerlas en una seccion aparte. 2. revisar los datos analiticos, tanto la informacion que trae de la base de datos como la que se muestra ya que parece que la mayoria estan mal. 3. Construye y escanea las docker images generadas cada vez que termine un speckit implement con trivy."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Interactive Timeline with Animation (Priority: P1)

As a dashboard user, I want a timeline chart that is visually engaging and responds to my interactions so I can explore song trends over time.

**Why this priority**: Timeline is a key visualization component. Current implementation lacks interactivity and visual appeal.

**Independent Test**: Can be tested by loading the dashboard and verifying the timeline responds to hover/click events with smooth animations.

**Acceptance Scenarios**:

1. **Given** the dashboard is loaded, **When** I hover over a data point on the timeline, **Then** I see an animated tooltip showing the year and song count
2. **Given** the dashboard is loaded, **When** I click on a data point, **Then** the chart highlights that year and shows details with animation
3. **Given** the timeline is displayed, **When** the page loads, **Then** the chart animates into view (draws progressively)
4. **Given** songs with "s/d" (sin dato) year exist, **When** the timeline renders, **Then** these songs are NOT shown in the main timeline but appear in a separate indicator/widget

---

### User Story 2 - Accurate Analytics Data (Priority: P1)

As a dashboard user, I want accurate statistics so I can trust the data shown and make informed decisions.

**Why this priority**: Analytics with incorrect data provides no value and may lead to wrong conclusions.

**Independent Test**: Can be tested by comparing dashboard displayed values against direct database queries for the same metrics.

**Acceptance Scenarios**:

1. **Given** songs exist in the database, **When** I view the total songs KPI, **Then** the displayed number matches `SELECT COUNT(*) FROM songs`
2. **Given** albums exist in the database, **When** I view the total albums KPI, **Then** the displayed number matches `SELECT COUNT(*) FROM fonogramas`
3. **Given** classified songs exist, **When** I view the classification breakdown, **Then** each category count matches `SELECT clasificacion, COUNT(*) FROM songs GROUP BY clasificacion`
4. **Given** songs with years exist, **When** I view the year distribution chart, **Then** the sum of all years equals total songs (excluding s/d)
5. **Given** songs with OOV levels exist, **When** I view the OOV chart, **Then** the data matches `SELECT oov_level, COUNT(*) FROM songs GROUP BY oov_level`

---

### User Story 3 - Docker Image Security Scanning (Priority: P2)

As a DevOps engineer, I want Docker images scanned for vulnerabilities after each implementation so we can maintain security compliance.

**Why this priority**: Security vulnerabilities in containers can expose the entire system. Scanning after each implementation ensures early detection.

**Independent Test**: Can be tested by running `speckit implement` and verifying Trivy scan executes and produces a report.

**Acceptance Scenarios**:

1. **Given** a `speckit implement` command completes, **When** the Docker image is built, **Then** Trivy scans the image for vulnerabilities
2. **Given** Trivy completes a scan, **When** vulnerabilities are found, **Then** a report is generated and CI fails if critical vulnerabilities exist
3. **Given** Trivy completes a scan, **When** no critical vulnerabilities are found, **Then** the build succeeds and report is archived

---

### User Story 4 - Separate Section for Songs with Missing Year (Priority: P1)

As a dashboard user, I want to understand how many songs have missing year data so I can assess data quality.

**Why this priority**: Transparency about data quality helps users understand limitations of the analytics.

**Independent Test**: Can be tested by querying database for songs with year='s/d' or empty and verifying the dashboard shows this count separately.

**Acceptance Scenarios**:

1. **Given** songs with year="s/d" exist in the database, **When** the dashboard loads, **Then** I see a "Songs without year data" indicator showing the count
2. **Given** I click on the "Songs without year data" indicator, **Then** I see a breakdown of which albums contain these songs

---

### Edge Cases

- What happens when the timeline has only 1-2 data points?
- How does the system handle a year with 0 songs (gap in timeline)?
- What happens when ALL songs have "s/d" year?
- What happens when the database returns empty results for all metrics?
- What happens when Trivy cannot connect to vulnerability database?
- What happens when Docker image is extremely large (multiple GB)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Timeline chart MUST animate on initial load and respond to hover/click interactions
- **FR-002**: Timeline chart MUST exclude songs with year="s/d" from the main visualization
- **FR-003**: Dashboard MUST display a separate indicator showing count of songs with missing year data
- **FR-004**: All displayed KPI values MUST match direct database queries for the same metric
- **FR-005**: All chart data MUST be validated against database before rendering
- **FR-006**: After `speckit implement` completes, Docker images MUST be scanned with Trivy
- **FR-007**: Trivy scans that find CRITICAL vulnerabilities MUST fail the CI pipeline
- **FR-008**: Trivy scan reports MUST be archived as build artifacts

### Key Entities *(include if feature involves data)*

- **Song**: Has title, album, year (can be "s/d"), lyrics, clasificacion, tema
- **Album (Fonograma)**: Has title, artist, year, song count
- **Dashboard Metrics**: Total songs, total albums, songs by year, songs by clasificacion, songs by OOV level
- **Docker Image**: Built artifact that needs vulnerability scanning
- **Trivy Report**: Security scan results with vulnerability classifications

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Timeline animation completes within 2 seconds on page load
- **SC-002**: All hover/click interactions on timeline respond within 200ms
- **SC-003**: Every KPI displayed on dashboard matches the corresponding database query result (100% accuracy)
- **SC-004**: Songs with year="s/d" are NEVER shown in the main timeline chart
- **SC-005**: Trivy scan executes automatically after every `speckit implement` that builds Docker images
- **SC-006**: CI pipeline fails if Trivy finds CRITICAL vulnerabilities with CVSS score >= 7.0
- **SC-007**: Trivy reports are stored for at least 30 days as build artifacts

## Assumptions

- Users access the dashboard via modern browsers supporting CSS animations
- Trivy is available in the CI environment with up-to-date vulnerability definitions
- The "s/d" (sin dato) year indicator is stored as the string "s/d" in the database
- Analytics data issues are caused by frontend display problems, not database schema issues
- Docker image scanning should happen for both backend and frontend images
- Critical vulnerability threshold follows industry standard (CVSS 7.0+)