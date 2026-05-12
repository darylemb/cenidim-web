package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/daryl/cenidim-go-api/middleware"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func setupAuthRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	r.POST("/auth/register", Register)
	r.POST("/auth/login", Login)
	authGroup := r.Group("/auth")
	authGroup.Use(middleware.RequireAuth())
	authGroup.GET("/me", Me)
	return r
}

func TestRegister(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAuthRouter()

	body := `{"username":"testuser","email":"test@test.com","password":"secret123"}`
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/auth/register", bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)

	require.Equal(t, http.StatusCreated, w.Code)
	var resp map[string]interface{}
	require.NoError(t, json.Unmarshal(w.Body.Bytes(), &resp))
	assert.NotEmpty(t, resp["token"])
	user := resp["user"].(map[string]interface{})
	assert.Equal(t, "testuser", user["username"])
	assert.Equal(t, "viewer", user["role"]) // default role
}

func TestRegisterDuplicate(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAuthRouter()

	body := `{"username":"dup","email":"dup@test.com","password":"pass12345"}`
	for i := 0; i < 2; i++ {
		w := httptest.NewRecorder()
		req, _ := http.NewRequest("POST", "/auth/register", bytes.NewBufferString(body))
		req.Header.Set("Content-Type", "application/json")
		r.ServeHTTP(w, req)
		if i == 0 {
			assert.Equal(t, http.StatusCreated, w.Code)
		} else {
			assert.Equal(t, http.StatusConflict, w.Code)
		}
	}
}

func TestLogin(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAuthRouter()

	// Register first
	regBody := `{"username":"loginuser","email":"login@test.com","password":"mypassword"}`
	regReq, _ := http.NewRequest("POST", "/auth/register", bytes.NewBufferString(regBody))
	regReq.Header.Set("Content-Type", "application/json")
	regW := httptest.NewRecorder()
	r.ServeHTTP(regW, regReq)
	require.Equal(t, http.StatusCreated, regW.Code)

	// Login with correct password
	loginBody := `{"username":"loginuser","password":"mypassword"}`
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/auth/login", bytes.NewBufferString(loginBody))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)

	require.Equal(t, http.StatusOK, w.Code)
	var resp map[string]interface{}
	require.NoError(t, json.Unmarshal(w.Body.Bytes(), &resp))
	assert.NotEmpty(t, resp["token"])
	user := resp["user"].(map[string]interface{})
	assert.Equal(t, "loginuser", user["username"])
}

func TestLoginWrongPassword(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAuthRouter()

	regBody := `{"username":"pwduser","email":"pwd@test.com","password":"correctpass"}`
	regReq, _ := http.NewRequest("POST", "/auth/register", bytes.NewBufferString(regBody))
	regReq.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(httptest.NewRecorder(), regReq)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/auth/login", bytes.NewBufferString(`{"username":"pwduser","password":"wrong"}`))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)
	assert.Equal(t, http.StatusUnauthorized, w.Code)
}

func TestLoginNotFound(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAuthRouter()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/auth/login", bytes.NewBufferString(`{"username":"nobody","password":"x"}`))
	req.Header.Set("Content-Type", "application/json")
	r.ServeHTTP(w, req)
	assert.Equal(t, http.StatusUnauthorized, w.Code)
}

func TestMe(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAuthRouter()

	// Register to create a real user in the DB with a valid token
	regBody := `{"username":"meuser","email":"me@test.com","password":"mepassword"}`
	regReq, _ := http.NewRequest("POST", "/auth/register", bytes.NewBufferString(regBody))
	regReq.Header.Set("Content-Type", "application/json")
	regW := httptest.NewRecorder()
	r.ServeHTTP(regW, regReq)
	require.Equal(t, http.StatusCreated, regW.Code)

	var regResp map[string]interface{}
	require.NoError(t, json.Unmarshal(regW.Body.Bytes(), &regResp))
	token := regResp["token"].(string)

	// Call /auth/me with the token
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/auth/me", nil)
	req.Header.Set("Authorization", "Bearer "+token)
	r.ServeHTTP(w, req)

	require.Equal(t, http.StatusOK, w.Code)
	var userResp map[string]interface{}
	require.NoError(t, json.Unmarshal(w.Body.Bytes(), &userResp))
	assert.Equal(t, "meuser", userResp["username"])
	assert.Equal(t, "viewer", userResp["role"])
}

func TestMeNoToken(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAuthRouter()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/auth/me", nil)
	r.ServeHTTP(w, req)
	assert.Equal(t, http.StatusUnauthorized, w.Code)
}
