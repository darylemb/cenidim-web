# Research: Project Assessment Implementation

**Date**: 2026-05-10  
**Context**: Implementation planning for security hardening, backend optimization, frontend enhancement, and timeline redesign per project-assessment.md

---

## 1. JWT Secret Management

### Decision
**Environment variable required, no fallback in production code.**

### Rationale
- Hardcoded secrets are a critical security vulnerability (CVE-worthy)
- The fallback "cenidim-secret-change-in-production" defeats the purpose of secret rotation
- 12-factor app methodology requires all config via environment

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|-----------------|
| Hardcoded fallback with warning | Security risk - secret could ship to production |
| Configuration file (config.json) | Extra file to manage, not 12-factor compliant |
| Fallback to env var only | **Selected** - Clean, secure, simple |

### Implementation
```go
// middleware/auth.go - Required changes
tokenSecret := os.Getenv("JWT_SECRET")
if tokenSecret == "" {
    log.Fatal("JWT_SECRET environment variable is required")
}
// Remove the fallback secret entirely
```

---

## 2. Rate Limiting for Go/Gin

### Decision
**Use golang.org/x/time/rateLimiter middleware or golang-middleware/middleware**

### Rationale
- golang.org/x/time/rate is the standard rate limiting package
- Integrates well with Gin middleware pattern
- Supports burst and tokens-per-second configuration

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|-----------------|
| custom-solution/ratelimit | Less battle-tested |
| utron middleware | Overkill for this use case |
| nginx-level rate limiting | Should be defense-in-depth, not sole solution |

### Implementation
```go
// main.go - Add rate limiter
import "golang.org/x/time/rate"

func rateLimiterMiddleware(rps float64, burst int) gin.HandlerFunc {
    limiter := rate.NewLimiter(rate.Limit(rps), burst)
    return func(c *gin.Context) {
        if !limiter.Allow() {
            c.JSON(429, gin.H{"error": "Too many requests"})
            c.Abort()
            return
        }
        c.Next()
    }
}
```

---

## 3. CORS Configuration

### Decision
**Allowlist specific origins from environment variable, no wildcard**

### Rationale
- Current `AllowOrigins: []string{"*"}` exposes API to any origin
- Should be configurable for different deployments (dev, staging, prod)

### Implementation
```go
// main.go - CORS configuration
allowedOrigins := strings.Split(os.Getenv("CORS_ORIGINS"), ",")
config := cors.DefaultConfig()
config.AllowOrigins = allowedOrigins
config.AllowHeaders = []string{"Authorization", "Content-Type"}
```

---

## 4. Timeline Animation Approach

### Decision
**CSS scroll-snap with Intersection Observer for progressive loading**

### Rationale
- Native browser scrolling with scroll-snap provides momentum without JS libraries
- Intersection Observer is lightweight and well-supported
- Avoids heavy dependencies like Timeline.js or GSAP

### Alternatives Considered
| Alternative | Rejected Because |
|-------------|-----------------|
| Timeline.js library | Too heavy, requires jQuery |
| GSAP animation | Overkill for scroll-based animations |
| Custom scroll handler | Performance issues, harder to maintain |

### Implementation Approach
1. **Horizontal scroll**: `overflow-x: scroll; scroll-snap-type: x mandatory;`
2. **Year cards**: `scroll-snap-align: start;`
3. **Progressive loading**: Intersection Observer triggers song loading
4. **Connecting line**: SVG path with `stroke-dasharray` animation
5. **Keyboard nav**: Arrow keys mapped to `scrollBy()`

---

## 5. React Migration (Vite vs CRA)

### Decision
**Defer migration to Vite - current React 19 + react-scripts 5.0.1 works but is deprecated**

### Rationale
- The project uses React 19.2.4 with react-scripts 5.0.1 (deprecated but functional)
- Vite migration is non-trivial and not blocking security fixes
- Schedule Vite migration as a follow-up task after security hardening

### Migration Path (for future reference)
1. Create new Vite project with React template
2. Install dependencies matching current package.json
3. Migrate components incrementally
4. Update build scripts

### Note
This decision may need revisiting based on:
- React 19 compatibility with existing dependencies
- Build toolchain stability requirements

---

## 6. Backend Service Layer Pattern

### Decision
**Introduce service layer with repository pattern for testability**

### Rationale
- Current handlers directly call database, making unit testing difficult
- Service layer extracts business logic from HTTP handling
- Repository pattern provides abstraction over SQL

### Architecture
```
API Handler → Service Layer → Repository Layer → Database
```

### Implementation
```go
// services/song_service.go
type SongService interface {
    GetSongsByYear(year int) ([]Song, error)
    SearchSongs(query string) ([]Song, error)
    GetStats() (*Stats, error)
}

// repositories/song_repository.go
type SongRepository interface {
    FindByYear(year int) ([]Song, error)
    Search(query string) ([]Song, error)
    GetStats() (*Stats, error)
}
```

---

## 7. Input Sanitization for LIKE Queries

### Decision
**Whitelist validation + prepared statement escaping**

### Rationale
- User input in LIKE clauses requires strict validation
- SQL prepared statements handle escaping, but validation adds defense-in-depth

### Implementation
```go
// handlers/songs.go
func sanitizeSearchQuery(query string) string {
    // Remove special LIKE characters
    re := regexp.MustCompile(`[%_\\]`)
    return re.ReplaceAllString(query, `\$0`)
}
```

---

## Summary of Decisions

| Item | Decision |
|------|----------|
| JWT Secret | Environment variable only, no fallback |
| Rate Limiting | golang.org/x/time/rate |
| CORS | Allowlist from CORS_ORIGINS env var |
| Timeline Animation | CSS scroll-snap + Intersection Observer |
| React Migration | Defer to future task |
| Service Layer | Introduce for testability |
| Search Input | Whitelist validation + escaping |

---

## Open Questions

1. **Timeline Style**: Awaiting clarification on horizontal vs pentagram concept
2. **Dashboard Metrics Priority**: Awaiting clarification on most important metrics
3. **React Migration Timeline**: Awaiting decision on Vite migration urgency

All open questions can be deferred to Phase 2 (implementation) as they don't block the implementation plan.
