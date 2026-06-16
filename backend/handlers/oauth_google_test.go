package handlers

import (
	"context"
	"database/sql"
	"errors"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	_ "modernc.org/sqlite"
)

func setupOAuthTestDB(t *testing.T) {
	t.Helper()
	database.DB = nil
	db, err := sql.Open("sqlite", ":memory:")
	require.NoError(t, err)
	schema := `
	CREATE TABLE users (
		id            INTEGER PRIMARY KEY AUTOINCREMENT,
		username      TEXT UNIQUE NOT NULL,
		email         TEXT UNIQUE NOT NULL,
		password_hash TEXT NOT NULL,
		role          TEXT NOT NULL DEFAULT 'viewer',
		created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
	);
	CREATE TABLE user_identities (
		id              INTEGER PRIMARY KEY AUTOINCREMENT,
		user_id         INTEGER NOT NULL,
		provider        TEXT    NOT NULL,
		subject         TEXT    NOT NULL,
		email_at_link   TEXT    NOT NULL,
		linked_at       TEXT    NOT NULL,
		UNIQUE (provider, subject)
	);
	`
	_, err = db.Exec(schema)
	require.NoError(t, err)
	database.DB = db
}

func withGoogleEnv(t *testing.T) {
	t.Helper()
	os.Setenv("GOOGLE_CLIENT_ID", "test-client-id")
	os.Setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
	os.Setenv("GOOGLE_REDIRECT_URL", "http://localhost:8080/api/auth/google/callback")
	os.Setenv("FRONTEND_BASE_URL", "http://localhost:3000")
}

func clearGoogleEnv(t *testing.T) {
	t.Helper()
	os.Unsetenv("GOOGLE_CLIENT_ID")
	os.Unsetenv("GOOGLE_CLIENT_SECRET")
	os.Unsetenv("GOOGLE_REDIRECT_URL")
	os.Unsetenv("FRONTEND_BASE_URL")
}

func TestLoadGoogleOAuthEnv_MissingVars(t *testing.T) {
	clearGoogleEnv(t)
	_, err := LoadGoogleOAuthEnv()
	assert.Error(t, err)
}

func TestLoadGoogleOAuthEnv_AllPresent(t *testing.T) {
	withGoogleEnv(t)
	defer clearGoogleEnv(t)
	env, err := LoadGoogleOAuthEnv()
	require.NoError(t, err)
	assert.Equal(t, "test-client-id", env.ClientID)
}

func TestGoogleAuthStart_RedirectsAndSetsCookie(t *testing.T) {
	withGoogleEnv(t)
	defer clearGoogleEnv(t)
	gin.SetMode(gin.TestMode)
	setupOAuthTestDB(t)
	defer database.DB.Close()

	r := gin.New()
	r.GET("/api/auth/google/start", GoogleAuthStart)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/auth/google/start", nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusFound, w.Code)
	loc := w.Header().Get("Location")
	assert.Contains(t, loc, "accounts.google.com")
	assert.Contains(t, loc, "state=")
	cookies := w.Header()["Set-Cookie"]
	require.NotEmpty(t, cookies)
	found := false
	for _, c := range cookies {
		if strings.HasPrefix(c, "oauth_state=") {
			found = true
			// A plain HTTP request (no TLS, no proxy) must not carry
			// the Secure flag — the browser would otherwise drop the
			// cookie on the local dev loopback.
			assert.NotContains(t, c, "Secure",
				"plain HTTP requests must not get a Secure cookie")
		}
	}
	assert.True(t, found, "oauth_state cookie must be set")
}

// TestGoogleAuthStart_SecureBehindProxy confirms that when the request
// arrives over HTTP but carries `X-Forwarded-Proto: https` (the standard
// signal a reverse proxy injects to indicate the original request was
// HTTPS), the state cookie still gets the Secure flag.
func TestGoogleAuthStart_SecureBehindProxy(t *testing.T) {
	withGoogleEnv(t)
	defer clearGoogleEnv(t)
	gin.SetMode(gin.TestMode)
	setupOAuthTestDB(t)
	defer database.DB.Close()

	r := gin.New()
	r.GET("/api/auth/google/start", GoogleAuthStart)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/auth/google/start", nil)
	req.Header.Set("X-Forwarded-Proto", "https")
	r.ServeHTTP(w, req)

	require.Equal(t, http.StatusFound, w.Code)
	cookies := w.Header()["Set-Cookie"]
	require.NotEmpty(t, cookies)
	found := false
	for _, c := range cookies {
		if strings.HasPrefix(c, "oauth_state=") {
			found = true
			assert.Contains(t, c, "Secure",
				"X-Forwarded-Proto=https must mark the cookie Secure")
		}
	}
	assert.True(t, found, "oauth_state cookie must be set")
}

func TestGoogleAuthStart_RejectsWithoutEnv(t *testing.T) {
	clearGoogleEnv(t)
	gin.SetMode(gin.TestMode)
	setupOAuthTestDB(t)
	defer database.DB.Close()

	r := gin.New()
	r.GET("/api/auth/google/start", GoogleAuthStart)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/auth/google/start", nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusInternalServerError, w.Code)
}

