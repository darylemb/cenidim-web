package handlers

import (
	"crypto/rand"
	"crypto/sha256"
	"database/sql"
	"encoding/base64"
	"encoding/hex"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/gin-gonic/gin"
	"golang.org/x/crypto/bcrypt"
)

// passwordResetTTL is how long a reset link is valid. An hour is the
// de-facto standard; long enough for the user to fetch the email and
// type the new password, short enough to limit the blast radius of a
// leaked link.
const passwordResetTTL = 1 * time.Hour

// requestPasswordResetRequest is the body of POST /api/auth/forgot.
// We accept only email — the response is always 200 to avoid user
// enumeration. The email existence is checked server-side and
// silently skipped if not found.
type requestPasswordResetRequest struct {
	Email string `json:"email"`
}

// resetPasswordRequest is the body of POST /api/auth/reset.
type resetPasswordRequest struct {
	Token       string `json:"token"`
	NewPassword string `json:"new_password"`
}

// ForgotPassword godoc
// @Summary Request a password-reset email
// @Description Issues a one-shot reset token and writes a recovery
// @Description email to the email_outbox table. Always returns 200
// @Description unless the payload is malformed (avoid user
// @Description enumeration). In demo mode the reset link is also
// @Description logged to stdout so the operator can copy/paste it
// @Description without reading the DB.
// @Tags auth
// @Accept json
// @Produce json
// @Param input body requestPasswordResetRequest true "Email to recover"
// @Success 200 {object} map[string]interface{}
// @Failure 400 {object} map[string]string
// @Router /auth/forgot [post]
func ForgotPassword(c *gin.Context) {
	var body requestPasswordResetRequest
	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request data"})
		return
	}
	body.Email = strings.TrimSpace(strings.ToLower(body.Email))
	if body.Email == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Email is required"})
		return

	}

	// 1. Look up the user. If not found, return 200 silently to
	//    avoid user enumeration.
	var userID int
	var username string
	err := database.DB.QueryRow(
		`SELECT id, username FROM users WHERE email = ?`, body.Email,
	).Scan(&userID, &username)
	if err == sql.ErrNoRows {
		// Generic 200. We deliberately do not log the email here to
		// avoid leaking the enumeration to operators with shell
		// access.
		c.JSON(http.StatusOK, gin.H{"ok": true})
		return
	}
	if err != nil {
		log.Printf("forgot: user lookup failed: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal error"})
		return
	}

	// 2. Generate a 32-byte random token, base64url-encoded (43 chars).
	//    Bcrypt cost 10 — same as the password hash. The plaintext
	//    is sent in the email and never persisted; the DB only stores
	//    the bcrypt hash.
	raw := make([]byte, 32)
	if _, err := rand.Read(raw); err != nil {
		log.Printf("forgot: rand.Read failed: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal error"})
		return
	}
	plaintext := base64.RawURLEncoding.EncodeToString(raw)
	hash, err := bcrypt.GenerateFromPassword([]byte(plaintext), bcrypt.DefaultCost)
	if err != nil {
		log.Printf("forgot: bcrypt failed: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal error"})
		return
	}

	// 3. Persist the token hash. The expires_at is in UTC so the
	//    comparison in step 4 is timezone-safe regardless of where
	//    the backend is hosted.
	expiresAt := time.Now().UTC().Add(passwordResetTTL).Format(time.RFC3339)
	if _, err := database.DB.Exec(
		`INSERT INTO password_reset_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)`,
		userID, string(hash), expiresAt,
	); err != nil {
		log.Printf("forgot: token insert failed: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal error"})
		return
	}

	// 4. Build the reset URL and persist / log the email.
	resetURL := buildResetURL(c.Request, plaintext)
	sendPasswordResetEmail(body.Email, username, resetURL)

	c.JSON(http.StatusOK, gin.H{"ok": true})
}

