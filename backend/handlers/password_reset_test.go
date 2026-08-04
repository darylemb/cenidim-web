package handlers

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"golang.org/x/crypto/bcrypt"
	_ "modernc.org/sqlite"
)

// setupPasswordResetDB seeds the minimal schema and an admin user for
// the password-reset tests.
func setupPasswordResetDB(t *testing.T) {
	t.Helper()
	database.DB = nil
	// Use a temp-file DB so multi-connection queries see the same
	// schema (":memory:" is per-connection in SQLite). The file is
	// cleaned up automatically when the test ends via t.Cleanup.
	tmpFile, err := os.CreateTemp("", "letras-test-*.db")
	if err != nil {
		t.Fatalf("create temp db: %v", err)
	}
	tmpPath := tmpFile.Name()
	tmpFile.Close()
	t.Cleanup(func() { _ = os.Remove(tmpPath) })
	// WAL mode lets reads happen concurrently with the single writer.
	// _busy_timeout gives SQLite a chance to wait for the writer.
	db, err := sql.Open("sqlite", tmpPath+"?_busy_timeout=30000&_journal_mode=WAL")
	if err != nil {
		t.Fatalf("open: %v", err)
	}
	schema := `
	CREATE TABLE users (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		username TEXT UNIQUE NOT NULL,
		email TEXT UNIQUE NOT NULL,
		password_hash TEXT NOT NULL,
		role TEXT NOT NULL DEFAULT 'viewer',
		last_sign_in_at DATETIME,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP
	);
	CREATE TABLE password_reset_tokens (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		user_id INTEGER NOT NULL,
		token_hash TEXT NOT NULL UNIQUE,
		expires_at DATETIME NOT NULL,
		used_at DATETIME,
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
	);
	CREATE TABLE email_outbox (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		to_addr TEXT NOT NULL,
		subject TEXT NOT NULL,
		body_text TEXT NOT NULL,
		body_html TEXT,
		kind TEXT NOT NULL,
		related_user_id INTEGER,
		delivered_at DATETIME,
		failed_at DATETIME,
		failure_reason TEXT,
		sent_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (related_user_id) REFERENCES users(id) ON DELETE SET NULL
	);
	`
	if _, err := db.Exec(schema); err != nil {
		t.Fatalf("schema: %v", err)
	}
	// Seed the seed admin so forgot/reset has a real user to target.
	if _, err := db.Exec(
		`INSERT INTO users (username, email, password_hash, role)
		 VALUES ('admin', 'admin@cenidim.test', 'placeholder', 'admin')`,
	); err != nil {
		t.Fatalf("seed: %v", err)
	}
	database.DB = db
}

func setupPasswordResetRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.POST("/auth/forgot", ForgotPassword)
	r.POST("/auth/reset", ResetPassword)
	return r
}

