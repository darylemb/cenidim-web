package handlers

import (
	"context"
	"crypto/rand"
	"encoding/base64"
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
	"google.golang.org/api/idtoken"
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
// are missing. The verifier performs full JWKS-based signature verification
// against Google's public certs (RS256/ES256), audience check, and issuer
// check. Use NewGoogleOAuthClientWithVerifier in tests to inject a stub.
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
		verifier: newGoogleIDTokenVerifier(env.ClientID),
	}, nil
}

// NewGoogleOAuthClientWithVerifier is the test-only constructor that lets
// callers swap the production JWKS verifier for a stub. Production code must
// use NewGoogleOAuthClient.
func NewGoogleOAuthClientWithVerifier(env GoogleOAuthEnv, v idTokenVerifier) *GoogleOAuthClient {
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
		verifier: v,
	}
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

// googleIDTokenVerifier validates Google-issued ID tokens using the official
// google.golang.org/api/idtoken library. It checks the RSA/ECDSA signature
// against Google's JWKS, the `aud` claim, the `exp` claim, and the `iss`
// claim. Without the signature check, an attacker holding the OAuth `code`
// (or anyone able to intercept the redirect over HTTP) could forge a token
// claiming any email — including an admin's — and the backend would happily
// accept it. Do not replace this with a payload-only parser.
type googleIDTokenVerifier struct {
	aud       string
	validator *idtoken.Validator
}

func newGoogleIDTokenVerifier(aud string) *googleIDTokenVerifier {
	v, err := idtoken.NewValidator(context.Background())
	if err != nil {
		// Without a validator we cannot verify signatures. We intentionally
		// fall back to a rejecting stub rather than silently skipping the
		// check — that would be a worse failure mode (forged tokens).
		return &googleIDTokenVerifier{aud: aud, validator: nil}
	}
	return &googleIDTokenVerifier{aud: aud, validator: v}
}

// validGoogleIssuers is the small set of `iss` values Google emits for
// user-facing OAuth. idtoken.Validate does not enforce `iss`, so we do it
// here to keep the backend from accepting tokens minted by, e.g., a
// non-Google IdP that happens to use the same audience.
var validGoogleIssuers = map[string]bool{
	"https://accounts.google.com": true,
	"accounts.google.com":         true,
}

func (v *googleIDTokenVerifier) Verify(ctx context.Context, raw string) (*GoogleIDTokenClaims, error) {
	if raw == "" {
		return nil, errors.New("empty id_token")
	}
	if v.validator == nil {
		return nil, errors.New("idtoken validator unavailable")
	}
	payload, err := v.validator.Validate(ctx, raw, v.aud)
	if err != nil {
		return nil, fmt.Errorf("validate id_token: %w", err)
	}
	if !validGoogleIssuers[payload.Issuer] {
		return nil, fmt.Errorf("unexpected issuer %q", payload.Issuer)
	}
	if payload.Subject == "" {
		return nil, errors.New("missing sub claim")
	}
	c := &GoogleIDTokenClaims{
		Sub:   payload.Subject,
		Aud:   payload.Audience,
		Email: stringClaim(payload.Claims, "email"),
		Name:  stringClaim(payload.Claims, "name"),
	}
	if v, ok := payload.Claims["email_verified"].(bool); ok {
		c.EmailVerified = v
	}
	if v, ok := payload.Claims["given_name"].(string); ok {
		c.GivenName = v
	}
	if v, ok := payload.Claims["family_name"].(string); ok {
		c.FamilyName = v
	}
	if v, ok := payload.Claims["picture"].(string); ok {
		c.Picture = v
	}
	return c, nil
}

func stringClaim(claims map[string]interface{}, key string) string {
	if v, ok := claims[key].(string); ok {
		return v
	}
	return ""
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
	// Secure flag is set automatically when the request is HTTPS — we
	// honor both the direct `c.Request.TLS != nil` case (rare; only when
	// the Go server is exposed on the public interface) and the common
	// reverse-proxy case via the standard `X-Forwarded-Proto` header so
	// production deployments behind Cloudflare, Nginx, or Coolify all
	// get the flag set correctly.
	cookie := &http.Cookie{
		Name:     oauthStateCookie,
		Value:    state,
		Path:     "/api/auth/google",
		MaxAge:   oauthStateMaxAge,
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
	}
	if c.Request.TLS != nil || strings.EqualFold(c.GetHeader("X-Forwarded-Proto"), "https") {
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
