package handlers

import (
	"database/sql"
	"net/http"
	"time"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/daryl/cenidim-go-api/middleware"
	"github.com/daryl/cenidim-go-api/models"
	"github.com/gin-gonic/gin"
	"github.com/golang-jwt/jwt/v5"
	"golang.org/x/crypto/bcrypt"
)

const tokenTTL = 24 * time.Hour

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
	var input models.UserInput
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
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
	var input models.LoginInput
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
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

	if hashErr := bcrypt.CompareHashAndPassword([]byte(hash), []byte(input.Password)); hashErr != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
		return
	}

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