func doPostJSON(r *gin.Engine, path, body string) *httptest.ResponseRecorder {
	req, _ := http.NewRequest("POST", path, bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	return w
}

func TestForgotPassword_RejectsEmptyEmail(t *testing.T) {
	setupPasswordResetDB(t)
	defer database.DB.Close()
	w := doPostJSON(setupPasswordResetRouter(), "/auth/forgot", `{"email":""}`)
	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestForgotPassword_RejectsInvalidJSON(t *testing.T) {
	setupPasswordResetDB(t)
	defer database.DB.Close()
	r := setupPasswordResetRouter()
	req, _ := http.NewRequest("POST", "/auth/forgot", bytes.NewBufferString("{not json"))
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestForgotPassword_UnknownEmailReturns200(t *testing.T) {
	setupPasswordResetDB(t)
	defer database.DB.Close()
	// Generic 200 — never reveal whether the email exists.
	w := doPostJSON(setupPasswordResetRouter(), "/auth/forgot",
		`{"email":"nobody@cenidim.test"}`)
	assert.Equal(t, http.StatusOK, w.Code)
}

func TestForgotPassword_KnownEmailIssuesToken(t *testing.T) {
	setupPasswordResetDB(t)
	defer database.DB.Close()
	w := doPostJSON(setupPasswordResetRouter(), "/auth/forgot",
		`{"email":"ADMIN@CENIDIM.TEST"}`)
	require.Equal(t, http.StatusOK, w.Code)

	// One row in password_reset_tokens, with expires_at in the future.
	var count int
	require.NoError(t, database.DB.QueryRow(
		`SELECT COUNT(*) FROM password_reset_tokens WHERE used_at IS NULL`,
	).Scan(&count))
	assert.Equal(t, 1, count)

	// And one row in email_outbox for the demo path.
	var outboxTo string
	require.NoError(t, database.DB.QueryRow(
		`SELECT to_addr FROM email_outbox WHERE kind = 'password_reset' ORDER BY id DESC LIMIT 1`,
	).Scan(&outboxTo))
	assert.Equal(t, "admin@cenidim.test", outboxTo)
}

func TestForgotPassword_TrimsAndLowercasesEmail(t *testing.T) {
	setupPasswordResetDB(t)
	defer database.DB.Close()
	// Whitespace + uppercase → should match the stored email
	// (`admin@cenidim.test`, lower-cased in the seed).
	w := doPostJSON(setupPasswordResetRouter(), "/auth/forgot",
		`{"email":"   ADMIN@CENIDIM.TEST   "}`)
	assert.Equal(t, http.StatusOK, w.Code)
	var outboxTo string
	require.NoError(t, database.DB.QueryRow(
		`SELECT to_addr FROM email_outbox ORDER BY id DESC LIMIT 1`,
	).Scan(&outboxTo))
	assert.Equal(t, "admin@cenidim.test", outboxTo)
}

func TestResetPassword_RejectsShortPassword(t *testing.T) {
	setupPasswordResetDB(t)
	defer database.DB.Close()
	w := doPostJSON(setupPasswordResetRouter(), "/auth/reset",
		`{"token":"any","new_password":"abc"}`)
	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestResetPassword_RejectsPasswordWithoutDigit(t *testing.T) {
	setupPasswordResetDB(t)
	defer database.DB.Close()
	w := doPostJSON(setupPasswordResetRouter(), "/auth/reset",
		`{"token":"any","new_password":"onlyletters"}`)
	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestResetPassword_RejectsTooLongPassword(t *testing.T) {
	setupPasswordResetDB(t)
	defer database.DB.Close()
	longPwd := strings.Repeat("a1", 65) // 130 chars
	body, _ := json.Marshal(map[string]string{
		"token": "any", "new_password": longPwd,
	})
	w := doPostJSON(setupPasswordResetRouter(), "/auth/reset", string(body))
	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestResetPassword_RejectsEmptyToken(t *testing.T) {
	setupPasswordResetDB(t)
	defer database.DB.Close()
	w := doPostJSON(setupPasswordResetRouter(), "/auth/reset",
		`{"token":"","new_password":"valid123"}`)
	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestResetPassword_RejectsBadToken(t *testing.T) {
	setupPasswordResetDB(t)
	defer database.DB.Close()
	w := doPostJSON(setupPasswordResetRouter(), "/auth/reset",
		`{"token":"not-the-right-token","new_password":"valid123"}`)
	assert.Equal(t, http.StatusUnauthorized, w.Code)
}

func TestResetPassword_HappyPath(t *testing.T) {
	setupPasswordResetDB(t)
	defer database.DB.Close()
	r := setupPasswordResetRouter()

	// 1. Request a reset for the seed admin.
	w := doPostJSON(r, "/auth/forgot", `{"email":"admin@cenidim.test"}`)
	require.Equal(t, http.StatusOK, w.Code)

	// 2. Read the reset URL from the email_outbox and extract the token.
	var body string
	require.NoError(t, database.DB.QueryRow(
		`SELECT body_text FROM email_outbox ORDER BY id DESC LIMIT 1`,
	).Scan(&body))
	idx := strings.Index(body, "/reset?token=")
	require.GreaterOrEqual(t, idx, 0, "expected reset URL in outbox body")
	tail := body[idx+len("/reset?token="):]
	end := strings.IndexAny(tail, " \n")
	var token string
	if end < 0 {
		token = strings.TrimSpace(tail)
	} else {
		token = tail[:end]
	}

	// 3. Reset with that token + a strong new password.
	w = doPostJSON(r, "/auth/reset",
		`{"token":"`+token+`","new_password":"NewStrong123"}`)
	require.Equal(t, http.StatusOK, w.Code)

	// 4. The token is marked used.
	var usedAt *string
	require.NoError(t, database.DB.QueryRow(
		`SELECT used_at FROM password_reset_tokens ORDER BY id DESC LIMIT 1`,
	).Scan(&usedAt))
	assert.NotNil(t, usedAt)

	// 5. The user's password_hash is now the bcrypt of the new one.
	var storedHash string
	require.NoError(t, database.DB.QueryRow(
		`SELECT password_hash FROM users WHERE username = 'admin'`,
	).Scan(&storedHash))
	assert.NotEqual(t, "placeholder", storedHash)
	// bcrypt.CompareHashAndPassword is the canonical check.
	assert.True(t, bcrypt.CompareHashAndPassword(
		[]byte(storedHash), []byte("NewStrong123"),
	) == nil, "new password should match the stored hash")
}

func TestResetPassword_TokenCannotBeReused(t *testing.T) {
	setupPasswordResetDB(t)
	defer database.DB.Close()
	r := setupPasswordResetRouter()

	w := doPostJSON(r, "/auth/forgot", `{"email":"admin@cenidim.test"}`)
	require.Equal(t, http.StatusOK, w.Code)

	var body string
	require.NoError(t, database.DB.QueryRow(
		`SELECT body_text FROM email_outbox ORDER BY id DESC LIMIT 1`,
	).Scan(&body))
	idx := strings.Index(body, "/reset?token=")
	require.GreaterOrEqual(t, idx, 0)
	token := body[idx+len("/reset?token="):]
	token = strings.TrimSpace(strings.Fields(token)[0])

	// First reset succeeds.
	w = doPostJSON(r, "/auth/reset",
		`{"token":"`+token+`","new_password":"FirstReset123"}`)
	require.Equal(t, http.StatusOK, w.Code)

	// Second attempt with the same token is rejected.
	w = doPostJSON(r, "/auth/reset",
		`{"token":"`+token+`","new_password":"SecondReset123"}`)
	assert.Equal(t, http.StatusUnauthorized, w.Code)
}

func TestResetPassword_InvalidatesOtherTokensForSameUser(t *testing.T) {
	setupPasswordResetDB(t)
	defer database.DB.Close()
	r := setupPasswordResetRouter()

	// Request two tokens for the same user.
	doPostJSON(r, "/auth/forgot", `{"email":"admin@cenidim.test"}`)
	time.Sleep(10 * time.Millisecond) // ensure different created_at
	doPostJSON(r, "/auth/forgot", `{"email":"admin@cenidim.test"}`)

	// Use the first one.
	var body string
	require.NoError(t, database.DB.QueryRow(
		`SELECT body_text FROM email_outbox ORDER BY id ASC LIMIT 1`,
	).Scan(&body))
	idx := strings.Index(body, "/reset?token=")
	require.GreaterOrEqual(t, idx, 0)
	// The URL is rendered into the body twice: once plain, once in the
	// HTML variant. We want the FIRST occurrence which is the plain
	// text "Para continuar, abrí este enlace..." line. The body also
	// contains the recipient + reset path; trim the leading "http://"
	// that strings.Fields would otherwise leave attached to the token.
	tokenWithPrefix := strings.TrimSpace(strings.Fields(body[idx+len("/reset?token="):])[0])
	first := strings.TrimPrefix(tokenWithPrefix, "http://")
	first = strings.TrimPrefix(first, "https://")
	// If the URL had a path component, take the token portion after
	// the last "/".
	if idxSlash := strings.LastIndex(first, "/"); idxSlash >= 0 {
		first = first[idxSlash+1:]
	}

	w := doPostJSON(r, "/auth/reset",
		`{"token":"`+first+`","new_password":"RotateMe123"}`)
	require.Equal(t, http.StatusOK, w.Code)

	// Both tokens should now be marked used (the second one is
	// swept by the "invalidate other tokens" clause).
	var unused int
	require.NoError(t, database.DB.QueryRow(
		`SELECT COUNT(*) FROM password_reset_tokens WHERE used_at IS NULL`,
	).Scan(&unused))
	assert.Equal(t, 0, unused)
}

func TestValidatePasswordPolicy(t *testing.T) {
	cases := []struct {
		pwd     string
		wantErr bool
	}{
		{"1234567", true},   // too short
		{"12345678", false}, // 8 chars + digit
		{"onlyletters", true},
		{"a1", true},
		{strings.Repeat("a1", 65), true}, // 130 chars
		{strings.Repeat("a1", 64), false}, // 128 chars
		{"", true},
		{"MiContraseñaSegura1", false},
	}
	for _, c := range cases {
		err := validatePasswordPolicy(c.pwd)
		if c.wantErr {
			assert.Error(t, err, "expected error for %q", c.pwd)
		} else {
			assert.NoError(t, err, "expected no error for %q", c.pwd)
		}
	}
}

func TestBuildResetURL_PrefersEnvVar(t *testing.T) {
	prev := os.Getenv("FRONTEND_BASE_URL")
	t.Setenv("FRONTEND_BASE_URL", "https://app.example.com")
	defer os.Setenv("FRONTEND_BASE_URL", prev)

	req, _ := http.NewRequest("POST", "/auth/forgot", nil)
	url := buildResetURL(req, "abc123")
	assert.True(t, strings.HasPrefix(url, "https://app.example.com/reset?token="),
		"expected env var prefix, got %s", url)
	assert.Contains(t, url, "token=abc123")
}

func TestBuildResetURL_FallsBackToRequestHost(t *testing.T) {
	prev := os.Getenv("FRONTEND_BASE_URL")
	os.Unsetenv("FRONTEND_BASE_URL")
	defer os.Setenv("FRONTEND_BASE_URL", prev)

	req, _ := http.NewRequest("POST", "/auth/forgot", nil)
	req.Host = "localhost:5173"
	req.Header.Set("X-Forwarded-Proto", "https")
	url := buildResetURL(req, "abc")
	assert.True(t, strings.HasPrefix(url, "https://localhost:5173/reset"),
		"got %s", url)
}
