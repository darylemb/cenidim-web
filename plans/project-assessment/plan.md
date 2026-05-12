# Implementation Plan: Project Quality Assessment & Improvement

**Branch**: `sandbox` | **Date**: 2026-05-10 | **Spec**: [project-assessment.md](../project-assessment.md)
**Note**: This is an assessment-driven implementation plan, not a feature branch plan. Executing on `sandbox` branch per user request.

## Summary

Address critical security vulnerabilities, testing gaps, and frontend inconsistencies identified in the project assessment. The implementation follows a phased approach: security hardening first, then backend optimization, frontend enhancement, and finally timeline redesign.

## Technical Context

**Language/Version**: Go 1.21+ (backend), JavaScript/React 19.2.4 (frontend)  
**Primary Dependencies**: Gin (Go HTTP framework), Chart.js, React Testing Library  
**Storage**: SQLite with prepared statements  
**Testing**: Go test suite, React Testing Library, (no E2E yet)  
**Target Platform**: Linux server (Docker), Web browser (frontend)  
**Project Type**: Web service + SPA frontend  
**Performance Goals**: Dashboard <500ms load, Timeline smooth 60fps scrolling  
**Constraints**: backward compatibility with existing API, no data migration required  
**Scale/Scope**: ~175 songs, ~14 albums, single-instance deployment

## Constitution Check

*Note: Constitution file is a template with placeholders. No gates apply to this assessment-driven plan.*

**GATE Status**: N/A - No violations

## Project Structure

### Documentation (this feature)

```text
plans/project-assessment/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/          # Song, User, Fonograma models
│   ├── handlers/        # API handlers (songs, auth, admin, stats)
│   ├── middleware/      # Auth, logging middleware
│   └── database/       # DB connection and queries
└── tests/
    └── integration/     # Handler tests with SQLite

frontend/
├── src/
│   ├── components/      # React components (Dashboard, Timeline, etc.)
│   ├── services/         # API client layer
│   └── styles/          # CSS design system
└── tests/
    └── components/      # React Testing Library tests
```

**Structure Decision**: Existing project structure is appropriate. No restructuring required - focus on improvements within existing layers.

## Research Phase - Key Unknowns

From project-assessment.md, the following items need research:

1. **JWT Secret Management**: How should the fallback secret be handled? Environment variables only?
2. **Rate Limiting Implementation**: What library for Go/Gin? Any existing patterns in similar projects?
3. **CORS Configuration**: What origins should be allowed? Configuration approach?
4. **Timeline Animation Library**: Best approach for smooth horizontal scroll with momentum?
5. **React Migration Path**: Vite vs CRA updates - pros/cons for this specific project?

## Implementation Phases

### Phase 1: Security Hardening (Week 1)

| Task | File | Changes |
|------|------|---------|
| Remove hardcoded JWT fallback | `middleware/auth.go` | Require JWT_SECRET env var |
| Add rate limiting | `main.go` | Integrate limiter middleware |
| Fix CORS | `main.go` | Remove wildcard, allow specific origins |
| Add input sanitization | `handlers/songs.go` | Validate LIKE clause queries |
| Add security headers | `main.go` | Integrate helmet middleware |

### Phase 2: Backend Optimization (Week 2)

| Task | File | Changes |
|------|------|---------|
| Create service layer | `services/` (new) | Extract business logic from handlers |
| Create repository interfaces | `repositories/` (new) | Abstract database operations |
| Add /api/stats endpoint | `handlers/stats.go` | New endpoint for dashboard metrics |
| Add auth handler tests | `handlers/auth_test.go` | Test Login, Register, Me |

### Phase 3: Frontend Enhancement (Week 3)

| Task | File | Changes |
|------|------|---------|
| Fix hardcoded dashboard | `DashboardView.jsx` | Fetch from /api/stats |
| Add stats API integration | `services/` | Connect frontend to stats endpoint |
| Fix README reference | `README.md` | Change Python → Go |
| Add Timeline tests | `Timeline.test.jsx` | React Testing Library |

### Phase 4: Timeline Redesign (Week 4)

| Task | File | Changes |
|------|------|---------|
| Horizontal scroll with momentum | `Timeline.jsx` | CSS scroll-snap + JS |
| Smooth year transitions | `Timeline.jsx` | Intersection Observer API |
| Animated connecting line | `Timeline.jsx` | SVG animation |
| Parallax depth effects | `Timeline.jsx` | CSS transforms |
| Keyboard navigation | `Timeline.jsx` | Arrow key support |

## Complexity Tracking

> No complexity violations to justify at this time.

## Questions for Clarification (from Assessment)

1. **Timeline Style**: Horizontal (Timeline.js style) or maintain pentagram/musical staff concept?
2. **Dashboard Metrics Priority**: Songs by year? Classification breakdown? Recently added?
3. **React Migration**: Migrate to Vite (recommended) or keep CRA with updates?
4. **Service Layer**: Acceptable to refactor handlers to use service layer?

*These will be resolved during Phase 0 research or deferred to implementation.*
