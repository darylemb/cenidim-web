package handlers

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/daryl/cenidim-go-api/middleware"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// setupAdminRouter builds a test router with all admin endpoints behind RequireAuth.
// Role enforcement is exercised separately in middleware tests.
func setupAdminRouter() *gin.Engine {
	gin.SetMode(gin.TestMode)
	r := gin.New()
	admin := r.Group("/admin")
	admin.Use(middleware.RequireAuth())
	{
		admin.GET("/fonogramas", AdminListFonogramas)
		admin.GET("/fonogramas/:id", AdminGetFonograma)
		admin.POST("/fonogramas", AdminCreateFonograma)
		admin.PUT("/fonogramas/:id", AdminUpdateFonograma)
		admin.DELETE("/fonogramas/:id", AdminDeleteFonograma)
		admin.GET("/songs", AdminListSongs)
		admin.POST("/songs", AdminCreateSong)
		admin.PUT("/songs/:id", AdminUpdateSong)
		admin.DELETE("/songs/:id", AdminDeleteSong)
		admin.GET("/users", AdminListUsers)
		admin.POST("/users", AdminCreateUser)
		admin.PUT("/users/:id", AdminUpdateUser)
		admin.DELETE("/users/:id", AdminDeleteUser)
	}
	return r
}

// adminTok generates a JWT for an admin user for use in test requests.
func adminTok(t *testing.T) string {
	t.Helper()
	tok, err := generateToken(1, "admin", "admin")
	require.NoError(t, err)
	return tok
}

// authHeader returns a standard Authorization header value.
func authHeader(token string) string { return "Bearer " + token }

// ─── Fonogramas CRUD ─────────────────────────────────────────────────────────

func TestAdminListFonogramas(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAdminRouter()
	tok := adminTok(t)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/admin/fonogramas", nil)
	req.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(w, req)

	require.Equal(t, http.StatusOK, w.Code)
	var resp map[string]interface{}
	require.NoError(t, json.Unmarshal(w.Body.Bytes(), &resp))
	assert.InDelta(t, float64(1), resp["total"], 0)
}

func TestAdminGetFonograma(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAdminRouter()
	tok := adminTok(t)

	// Existing fonograma
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/admin/fonogramas/1", nil)
	req.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(w, req)
	require.Equal(t, http.StatusOK, w.Code)
	var f map[string]interface{}
	require.NoError(t, json.Unmarshal(w.Body.Bytes(), &f))
	assert.Equal(t, "Test Album", f["titulo"])

	// Non-existent
	w2 := httptest.NewRecorder()
	req2, _ := http.NewRequest("GET", "/admin/fonogramas/999", nil)
	req2.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(w2, req2)
	assert.Equal(t, http.StatusNotFound, w2.Code)
}

func TestAdminCreateFonograma(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAdminRouter()
	tok := adminTok(t)

	body := `{"clave_fonograma":99,"titulo":"New Fonograma","anio":"1975"}`
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/admin/fonogramas", bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(w, req)
	require.Equal(t, http.StatusCreated, w.Code)

	// Duplicate clave should fail
	w2 := httptest.NewRecorder()
	req2, _ := http.NewRequest("POST", "/admin/fonogramas", bytes.NewBufferString(body))
	req2.Header.Set("Content-Type", "application/json")
	req2.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(w2, req2)
	assert.Equal(t, http.StatusConflict, w2.Code)
}

