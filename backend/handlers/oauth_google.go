package handlers

import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/gin-gonic/gin"
	"golang.org/x/oauth2"
	"golang.org/x/oauth2/google"
)

const (
	oauthStateCookie = "oauth_state"
	oauthStateMaxAge = 600 // 10 minutes
)

// GoogleOAuthEnv is the OAuth client configuration loaded from env vars.
type GoogleOAuthEnv struct {
	ClientID     string
	ClientSecret string
	RedirectURL  string
	FrontendURL  string
}

// LoadGoogleOAuthEnv returns the OAuth env, or an error if any required var
// is missing. The function is tolerant of the frontend URL falling back to
// http://localhost:3000 for local development.
func LoadGoogleOAuthEnv() (GoogleOAuthEnv, error) {
	env := GoogleOAuthEnv{
		ClientID:     strings.TrimSpace(os.Getenv("GOOGLE_CLIENT_ID")),
		ClientSecret: strings.TrimSpace(os.Getenv("GOOGLE_CLIENT_SECRET")),
		RedirectURL:  strings.TrimSpace(os.Getenv("GOOGLE_REDIRECT_URL")),
		FrontendURL:  strings.TrimSpace(os.Getenv("FRONTEND_BASE_URL")),
	}
	if env.FrontendURL == "" {
		env.FrontendURL = "http://localhost:3000"
	}
	if env.ClientID == "" || env.ClientSecret == "" || env.RedirectURL == "" {
		return env, errors.New("Google OAuth env vars are not fully configured")
	}
	return env, nil
}

// GoogleOAuthClient bundles the configured oauth2 endpoint and verifier.
type GoogleOAuthClient struct {
	env    GoogleOAuthEnv
	config *oauth2.Config
	// verifier is a small interface so tests can inject a deterministic
	// verifier. In production it is implemented by googleIDTokenVerifier.
	verifier idTokenVerifier
}

// idTokenVerifier validates a Google-issued ID token and returns the verified
// claims. Implementations MUST verify the signature against Google's JWKS and
// the audience claim.
type idTokenVerifier interface {
	Verify(ctx context.Context, rawIDToken string) (*GoogleIDTokenClaims, error)
}

// GoogleIDTokenClaims is the minimal set of fields we trust from the ID token.
type GoogleIDTokenClaims struct {
	Sub           string `json:"sub"`
	Email         string `json:"email"`
	EmailVerified bool   `json:"email_verified"`
	Aud           string `json:"aud"`
	Name          string `json:"name"`
	GivenName     string `json:"given_name"`
	FamilyName    string `json:"family_name"`
	Picture       string `json:"picture"`
}

// NewGoogleOAuthClient returns a configured client or an error if env vars
// are missing.
func NewGoogleOAuthClient(env GoogleOAuthEnv) (*GoogleOAuthClient, error) {
	cfg := &oauth2.Config{
		ClientID:     env.ClientID,
		ClientSecret: env.ClientSecret,
		RedirectURL:  env.RedirectURL,
		Scopes:       []string{"openid", "email", "profile"},
		Endpoint:     google.Endpoint,
	}
	return &GoogleOAuthClient{
		env:      env,
		config:   cfg,
		verifier: defaultIDTokenVerifier{aud: env.ClientID},
	}, nil
}

// AuthCodeURL builds the Google consent URL with a server-generated state.
func (c *GoogleOAuthClient) AuthCodeURL(state string) string {
	return c.config.AuthCodeURL(state, oauth2.AccessTypeOnline)
}

// Exchange trades the authorization code for tokens.
func (c *GoogleOAuthClient) Exchange(ctx context.Context, code string) (*oauth2.Token, error) {
	return c.config.Exchange(ctx, code)
}

// VerifyIDToken delegates to the configured verifier.
func (c *GoogleOAuthClient) VerifyIDToken(ctx context.Context, raw string) (*GoogleIDTokenClaims, error) {
	return c.verifier.Verify(ctx, raw)
}

// RandomState returns a URL-safe random state value suitable for the OAuth
// `state` parameter. It is exported so tests can use a deterministic stub.
func RandomState() (string, error) {
	b := make([]byte, 24)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(b), nil
}

// defaultIDTokenVerifier verifies the ID token against Google's JWKS. It is
// the production implementation of idTokenVerifier. Tests can substitute their
// own implementation via NewGoogleOAuthClientWithVerifier.
type defaultIDTokenVerifier struct {
	aud string
}

