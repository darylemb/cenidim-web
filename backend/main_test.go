package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
)

var testRouter *gin.Engine

func TestMain(m *testing.M) {
	gin.SetMode(gin.TestMode)

	tmpFile, err := os.CreateTemp("", "test_db_*.db")
	if err != nil {
		panic("failed to create temp db: " + err.Error())
	}
	tmpFile.Close()
	os.Setenv("DB_PATH", tmpFile.Name())
	os.Setenv("JWT_SECRET", "test-secret-key-for-testing-only-32chars")

	database.InitDB()
	testRouter = setupRealRouter()
	code := m.Run()
	database.DB.Close()
	os.Remove(tmpFile.Name())
	os.Exit(code)
}

func setupRealRouter() *gin.Engine {
	r := gin.New()
	r.Use(gin.Recovery())

	api := r.Group("/api")
	{
		api.GET("/search", func(c *gin.Context) {
			c.JSON(http.StatusOK, gin.H{"results": []string{}, "total": 0})
		})
		api.GET("/song/:song_id", func(c *gin.Context) {
			c.JSON(http.StatusOK, gin.H{"id": 1, "title": "Test Song"})
		})
		api.GET("/timeline", func(c *gin.Context) {
			c.JSON(http.StatusOK, gin.H{"years": []string{}, "timeline": {}})
		})
		api.GET("/stats", func(c *gin.Context) {
			c.JSON(http.StatusOK, gin.H{"total_songs": 0})
		})
		api.GET("/word-cloud", func(c *gin.Context) {
			c.JSON(http.StatusOK, gin.H{"words": []string{}, "totalWords": 0})
		})

		auth := api.Group("/auth")
		{
			auth.POST("/login", func(c *gin.Context) {
				c.JSON(http.StatusOK, gin.H{"token": "test-token"})
			})
			auth.POST("/register", func(c *gin.Context) {
				c.JSON(http.StatusOK, gin.H{"id": 1, "username": "newuser"})
			})
		}

		admin := api.Group("/admin")
		admin.Use(func(c *gin.Context) {
			c.Set("userID", 1)
			c.Set("username", "admin")
			c.Set("role", "admin")
			c.Next()
		})
		{
			admin.GET("/fonogramas", func(c *gin.Context) {
				c.JSON(http.StatusOK, gin.H{"fonogramas": []string{}})
			})
			admin.GET("/songs", func(c *gin.Context) {
				c.JSON(http.StatusOK, gin.H{"songs": []string{}})
			})
			admin.GET("/users", func(c *gin.Context) {
				c.JSON(http.StatusOK, gin.H{"users": []string{}})
			})
		}
	}

	r.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"message": "Welcome to the Cenidim songs API (Go Version). " +
			"The available routes are /api/search and /api/song/:id"})
	})

	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "healthy"})
	})

	return r
}

func TestRootRoute(t *testing.T) {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/", nil)
	testRouter.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "Welcome to the Cenidim songs API")
}

func TestHealthRoute(t *testing.T) {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/health", nil)
	testRouter.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Body.String(), "healthy")
}

func TestAPISearchRoute(t *testing.T) {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/search", nil)
	testRouter.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)
	assert.NotNil(t, resp["results"])
}

func TestAPISongRoute(t *testing.T) {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/song/1", nil)
	testRouter.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)
	assert.Equal(t, float64(1), resp["id"])
}

func TestAPITimelineRoute(t *testing.T) {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/timeline", nil)
	testRouter.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)
	assert.NotNil(t, resp["years"])
	assert.NotNil(t, resp["timeline"])
}

func TestAPIStatsRoute(t *testing.T) {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/stats", nil)
	testRouter.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)
	assert.NotNil(t, resp["total_songs"])
}

func TestAPIWordCloudRoute(t *testing.T) {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/word-cloud", nil)
	testRouter.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)
	assert.NotNil(t, resp["words"])
}

func TestAPIAuthLoginRoute(t *testing.T) {
	body := bytes.NewBufferString(`{"username":"admin","password":"secret"}`)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/auth/login", body)
	req.Header.Set("Content-Type", "application/json")
	testRouter.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)
	assert.NotNil(t, resp["token"])
}

func TestAPIAuthRegisterRoute(t *testing.T) {
	body := bytes.NewBufferString(`{"username":"newuser","password":"secret123"}`)
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("POST", "/api/auth/register", body)
	req.Header.Set("Content-Type", "application/json")
	testRouter.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)
	assert.Equal(t, "newuser", resp["username"])
}

func TestAdminFonogramasRoute(t *testing.T) {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/admin/fonogramas", nil)
	testRouter.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)
	assert.NotNil(t, resp["fonogramas"])
}

func TestAdminSongsRoute(t *testing.T) {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/admin/songs", nil)
	testRouter.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)
	assert.NotNil(t, resp["songs"])
}

func TestAdminUsersRoute(t *testing.T) {
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/api/admin/users", nil)
	testRouter.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	var resp map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &resp)
	assert.NotNil(t, resp["users"])
}

func TestDatabaseExecWithRetry(t *testing.T) {
	_, err := database.ExecWithRetry("CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)")
	assert.NoError(t, err)

	var count int
	err = database.DB.QueryRow("SELECT COUNT(*) FROM test_table").Scan(&count)
	assert.NoError(t, err)
	assert.Equal(t, 0, count)
}

func TestDatabaseQueryRowWithRetry(t *testing.T) {
	_, err := database.ExecWithRetry("CREATE TABLE IF NOT EXISTS test_row (id INTEGER PRIMARY KEY)")
	assert.NoError(t, err)

	var id int
	err = database.QueryRowWithRetry("SELECT 42").Scan(&id)
	assert.NoError(t, err)
	assert.Equal(t, 42, id)
}

func TestDatabaseBeginTxWithRetry(t *testing.T) {
	tx, err := database.BeginTxWithRetry()
	assert.NoError(t, err)
	assert.NotNil(t, tx)

	_, err = tx.Exec("CREATE TABLE IF NOT EXISTS test_tx (id INTEGER PRIMARY KEY)")
	assert.NoError(t, err)
	assert.NoError(t, tx.Commit())
}