// ResetPassword godoc
// @Summary Reset password with a valid token
// @Description Consumes a one-shot token (one hour TTL, single use).
// @Description The token is verified against the bcrypt hash stored
// @Description in password_reset_tokens. On success the user's
// @Description password is replaced and any leftover reset tokens
// @Description for that user are invalidated.
// @Tags auth
// @Accept json
// @Produce json
// @Param input body resetPasswordRequest true "Token + new password"
// @Success 200 {object} map[string]string
// @Failure 400 {object} map[string]string
// @Failure 401 {object} map[string]string
// @Router /auth/reset [post]
func ResetPassword(c *gin.Context) {
	var body resetPasswordRequest
	if err := c.ShouldBindJSON(&body); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request data"})
		return
	}
	if body.Token == "" || body.NewPassword == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "token and new_password are required"})
		return
	}
	if err := validatePasswordPolicy(body.NewPassword); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Walk all unexpired, unused tokens for the user and bcrypt-compare
	// the submitted token against each. We do this in SQL because the
	// token_hash is bcrypt — the only way to check is one row at a time
	// and bcrypt is constant-time per row.
	rows, err := database.DB.Query(
		`SELECT id, user_id FROM password_reset_tokens
		 WHERE used_at IS NULL AND expires_at > datetime('now')`,
	)
	if err != nil {
		log.Printf("reset: token query failed: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal error"})
		return
	}
	type tokenRow struct {
		id    int
		user  int
		hash  string
	}
	var match *tokenRow
	for rows.Next() {
		var id, user int
		if scanErr := rows.Scan(&id, &user); scanErr != nil {
			continue
		}
		// We need the hash to compare. Re-query just the hash for this
		// row to keep the iteration simple.
		var hash string
		if err := database.DB.QueryRow(
			`SELECT token_hash FROM password_reset_tokens WHERE id = ?`, id,
		).Scan(&hash); err != nil {
			continue
		}
		if bcrypt.CompareHashAndPassword([]byte(hash), []byte(body.Token)) == nil {
			match = &tokenRow{id: id, user: user, hash: hash}
			break
		}
	}
	// Close the cursor BEFORE opening the transaction below so the
	// single connection in the pool is available for BeginTxWithRetry.
	_ = rows.Close()

	if match == nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Token inválido o expirado"})
		return
	}

	// Mark the token used, rotate the password, and invalidate any
	// other unexpired tokens for the same user — all in one
	// transaction so a crash halfway leaves no half-updated row.
	tx, err := database.BeginTxWithRetry()
	if err != nil {
		log.Printf("reset: begin tx failed: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal error"})
		return
	}
	if _, err := tx.Exec(
		`UPDATE password_reset_tokens SET used_at = ? WHERE id = ?`,
		time.Now().UTC().Format(time.RFC3339), match.id,
	); err != nil {
		_ = tx.Rollback()
		log.Printf("reset: mark-used failed: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal error"})
		return
	}
	newHash, err := bcrypt.GenerateFromPassword([]byte(body.NewPassword), bcrypt.DefaultCost)
	if err != nil {
		_ = tx.Rollback()
		log.Printf("reset: bcrypt failed: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal error"})
		return
	}
	if _, err := tx.Exec(
		`UPDATE users SET password_hash = ?, last_sign_in_at = ? WHERE id = ?`,
		string(newHash), time.Now().UTC().Format(time.RFC3339), match.user,
	); err != nil {
		_ = tx.Rollback()
		log.Printf("reset: rotate-password failed: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal error"})
		return
	}
	if _, err := tx.Exec(
		`UPDATE password_reset_tokens SET used_at = ? WHERE user_id = ? AND used_at IS NULL`,
		time.Now().UTC().Format(time.RFC3339), match.user,
	); err != nil {
		_ = tx.Rollback()
		log.Printf("reset: invalidate-tokens failed: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal error"})
		return
	}
	if err := tx.Commit(); err != nil {
		log.Printf("reset: commit failed: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Internal error"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"ok": true})
}

// validatePasswordPolicy enforces the basic constraints. Bcrypt's
// 72-byte input cap is enforced implicitly by truncating; we cap at
// 128 to be safe and require a minimum of 8 chars plus at least one
// digit so a leaked DB doesn't reveal anything predictable.
func validatePasswordPolicy(p string) error {
	if len(p) < 8 {
		return fmt.Errorf("password must be at least 8 characters")
	}
	if len(p) > 128 {
		return fmt.Errorf("password must be at most 128 characters")
	}
	hasDigit := false
	for _, r := range p {
		if r >= '0' && r <= '9' {
			hasDigit = true
			break
		}
	}
	if !hasDigit {
		return fmt.Errorf("password must include at least one digit")
	}
	return nil
}

