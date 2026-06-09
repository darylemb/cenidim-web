package handlers

import (
	"database/sql"
	"net/http"
	"strings"
	"sync"
	"time"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/daryl/cenidim-go-api/middleware"
	"github.com/daryl/cenidim-go-api/models"
	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
)

const tokenTTL = 24 * time.Hour

type rateLimitEntry struct {
	count    int
	lastSeen time.Time
}

var (
	loginAttempts    = make(map[string]*rateLimitEntry)
	loginAttemptsMtx sync.Mutex
	loginMaxAttempts = 5
	loginWindow      = 5 * time.Minute
)

func getClientIP(c *gin.Context) string {
	if xff := c.GetHeader("X-Forwarded-For"); xff != "" {
		parts := strings.Split(xff, ",")
		return strings.TrimSpace(parts[0])
	}
	return c.ClientIP()
}

func isRateLimited(key string) bool {
	loginAttemptsMtx.Lock()
	defer loginAttemptsMtx.Unlock()

	entry, exists := loginAttempts[key]
	if !exists {
		loginAttempts[key] = &rateLimitEntry{count: 1, lastSeen: time.Now()}
		return false
	}

	if time.Since(entry.lastSeen) > loginWindow {
		entry.count = 1
		entry.lastSeen = time.Now()
		return false
	}

	entry.count++
	entry.lastSeen = time.Now()

	return entry.count > loginMaxAttempts
}

func cleanupLoginAttempts() {
	loginAttemptsMtx.Lock()
	defer loginAttemptsMtx.Unlock()

	for key, entry := range loginAttempts {
		if time.Since(entry.lastSeen) > loginWindow {
			delete(loginAttempts, key)
		}
	}
}

func init() {
	go func() {
		ticker := time.NewTicker(1 * time.Minute)
		for range ticker.C {
			cleanupLoginAttempts()
		}
	}()
}

// Register godoc
// @Summary Register a new user
// @Tags auth
// @Accept json
// @Produce json
// @Param input body models.UserInput true "Registration data"
// @Success 201 {object} map[string]interface{}
// @Failure 400 {object} map[string]string
// @Failure 409 {object} map[string]string
// @Router /auth/register [post]
func Register(c *gin.Context) {
	if isRateLimited(getClientIP(c)) {
		c.JSON(http.StatusTooManyRequests, gin.H{"error": "Too many requests, please try again later"})
		return
	}

	var input models.UserInput
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request data"})
		return
	}

	// Default role is viewer; only admins can set other roles via admin endpoint
	role := "viewer"

	hash, err := bcrypt.GenerateFromPassword([]byte(input.Password), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error processing password"})
		return
	}

	res, err := database.DB.Exec(
		`INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)`,
		input.Username, input.Email, string(hash), role,
	)
	if err != nil {
		c.JSON(http.StatusConflict, gin.H{"error": "Username or email already exists"})
		return
	}

	id, _ := res.LastInsertId()
	token, err := generateToken(int(id), input.Username, role)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error generating token"})
		return
	}

	c.JSON(http.StatusCreated, gin.H{
		"token": token,
		"user":  gin.H{"id": id, "username": input.Username, "email": input.Email, "role": role},
	})
}

// Login godoc
// @Summary Login
// @Tags auth
// @Accept json
// @Produce json
// @Param input body models.LoginInput true "Credentials"
// @Success 200 {object} map[string]interface{}
// @Failure 400 {object} map[string]string
// @Failure 401 {object} map[string]string
// @Router /auth/login [post]
func Login(c *gin.Context) {
	if isRateLimited(getClientIP(c)) {
		c.JSON(http.StatusTooManyRequests, gin.H{"error": "Too many requests, please try again later"})
		return
	}

	var input models.LoginInput
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request data"})
		return
	}

	var id int
	var username, email, hash, role string
	err := database.DB.QueryRow(
		`SELECT id, username, email, password_hash, role FROM users WHERE username = ?`,
		input.Username,
	).Scan(&id, &username, &email, &hash, &role)

	if err == sql.ErrNoRows {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
		return
	}

	// Google-only accounts have a sentinel password hash and must use the
	// "Continuar con Google" flow instead of the password form.
	if hash == googleLinkedSentinel {
		c.JSON(http.StatusUnauthorized, gin.H{
			"error": "Esta cuenta solo puede iniciar sesión con Google.",
		})
		return
	}

	if hashErr := bcrypt.CompareHashAndPassword([]byte(hash), []byte(input.Password)); hashErr != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

	// Audit: record the sign-in method.
	_, _ = database.DB.Exec(
		`UPDATE users SET last_sign_in_method = ?, last_sign_in_at = ? WHERE id = ?`,
		"password", time.Now().UTC().Format(time.RFC3339), id,
	)

	token, err := generateToken(id, username, role)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error generating token"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"token": token,
		"user":  gin.H{"id": id, "username": username, "email": email, "role": role},
	})
}

// Me godoc
// @Summary Get current user profile
// @Tags auth
// @Security BearerAuth
// @Produce json
// @Success 200 {object} models.User
// @Router /auth/me [get]
func Me(c *gin.Context) {
	userID, _ := c.Get("userID")
	var u models.User
	err := database.DB.QueryRow(
		`SELECT id, username, email, role, created_at FROM users WHERE id = ?`, userID,
	).Scan(&u.ID, &u.Username, &u.Email, &u.Role, &u.CreatedAt)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}
	c.JSON(http.StatusOK, u)
}

func generateToken(userID int, username, role string) (string, error) {
	claims := middleware.Claims{
		UserID:   userID,
		Username: username,
		Role:     role,
		RegisteredClaims: jwt.RegisteredClaims{
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(tokenTTL)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(middleware.JWTSecret())
}

// googleLinkedSentinel is the value stored in `users.password_hash` for
// accounts that were created via Google sign-in. The password login route
// short-circuits when it sees this value and returns a clear error.
const googleLinkedSentinel = "GOOGLE_LINKED"
