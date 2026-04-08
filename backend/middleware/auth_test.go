package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"github.com/stretchr/testify/assert"
)

// makeToken creates a signed JWT for use in middleware tests.
func makeToken(userID int, username, role string) string {
	claims := Claims{
		UserID:   userID,
		Username: username,
		Role:     role,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(time.Hour)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	signed, _ := token.SignedString(jwtSecret())
	return signed
}

func authOnlyRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.Use(RequireAuth())
	r.GET("/", func(c *gin.Context) {
		role, _ := c.Get("role")
		username, _ := c.Get("username")
		c.JSON(http.StatusOK, gin.H{"role": role, "username": username})
	})
	return r
}

func roleRouter(minRole string) *gin.Engine {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.Use(RequireAuth())
	r.Use(RequireRole(minRole))
	r.GET("/", func(c *gin.Context) { c.Status(http.StatusOK) })
	return r
}

// ─── RequireAuth tests ────────────────────────────────────────────────────────

func TestRequireAuth_NoHeader(t *testing.T) {
	r := authOnlyRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	r.ServeHTTP(w, req)
	assert.Equal(t, http.StatusUnauthorized, w.Code)
}

func TestRequireAuth_BadFormat(t *testing.T) {
	r := authOnlyRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	req.Header.Set("Authorization", "Token abc123") // wrong scheme
	r.ServeHTTP(w, req)
	assert.Equal(t, http.StatusUnauthorized, w.Code)
}

func TestRequireAuth_InvalidToken(t *testing.T) {
	r := authOnlyRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	req.Header.Set("Authorization", "Bearer notavalidtoken")
	r.ServeHTTP(w, req)
	assert.Equal(t, http.StatusUnauthorized, w.Code)
}

func TestRequireAuth_ExpiredToken(t *testing.T) {
	r := authOnlyRouter()
	claims := Claims{
		UserID:   1,
		Username: "user",
		Role:     "viewer",
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(-time.Hour)), // expired
			IssuedAt:  jwt.NewNumericDate(time.Now().Add(-2 * time.Hour)),
		},
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	signed, _ := token.SignedString(jwtSecret())

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	req.Header.Set("Authorization", "Bearer "+signed)
	r.ServeHTTP(w, req)
	assert.Equal(t, http.StatusUnauthorized, w.Code)
}

func TestRequireAuth_ValidToken(t *testing.T) {
	r := authOnlyRouter()
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	req.Header.Set("Authorization", "Bearer "+makeToken(1, "testadmin", "admin"))
	r.ServeHTTP(w, req)
	assert.Equal(t, http.StatusOK, w.Code)
}

// ─── RequireRole tests ────────────────────────────────────────────────────────

func TestRequireRole_ViewerAccessesViewerRoute(t *testing.T) {
	r := roleRouter("viewer")
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	req.Header.Set("Authorization", "Bearer "+makeToken(3, "viewer1", "viewer"))
	r.ServeHTTP(w, req)
	assert.Equal(t, http.StatusOK, w.Code)
}

func TestRequireRole_ViewerBlockedFromEditorRoute(t *testing.T) {
	r := roleRouter("editor")
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	req.Header.Set("Authorization", "Bearer "+makeToken(3, "viewer1", "viewer"))
	r.ServeHTTP(w, req)
	assert.Equal(t, http.StatusForbidden, w.Code)
}

func TestRequireRole_ViewerBlockedFromAdminRoute(t *testing.T) {
	r := roleRouter("admin")
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	req.Header.Set("Authorization", "Bearer "+makeToken(3, "viewer1", "viewer"))
	r.ServeHTTP(w, req)
	assert.Equal(t, http.StatusForbidden, w.Code)
}

func TestRequireRole_EditorAccessesEditorRoute(t *testing.T) {
	r := roleRouter("editor")
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	req.Header.Set("Authorization", "Bearer "+makeToken(2, "editor1", "editor"))
	r.ServeHTTP(w, req)
	assert.Equal(t, http.StatusOK, w.Code)
}

func TestRequireRole_EditorBlockedFromAdminRoute(t *testing.T) {
	r := roleRouter("admin")
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	req.Header.Set("Authorization", "Bearer "+makeToken(2, "editor1", "editor"))
	r.ServeHTTP(w, req)
	assert.Equal(t, http.StatusForbidden, w.Code)
}

func TestRequireRole_AdminAccessesAllRoutes(t *testing.T) {
	for _, minRole := range []string{"viewer", "editor", "admin"} {
		r := roleRouter(minRole)
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("GET", "/", nil)
		req.Header.Set("Authorization", "Bearer "+makeToken(1, "admin1", "admin"))
		r.ServeHTTP(w, req)
		assert.Equal(t, http.StatusOK, w.Code, "admin should access %s route", minRole)
	}
}
