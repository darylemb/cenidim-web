package handlers

import (
	"database/sql"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/daryl/cenidim-go-api/models"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	_ "modernc.org/sqlite"
)

func setupTestDB(t *testing.T) {
	// Use an in-memory database for fast integration tests
	db, err := sql.Open("sqlite", ":memory:")
	if err != nil {
		t.Fatalf("Failed to open test db: %v", err)
	}

	// Setup Schema
	schema := `
	CREATE TABLE albums (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		name TEXT NOT NULL
	);
	CREATE TABLE songs (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		title TEXT NOT NULL,
		album_id INTEGER,
		filename TEXT,
		lyrics TEXT,
		FOREIGN KEY (album_id) REFERENCES albums (id)
	);`
	if _, err = db.Exec(schema); err != nil {
		t.Fatalf("Failed to create schema: %v", err)
	}

	// Seed Data
	_, err = db.Exec(`INSERT INTO albums (id, name) VALUES (1, 'Test Album')`)
	require.NoError(t, err)
	_, err = db.Exec(`INSERT INTO songs (id, title, album_id, filename, lyrics) VALUES (1, 'Test Song', 1, 'test.txt', 'This is a test lyric about love')`)
	require.NoError(t, err)

	database.DB = db
}

func TestSearchSongsIntegration(t *testing.T) {
	gin.SetMode(gin.TestMode)
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()

	r := gin.New()
	r.GET("/search", SearchSongs)

	// Test Case 1: Search by title
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/search?query=test&field=title", nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var results []models.Song
	err := json.Unmarshal(w.Body.Bytes(), &results)
	require.NoError(t, err)
	assert.Len(t, results, 1)
	assert.Equal(t, "Test Song", results[0].Title)

	// Test Case 2: No results
	w2 := httptest.NewRecorder()
	req2, _ := http.NewRequest("GET", "/search?query=nonexistent", nil)
	r.ServeHTTP(w2, req2)

	var emptyResults []models.Song
	err = json.Unmarshal(w2.Body.Bytes(), &emptyResults)
	require.NoError(t, err)
	assert.Empty(t, emptyResults)
}

func TestGetSongIntegration(t *testing.T) {
	gin.SetMode(gin.TestMode)
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()

	r := gin.New()
	r.GET("/song/:song_id", GetSong)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/song/1", nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var s models.SongDetail
	err := json.Unmarshal(w.Body.Bytes(), &s)
	require.NoError(t, err)
	assert.Equal(t, "Test Song", s.Title)
	assert.Contains(t, s.Lyrics, "test lyric")
}