func TestAdminUpdateFonograma(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAdminRouter()
	tok := adminTok(t)

	body := `{"titulo":"Updated Album","anio":"1970"}`
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("PUT", "/admin/fonogramas/1", bytes.NewBufferString(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(w, req)
	require.Equal(t, http.StatusOK, w.Code)

	// Verify the update persisted
	wg := httptest.NewRecorder()
	reqg, _ := http.NewRequest("GET", "/admin/fonogramas/1", nil)
	reqg.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(wg, reqg)
	var f map[string]interface{}
	require.NoError(t, json.Unmarshal(wg.Body.Bytes(), &f))
	assert.Equal(t, "Updated Album", f["titulo"])

	// Non-existent
	w2 := httptest.NewRecorder()
	req2, _ := http.NewRequest("PUT", "/admin/fonogramas/999", bytes.NewBufferString(body))
	req2.Header.Set("Content-Type", "application/json")
	req2.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(w2, req2)
	assert.Equal(t, http.StatusNotFound, w2.Code)
}

func TestAdminDeleteFonograma(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAdminRouter()
	tok := adminTok(t)

	// Delete existing → 200, cascades songs
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("DELETE", "/admin/fonogramas/1", nil)
	req.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(w, req)
	require.Equal(t, http.StatusOK, w.Code)

	// Verify cascade: songs for this fonograma should be gone
	var count int
	require.NoError(t, database.DB.QueryRow("SELECT COUNT(*) FROM songs WHERE fonograma_id = 1").Scan(&count))
	assert.Equal(t, 0, count)

	// Already deleted → 404
	w2 := httptest.NewRecorder()
	req2, _ := http.NewRequest("DELETE", "/admin/fonogramas/1", nil)
	req2.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(w2, req2)
	assert.Equal(t, http.StatusNotFound, w2.Code)
}

func TestAdminNoToken(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAdminRouter()

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/admin/fonogramas", nil)
	r.ServeHTTP(w, req)
	assert.Equal(t, http.StatusUnauthorized, w.Code)
}

// ─── Songs CRUD ───────────────────────────────────────────────────────────────

func TestAdminSongsCRUD(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAdminRouter()
	tok := adminTok(t)

	// List all songs (3 seeded)
	wl := httptest.NewRecorder()
	reql, _ := http.NewRequest("GET", "/admin/songs", nil)
	reql.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(wl, reql)
	require.Equal(t, http.StatusOK, wl.Code)
	var listResp map[string]interface{}
	require.NoError(t, json.Unmarshal(wl.Body.Bytes(), &listResp))
	assert.InDelta(t, float64(3), listResp["total"], 0)

	// List songs filtered by fonograma_id
	wf := httptest.NewRecorder()
	reqf, _ := http.NewRequest("GET", "/admin/songs?fonograma_id=1", nil)
	reqf.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(wf, reqf)
	require.Equal(t, http.StatusOK, wf.Code)

	// Create a new song
	createBody := `{"fonograma_id":1,"title":"New Song","lyrics":"Test lyrics"}`
	wc := httptest.NewRecorder()
	reqc, _ := http.NewRequest("POST", "/admin/songs", bytes.NewBufferString(createBody))
	reqc.Header.Set("Content-Type", "application/json")
	reqc.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(wc, reqc)
	require.Equal(t, http.StatusCreated, wc.Code)

	var createResp map[string]interface{}
	require.NoError(t, json.Unmarshal(wc.Body.Bytes(), &createResp))
	newID := int(createResp["id"].(float64))

	// Update the created song
	updateBody := `{"title":"Updated Song","lyrics":"New lyrics"}`
	wu := httptest.NewRecorder()
	requ, _ := http.NewRequest("PUT", fmt.Sprintf("/admin/songs/%d", newID), bytes.NewBufferString(updateBody))
	requ.Header.Set("Content-Type", "application/json")
	requ.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(wu, requ)
	require.Equal(t, http.StatusOK, wu.Code)

	// Update non-existent → 404
	wu2 := httptest.NewRecorder()
	requ2, _ := http.NewRequest("PUT", "/admin/songs/9999", bytes.NewBufferString(updateBody))
	requ2.Header.Set("Content-Type", "application/json")
	requ2.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(wu2, requ2)
	assert.Equal(t, http.StatusNotFound, wu2.Code)

	// Delete the created song
	wd := httptest.NewRecorder()
	reqd, _ := http.NewRequest("DELETE", fmt.Sprintf("/admin/songs/%d", newID), nil)
	reqd.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(wd, reqd)
	require.Equal(t, http.StatusOK, wd.Code)

	// Delete non-existent → 404
	wd2 := httptest.NewRecorder()
	reqd2, _ := http.NewRequest("DELETE", fmt.Sprintf("/admin/songs/%d", newID), nil)
	reqd2.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(wd2, reqd2)
	assert.Equal(t, http.StatusNotFound, wd2.Code)
}

// ─── Users CRUD (admin only) ─────────────────────────────────────────────────

func TestAdminUsersCRUD(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAdminRouter()
	tok := adminTok(t)

	// List users (empty DB)
	wl := httptest.NewRecorder()
	reql, _ := http.NewRequest("GET", "/admin/users", nil)
	reql.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(wl, reql)
	require.Equal(t, http.StatusOK, wl.Code)

	// Create an editor user
	createBody := `{"username":"neweditor","email":"ed@test.com","password":"edpassword","role":"editor"}`
	wc := httptest.NewRecorder()
	reqc, _ := http.NewRequest("POST", "/admin/users", bytes.NewBufferString(createBody))
	reqc.Header.Set("Content-Type", "application/json")
	reqc.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(wc, reqc)
	require.Equal(t, http.StatusCreated, wc.Code)

	var createResp map[string]interface{}
	require.NoError(t, json.Unmarshal(wc.Body.Bytes(), &createResp))
	u := createResp["user"].(map[string]interface{})
	assert.Equal(t, "editor", u["role"])
	uid := int(u["id"].(float64))

	// Duplicate username → 409
	wdup := httptest.NewRecorder()
	reqdup, _ := http.NewRequest("POST", "/admin/users", bytes.NewBufferString(createBody))
	reqdup.Header.Set("Content-Type", "application/json")
	reqdup.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(wdup, reqdup)
	assert.Equal(t, http.StatusConflict, wdup.Code)

	// Update the created user's role
	updateBody := `{"role":"viewer"}`
	wu := httptest.NewRecorder()
	requ, _ := http.NewRequest("PUT", fmt.Sprintf("/admin/users/%d", uid), bytes.NewBufferString(updateBody))
	requ.Header.Set("Content-Type", "application/json")
	requ.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(wu, requ)
	assert.Equal(t, http.StatusOK, wu.Code)

	// Delete the created user
	wd := httptest.NewRecorder()
	reqd, _ := http.NewRequest("DELETE", fmt.Sprintf("/admin/users/%d", uid), nil)
	reqd.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(wd, reqd)
	require.Equal(t, http.StatusOK, wd.Code)

	// Delete non-existent → 404
	wd2 := httptest.NewRecorder()
	reqd2, _ := http.NewRequest("DELETE", fmt.Sprintf("/admin/users/%d", uid), nil)
	reqd2.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(wd2, reqd2)
	assert.Equal(t, http.StatusNotFound, wd2.Code)
}

func TestAdminDeleteLastAdmin(t *testing.T) {
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()
	r := setupAdminRouter()
	tok := adminTok(t)

	// Insert an admin user with id=1 so we can try to self-delete as last admin
	_, err := database.DB.Exec(
		`INSERT INTO users (id, username, email, password_hash, role) VALUES (1, 'admin', 'admin@test.com', 'x', 'admin')`,
	)
	require.NoError(t, err)

	wd := httptest.NewRecorder()
	reqd, _ := http.NewRequest("DELETE", "/admin/users/1", nil)
	reqd.Header.Set("Authorization", authHeader(tok))
	r.ServeHTTP(wd, reqd)
	assert.Equal(t, http.StatusBadRequest, wd.Code)
}
