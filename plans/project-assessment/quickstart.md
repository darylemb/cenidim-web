# Quickstart: Project Assessment Implementation

**Date**: 2026-05-10  
**Context**: Implementation guide for security hardening, backend optimization, and frontend enhancement

---

## Prerequisites

- Go 1.21+
- Node.js 18+ and npm
- SQLite3
- Git

---

## Backend Implementation

### 1. Security Hardening

#### Remove Hardcoded JWT Secret

```bash
# In backend/middleware/auth.go
# Remove the fallback secret around line 22
# Required: Set JWT_SECRET env var before running
```

```go
// middleware/auth.go - Required changes
package middleware

import (
    "context"
    "net/http"
    "os"
    "strings"

    "github.com/gin-gonic/gin"
    "github.com/golang-jwt/jwt/v5"
)

// GetTokenSecret returns the JWT secret from environment variable
func GetTokenSecret() string {
    secret := os.Getenv("JWT_SECRET")
    if secret == "" {
        log.Fatal("JWT_SECRET environment variable is required")
    }
    return secret
}
```

#### Add Rate Limiting

```go
// main.go - Add rate limiter middleware
import (
    "golang.org/x/time/rate"
    "github.com/gin-contrib/cors"
   "github.com/gin-contrib/helmet"
)

func rateLimiterMiddleware(rps float64, burst int) gin.HandlerFunc {
    limiter := rate.NewLimiter(rate.Limit(rps), burst)
    return func(c *gin.Context) {
        if !limiter.Allow() {
            c.JSON(http.StatusTooManyRequests, gin.H{
                "error": "Too many requests",
                "retry_after": 60,
            })
            c.Abort()
            return
        }
        c.Next()
    }
}

func main() {
    // ... existing code ...
    
    // Security middleware
    router.Use(helmet.New())
    router.Use(cors.New(cors.Config{
        AllowOrigins: strings.Split(os.Getenv("CORS_ORIGINS"), ","),
        AllowHeaders: []string{"Authorization", "Content-Type"},
    }))
    
    // Rate limiting (apply per-route as needed)
    authGroup := router.Group("/api/auth")
    authGroup.Use(rateLimiterMiddleware(5, 10)) // 5 req/sec, burst 10
}
```

#### Add Input Sanitization for Search

```go
// handlers/songs.go - Sanitize search input
import "regexp"

func sanitizeSearchQuery(query string) string {
    // Remove special LIKE characters
    re := regexp.MustCompile(`[%_\\]`)
    return re.ReplaceAllString(query, `\\$0`)
}

func (h *SongsHandler) SearchSongs(c *gin.Context) {
    query := c.Query("q")
    if len(query) > 100 {
        c.JSON(http.StatusBadRequest, gin.H{"error": "Query too long"})
        return
    }
    
    sanitized := sanitizeSearchQuery(query)
    // Use sanitized in query
}
```

---

### 2. New Stats Endpoint

#### Add Stats Handler

```go
// handlers/stats.go - New file
package handlers

import (
    "net/http"
    "time"

    "github.com/gin-gonic/gin"
)

type StatsHandler struct {
    DB *sql.DB
}

type StatsResponse struct {
    TotalSongs            int            `json:"total_songs"`
    TotalAlbums           int            `json:"total_albums"`
    SongsByYear           map[string]int `json:"songs_by_year"`
    SongsByClasificacion  map[string]int `json:"songs_by_clasificacion"`
    RecentlyAdded         int            `json:"recently_added"`
}

func (h *StatsHandler) GetStats(c *gin.Context) {
    ctx, cancel := context.WithTimeout(c.Request.Context(), 5*time.Second)
    defer cancel()

    stats := StatsResponse{
        SongsByYear:          make(map[string]int),
        SongsByClasificacion: make(map[string]int),
    }

    // Total songs
    row := h.DB.QueryRowContext(ctx, "SELECT COUNT(*) FROM songs")
    row.Scan(&stats.TotalSongs)

    // Total albums
    row = h.DB.QueryRowContext(ctx, "SELECT COUNT(DISTINCT fonograma_id) FROM songs")
    row.Scan(&stats.TotalAlbums)

    // Songs by year
    rows, err := h.DB.QueryContext(ctx, `
        SELECT f.anio, COUNT(s.id) 
        FROM fonogramas f 
        LEFT JOIN songs s ON s.fonograma_id = f.clave_fonograma 
        GROUP BY f.anio
    `)
    if err == nil {
        defer rows.Close()
        for rows.Next() {
            var year string
            var count int
            rows.Scan(&year, &count)
            stats.SongsByYear[year] = count
        }
    }

    // Recently added (last 30 days)
    thirtyDaysAgo := time.Now().AddDate(0, 0, -30).Format("2006-01-02")
    row = h.DB.QueryRowContext(ctx, 
        "SELECT COUNT(*) FROM songs WHERE created_at >= ?", thirtyDaysAgo)
    row.Scan(&stats.RecentlyAdded)

    c.JSON(http.StatusOK, stats)
}
```

#### Register Stats Route