func TestGoogleAuthCallback_RejectsStateMismatch(t *testing.T) {
	withGoogleEnv(t)
	defer clearGoogleEnv(t)
	gin.SetMode(gin.TestMode)
	setupOAuthTestDB(t)
	defer database.DB.Close()

	r := gin.New()
	r.GET("/api/auth/google/callback", GoogleAuthCallback)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/auth/google/callback?state=foo&code=bar", nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusFound, w.Code)
	assert.Contains(t, w.Header().Get("Location"), "google=err=state_mismatch")
}

func TestGoogleAuthCallback_RejectsUserCancelled(t *testing.T) {
	withGoogleEnv(t)
	defer clearGoogleEnv(t)
	gin.SetMode(gin.TestMode)
	setupOAuthTestDB(t)
	defer database.DB.Close()

	r := gin.New()
	r.GET("/api/auth/google/callback", GoogleAuthCallback)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/auth/google/callback?state=foo&error=access_denied", nil)
	req.AddCookie(&http.Cookie{Name: "oauth_state", Value: "foo"})
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusFound, w.Code)
	assert.Contains(t, w.Header().Get("Location"), "google=err=user_cancelled")
}

func TestFindOrCreateUser_MatchesExisting(t *testing.T) {
	setupOAuthTestDB(t)
	defer database.DB.Close()
	_, err := database.DB.Exec(
		`INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)`,
		"jane", "jane@example.com", "GOOGLE_LINKED", "editor",
	)
	require.NoError(t, err)

	uid, username, role, auto, err := findOrCreateUser(
		context.Background(), &GoogleIDTokenClaims{Email: "jane@example.com", Sub: "google-1"},
	)
	require.NoError(t, err)
	assert.Equal(t, "jane", username)
	assert.Equal(t, "editor", role)
	assert.False(t, auto)
	assert.NotZero(t, uid)
}

func TestFindOrCreateUser_ProvisionsViewer(t *testing.T) {
	setupOAuthTestDB(t)
	defer database.DB.Close()
	uid, username, role, auto, err := findOrCreateUser(
		context.Background(), &GoogleIDTokenClaims{Email: "newuser@example.com", Sub: "google-2"},
	)
	require.NoError(t, err)
	assert.True(t, auto)
	assert.Equal(t, "newuser", username)
	assert.Equal(t, "viewer", role)
	assert.NotZero(t, uid)

	// Hash should be the sentinel so the password route short-circuits.
	var hash string
	require.NoError(t, database.DB.QueryRow(`SELECT password_hash FROM users WHERE id = ?`, uid).Scan(&hash))
	assert.Equal(t, "GOOGLE_LINKED", hash)
}

func TestLinkIdentity_Idempotent(t *testing.T) {
	setupOAuthTestDB(t)
	defer database.DB.Close()
	uid, _, _, _, _ := findOrCreateUser(
		context.Background(), &GoogleIDTokenClaims{Email: "x@example.com", Sub: "google-3"},
	)
	claims := &GoogleIDTokenClaims{Email: "x@example.com", Sub: "google-3"}
	require.NoError(t, linkIdentity(context.Background(), uid, claims))
	require.NoError(t, linkIdentity(context.Background(), uid, claims), "re-linking must be a no-op")
	var n int
	require.NoError(t, database.DB.QueryRow(`SELECT COUNT(*) FROM user_identities WHERE user_id = ?`, uid).Scan(&n))
	assert.Equal(t, 1, n)
}

func TestUnlinkIdentity(t *testing.T) {
	setupOAuthTestDB(t)
	defer database.DB.Close()
	uid, _, _, _, _ := findOrCreateUser(
		context.Background(), &GoogleIDTokenClaims{Email: "y@example.com", Sub: "google-4"},
	)
	_ = linkIdentity(context.Background(), uid, &GoogleIDTokenClaims{Email: "y@example.com", Sub: "google-4"})
	found, err := unlinkIdentity(context.Background(), uid)
	require.NoError(t, err)
	assert.True(t, found)
	found2, err := unlinkIdentity(context.Background(), uid)
	require.NoError(t, err)
	assert.False(t, found2)
}

// stubVerifier returns canned claims without checking signatures, so the
// happy-path test does not need a real Google-issued JWT.
type stubVerifier struct {
	claims *GoogleIDTokenClaims
	err    error
}

func (s stubVerifier) Verify(_ context.Context, _ string) (*GoogleIDTokenClaims, error) {
	return s.claims, s.err
}

func TestVerifyIDToken_RejectsBadJWT(t *testing.T) {
	env, _ := LoadGoogleOAuthEnv()
	env.ClientID = "aud"
	stub := stubVerifier{err: errors.New("bad jwt")}
	client := NewGoogleOAuthClientWithVerifier(env, stub)
	_, err := client.VerifyIDToken(context.Background(), "not-a-jwt")
	assert.Error(t, err)
}

func TestVerifyIDToken_AcceptsValidClaims(t *testing.T) {
	env, _ := LoadGoogleOAuthEnv()
	env.ClientID = "aud"
	stub := stubVerifier{claims: &GoogleIDTokenClaims{
		Sub:           "google-5",
		Email:         "z@example.com",
		EmailVerified: true,
		Aud:           "aud",
	}}
	client := NewGoogleOAuthClientWithVerifier(env, stub)
	claims, err := client.VerifyIDToken(context.Background(), "any-token")
	require.NoError(t, err)
	assert.Equal(t, "google-5", claims.Sub)
	assert.True(t, claims.EmailVerified)
}