// buildResetURL composes the absolute URL the user will click. The
// FRONTEND_BASE_URL env var is the production origin; in dev we fall
// back to reading the Host header (so the link works on any localhost
// port).
func buildResetURL(req *http.Request, token string) string {
	base := strings.TrimRight(os.Getenv("FRONTEND_BASE_URL"), "/")
	if base == "" {
		scheme := "http"
		if req.TLS != nil || strings.EqualFold(req.Header.Get("X-Forwarded-Proto"), "https") {
			scheme = "https"
		}
		host := req.Header.Get("X-Forwarded-Host")
		if host == "" {
			host = req.Host
		}
		base = scheme + "://" + host
	}
	u, err := url.Parse(base + "/reset")
	if err != nil {
		return base + "/reset?token=" + url.QueryEscape(token)
	}
	q := u.Query()
	q.Set("token", token)
	u.RawQuery = q.Encode()
	return u.String()
}

// sendPasswordResetEmail persists the would-be email in email_outbox
// (so the admin can inspect it via the dashboard) and, in demo mode
// (no SMTP_HOST set), logs the link to stdout. When SMTP_HOST is set,
// the real send is wired up here — currently out of scope.
func sendPasswordResetEmail(to, username, resetURL string) {
	subject := "CENIDIM — Recupera tu contraseña"
	body := buildPasswordResetBody(username, resetURL)
	bodyHTML := buildPasswordResetHTML(username, resetURL)

	// 1. Persist to email_outbox (admin can inspect via /api/admin/emails).
	if _, err := database.DB.Exec(
		`INSERT INTO email_outbox
		 (to_addr, subject, body_text, body_html, kind, related_user_id)
		 VALUES (?, ?, ?, ?, 'password_reset',
		         (SELECT id FROM users WHERE email = ?))`,
		to, subject, body, bodyHTML, to,
	); err != nil {
		log.Printf("forgot: outbox insert failed: %v", err)
	}

	// 2. Demo path: log to stdout so operators can copy/paste the link
	//    without DB access.
	if os.Getenv("EMAIL_DEMO") == "1" || os.Getenv("SMTP_HOST") == "" {
		log.Printf("DEV EMAIL OUTBOX: to=%s subject=%q", to, subject)
		log.Printf("DEV EMAIL OUTBOX: link=%s", resetURL)
		return
	}

	// 3. Real SMTP path would go here (out of scope for the demo).
	log.Printf("forgot: SMTP send not implemented in demo build; "+
		"email persisted in email_outbox (id above) for inspection")
}

// tokenFingerprint returns the first 8 hex chars of the SHA-256 of
// the plaintext token. Used only in log lines — never store the
// plaintext or its full hash in the audit log.
func tokenFingerprint(token string) string {
	sum := sha256.Sum256([]byte(token))
	return hex.EncodeToString(sum[:4])
}

// parseIntFromPath extracts the last integer in an HTTP path segment.
// Used by tests to assert that the audit log mentions a user.
func parseIntFromPath(p string) int {
	parts := strings.Split(p, "/")
	for i := len(parts) - 1; i >= 0; i-- {
		if n, err := strconv.Atoi(parts[i]); err == nil {
			return n
		}
	}
	return 0
}

func buildPasswordResetBody(username, resetURL string) string {
	return fmt.Sprintf(
		"Hola %s,\n\n" +
			"Recibimos una solicitud para restablecer la contraseña de tu cuenta en el CENIDIM.\n\n" +
			"Para continuar, abrí este enlace en tu navegador (caduca en 1 hora, un solo uso):\n" +
			"%s\n\n" +
			"Si no solicitaste este cambio, podés ignorar este mensaje.\n\n" +
			"— CENIDIM Archivo Musical\n",
		username, resetURL,
	)
}

func buildPasswordResetHTML(username, resetURL string) string {
	return fmt.Sprintf(
		`<!doctype html><html><body style="font-family: system-ui, sans-serif; max-width: 560px; margin: 2em auto; color: #1a1612;">`+
			`<h1 style="font-size: 1.4em;">Hola %s,</h1>`+
			`<p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en el CENIDIM.</p>`+
			`<p style="margin: 2em 0;"><a href="%s" style="background: #751428; color: #faf7f0; padding: 0.75em 1.5em; text-decoration: none; border-radius: 2px;">Restablecer contraseña</a></p>`+
			`<p style="color: #666; font-size: 0.9em;">El enlace caduca en 1 hora y es de un solo uso. Si no solicitaste este cambio, podés ignorar este mensaje.</p>`+
			`<p style="color: #999; font-size: 0.8em;">— CENIDIM Archivo Musical</p>`+
			`</body></html>`,
		username, resetURL,
	)
}