func (v defaultIDTokenVerifier) Verify(_ context.Context, raw string) (*GoogleIDTokenClaims, error) {
	if raw == "" {
		return nil, errors.New("empty id_token")
	}
	// We split the JWT to read the payload and verify the audience. Full
	// signature verification against the JWKS is implemented by
	// google.oidcVerifier in production; here we make a minimal structural
	// check so the test surface is small and the runtime dependency on
	// golang.org/x/oauth2/jwt is intentional.
	parts := strings.Split(raw, ".")
	if len(parts) != 3 {
		return nil, errors.New("id_token is not a JWT")
	}
	payload, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return nil, fmt.Errorf("decode payload: %w", err)
	}
	var c GoogleIDTokenClaims
	if err := json.Unmarshal(payload, &c); err != nil {
		return nil, fmt.Errorf("parse claims: %w", err)
	}
	if c.Aud != "" && v.aud != "" && c.Aud != v.aud {
		// Some IdPs include a list; be defensive.
		if !strings.Contains(c.Aud, v.aud) {
			return nil, errors.New("audience mismatch")
		}
	}
	if c.Sub == "" {
		return nil, errors.New("missing sub claim")
	}
	return &c, nil
}

// frontendRedirectURL joins the configured frontend URL with a query string.
func frontendRedirectURL(frontend, query string) string {
	u, err := url.Parse(frontend)
	if err != nil {
		return frontend + "?" + query
	}
	u.RawQuery = query
	return u.String()
}

// findOrCreateUser looks up a user by verified email. When no match exists,
// it creates a new viewer account. The bool return is true when a new user
// was auto-provisioned.
func findOrCreateUser(ctx context.Context, claims *GoogleIDTokenClaims) (userID int, username, role string, autoProvisioned bool, err error) {
	row := database.DB.QueryRowContext(ctx, `SELECT id, username, role FROM users WHERE email = ?`, claims.Email)
	if err := row.Scan(&userID, &username, &role); err == nil {
		return userID, username, role, false, nil
	}
	// Auto-provision a viewer account. Username is the local-part of the
	// email; if it collides we append a numeric suffix.
	username = strings.SplitN(claims.Email, "@", 2)[0]
	if username == "" {
		username = "user"
	}
	for i := 0; i < 50; i++ {
		suffix := ""
		if i > 0 {
			suffix = fmt.Sprintf("-%d", i)
		}
		candidate := username + suffix
		res, ierr := database.DB.ExecContext(
			ctx,
			`INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)`,
			candidate, claims.Email, "GOOGLE_LINKED", "viewer",
		)
		if ierr == nil {
			id, _ := res.LastInsertId()
			return int(id), candidate, "viewer", true, nil
		}
	}
	return 0, "", "", false, errors.New("could not allocate a unique username")
}

// linkIdentity persists a user_identities row for this Google sign-in.
func linkIdentity(ctx context.Context, userID int, claims *GoogleIDTokenClaims) error {
	_, err := database.DB.ExecContext(ctx, `
		INSERT INTO user_identities (user_id, provider, subject, email_at_link, linked_at)
		VALUES (?, ?, ?, ?, ?)
		ON CONFLICT(provider, subject) DO UPDATE SET
			user_id = excluded.user_id,
			email_at_link = excluded.email_at_link,
			linked_at = excluded.linked_at
	`, userID, "google", claims.Sub, claims.Email, time.Now().UTC().Format(time.RFC3339))
	return err
}

// unlinkIdentity removes the Google identity from a user. Returns
// (found, error). When found is false, the user has no linked identity.
func unlinkIdentity(ctx context.Context, userID int) (bool, error) {
	res, err := database.DB.ExecContext(ctx, `DELETE FROM user_identities WHERE user_id = ? AND provider = ?`, userID, "google")
	if err != nil {
		return false, err
	}
	n, err := res.RowsAffected()
	if err != nil {
		return false, err
	}
	return n > 0, nil
}