```go
// main.go - Add route
statsHandler := &handlers.StatsHandler{DB: db}
router.GET("/api/stats", statsHandler.GetStats)
```

---

### 3. Service Layer Pattern (Optional Enhancement)

#### Create Service Interface

```go
// services/song_service.go - New file
package services

import "context"

type Song struct {
    ID          int
    Title       string
    FonogramaID int
    // ... other fields
}

type SongService interface {
    GetSongsByYear(ctx context.Context, year int) ([]Song, error)
    SearchSongs(ctx context.Context, query string) ([]Song, error)
    GetStats(ctx context.Context) (*StatsResponse, error)
}
```

#### Create Repository Interface

```go
// repositories/song_repository.go - New file
package repositories

import "context"

type SongRepository interface {
    FindByYear(ctx context.Context, year int) ([]Song, error)
    Search(ctx context.Context, query string) ([]Song, error)
    GetStats(ctx context.Context) (*Stats, error)
}
```

---

## Frontend Implementation

### 1. Fix Dashboard with Real Stats

```jsx
// frontend/src/components/DashboardView.jsx
import { useEffect, useState } from 'react';
import { Bar } from 'react-chartjs-2';

function DashboardView() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetch('/api/stats', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        })
        .then(res => {
            if (!res.ok) throw new Error('Failed to fetch stats');
            return res.json();
        })
        .then(data => {
            setStats(data);
            setLoading(false);
        })
        .catch(err => {
            setError(err.message);
            setLoading(false);
        });
    }, []);

    if (loading) return <div className="loading">Cargando estadísticas...</div>;
    if (error) return <div className="error">Error: {error}</div>;

    return (
        <div className="dashboard">
            <div className="stats-cards">
                <div className="stat-card">
                    <h3>Total de Canciones</h3>
                    <p className="stat-value">{stats.total_songs}</p>
                </div>
                <div className="stat-card">
                    <h3>Álbumes</h3>
                    <p className="stat-value">{stats.total_albums}</p>
                </div>
                <div className="stat-card">
                    <h3>Agregados Recientemente</h3>
                    <p className="stat-value">{stats.recently_added}</p>
                </div>
            </div>
            {/* Chart implementation */}
        </div>
    );
}
```

---

### 2. Timeline Enhancements

```css
/* frontend/src/components/Timeline.css */
/* Horizontal scroll with momentum */
.timeline-container {
    overflow-x: scroll;
    scroll-snap-type: x mandatory;
    scroll-behavior: smooth;
    -webkit-overflow-scrolling: touch;
}

.timeline-year {
    scroll-snap-align: start;
    min-width: 300px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.timeline-year:hover {
    transform: scale(1.05);
    box-shadow: 0 0 20px rgba(0, 123, 255, 0.3);
}

/* Keyboard navigation */
.timeline-container:focus {
    outline: none;
}
```

```jsx
// frontend/src/components/Timeline.jsx - Keyboard navigation
useEffect(() => {
    const handleKeyDown = (e) => {
        if (e.key === 'ArrowRight') {
            containerRef.current.scrollBy({ left: 320, behavior: 'smooth' });
        } else if (e.key === 'ArrowLeft') {
            containerRef.current.scrollBy({ left: -320, behavior: 'smooth' });
        }
    };

    const container = containerRef.current;
    container?.addEventListener('keydown', handleKeyDown);
    return () => container?.removeEventListener('keydown', handleKeyDown);
}, []);
```

---

## Environment Variables

Create a `.env.example` file:

```bash
# Backend
JWT_SECRET=your-secure-secret-here
CORS_ORIGINS=http://localhost:3000,https://cenidim.mx
DATABASE_PATH=./data/cenidim.db

# Frontend
REACT_APP_API_URL=http://localhost:8080
```

---

## Running the Implementation

### Development

```bash
# Backend
cd backend
export JWT_SECRET=dev-secret
export CORS_ORIGINS=http://localhost:3000
go run main.go

# Frontend
cd frontend
npm start
```

### Testing

```bash
# Backend tests
cd backend
go test ./... -v

# Frontend tests
cd frontend
npm test -- --watchAll=false
```

### Docker

```bash
# Build and run
docker-compose -f docker-compose-coolify.yaml up -d

# View logs
docker-compose -f docker-compose-coolify.yaml logs -f
```

---

## Troubleshooting

### "JWT_SECRET environment variable is required"
- Ensure `JWT_SECRET` is set in environment before running backend
- For Docker, set in docker-compose.yaml or environment

### CORS errors
- Verify `CORS_ORIGINS` includes your frontend origin
- For development: `http://localhost:3000`
- No wildcards allowed in production

### Stats endpoint returning 0
- Check database has songs and fonogramas tables populated
- Verify database path is correct

---

## Next Steps

1. **Phase 1**: Implement security hardening (JWT, CORS, rate limiting)
2. **Phase 2**: Add stats endpoint and auth handler tests
3. **Phase 3**: Connect frontend dashboard to stats API
4. **Phase 4**: Enhance timeline with smooth animations
5. **Phase 5**: Update documentation and README