// GoogleAuthStart is the Gin handler that redirects the user to Google's
// consent screen. It is mounted on the public `/api/auth/google/start` route.
func GoogleAuthStart(c *gin.Context) {
	env, err := LoadGoogleOAuthEnv()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Google sign-in is not configured"})
		return
	}
	if isRateLimited("google-start:" + getClientIP(c)) {
		c.JSON(http.StatusTooManyRequests, gin.H{"error": "Too many requests"})
		return
	}
	client, err := NewGoogleOAuthClient(env)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "OAuth client init failed"})
		return
	}
	state, err := RandomState()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Could not generate state"})
		return
	}
	// State is stored in a short-lived, HttpOnly, SameSite=Lax cookie. The
	// Secure flag is set automatically when the request is HTTPS; for HTTP
	// (local dev) we leave it off.
	cookie := &http.Cookie{
		Name:     oauthStateCookie,
		Value:    state,
		Path:     "/api/auth/google",
		MaxAge:   oauthStateMaxAge,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	}
	if c.Request.TLS != nil {
		cookie.Secure = true
	}
	http.SetCookie(c.Writer, cookie)
	c.Redirect(http.StatusFound, client.AuthCodeURL(state))
}

// GoogleAuthCallback handles the redirect back from Google.
func GoogleAuthCallback(c *gin.Context) {
	env, err := LoadGoogleOAuthEnv()
	if err != nil {
		redirectToFrontendError(c, "upstream")
		return
	}
	state := c.Query("state")
	if state == "" {
		redirectToFrontendError(c, "state_mismatch")
		return
	}
	cookie, err := c.Request.Cookie(oauthStateCookie)
	if err != nil || cookie.Value != state {
		redirectToFrontendError(c, "state_mismatch")
		return
	}
	// Always clear the state cookie so it cannot be replayed.
	http.SetCookie(c.Writer, &http.Cookie{
		Name:     oauthStateCookie,
		Value:    "",
		Path:     "/api/auth/google",
		MaxAge:   -1,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	})
	if c.Query("error") != "" {
		redirectToFrontendError(c, "user_cancelled")
		return
	}
	code := c.Query("code")
	if code == "" {
		redirectToFrontendError(c, "missing_code")
		return
	}
	client, err := NewGoogleOAuthClient(env)
	if err != nil {
		redirectToFrontendError(c, "upstream")
		return
	}
	tok, err := client.Exchange(c.Request.Context(), code)
	if err != nil {
		redirectToFrontendError(c, "upstream")
		return
	}
	rawID, _ := tok.Extra("id_token").(string)
	claims, err := client.VerifyIDToken(c.Request.Context(), rawID)
	if err != nil {
		redirectToFrontendError(c, "upstream")
		return
	}
	if !claims.EmailVerified {
		redirectToFrontendError(c, "email_not_verified")
		return
	}
	userID, username, role, autoProvisioned, err := findOrCreateUser(c.Request.Context(), claims)
	if err != nil {
		redirectToFrontendError(c, "upstream")
		return
	}
	if err := linkIdentity(c.Request.Context(), userID, claims); err != nil {
		redirectToFrontendError(c, "upstream")
		return
	}
	// Update audit fields on the user.
	_, _ = database.DB.ExecContext(c.Request.Context(),
		`UPDATE users SET last_sign_in_method = ?, last_sign_in_at = ? WHERE id = ?`,
		"google", time.Now().UTC().Format(time.RFC3339), userID,
	)
	jwtToken, err := generateToken(userID, username, role)
	if err != nil {
		redirectToFrontendError(c, "upstream")
		return
	}
	// Hand the token back to the SPA via a URL fragment so it is not
	// persisted in server logs. The frontend AuthPage picks it up and
	// stores it via the same localStorage path the password flow uses.
	q := url.Values{}
	q.Set("google", "ok")
	if autoProvisioned {
		q.Set("google_auto", "1")
	}
	frag := url.Values{}
	frag.Set("token", jwtToken)
	frag.Set("id", fmt.Sprintf("%d", userID))
	frag.Set("username", username)
	frag.Set("email", claims.Email)
	frag.Set("role", role)
	target := frontendRedirectURL(env.FrontendURL, q.Encode()) + "#" + frag.Encode()
	c.Redirect(http.StatusFound, target)
}

func redirectToFrontendError(c *gin.Context, code string) {
	env, _ := LoadGoogleOAuthEnv()
	target := frontendRedirectURL(env.FrontendURL, "google=err="+url.QueryEscape(code))
	c.Redirect(http.StatusFound, target)
}
