package handlers

import (
	"database/sql"
	"encoding/json"
	"fmt"
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
	t.Helper()
	// Use an in-memory database for fast integration tests
	db, err := sql.Open("sqlite", ":memory:")
	if err != nil {
		t.Fatalf("Failed to open test db: %v", err)
	}

	// Setup Schema (matches production schema)
	schema := `
	CREATE TABLE fonogramas (
		clave_fonograma         INTEGER PRIMARY KEY,
		titulo                  TEXT NOT NULL,
		subtitulo               TEXT,
		interprete_principal    TEXT,
		interpretes_invitados   TEXT,
		interprete_participante TEXT,
		soporte_fisico          TEXT,
		editora                TEXT,
		numero_catalogo         TEXT,
		ciudad_edicion          TEXT,
		pais_edicion            TEXT,
		anio                    TEXT,
		pistas                  TEXT,
		observaciones           TEXT,
		version                 INTEGER DEFAULT 0
	);
	CREATE TABLE songs (
		id           INTEGER PRIMARY KEY AUTOINCREMENT,
		fonograma_id INTEGER,
		title        TEXT NOT NULL,
		filename     TEXT,
		lyrics       TEXT,
		version      INTEGER DEFAULT 0,
		clasificacion TEXT,
		tema         TEXT,
		FOREIGN KEY (fonograma_id) REFERENCES fonogramas(clave_fonograma)
	);
	CREATE TABLE users (
		id            INTEGER PRIMARY KEY AUTOINCREMENT,
		username      TEXT UNIQUE NOT NULL,
		email         TEXT UNIQUE NOT NULL,
		password_hash TEXT NOT NULL,
		role          TEXT NOT NULL DEFAULT 'viewer',
		created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
		version       INTEGER DEFAULT 0
	);`
	if _, err = db.Exec(schema); err != nil {
		t.Fatalf("Failed to create schema: %v", err)
	}

	// Seed Data — use empty strings for nullable columns to avoid NULL scan issues
	_, err = db.Exec(`INSERT INTO fonogramas
		(clave_fonograma, titulo, subtitulo, interprete_principal, interpretes_invitados,
		 interprete_participante, soporte_fisico, editora, numero_catalogo, ciudad_edicion,
		 pais_edicion, anio, pistas, observaciones)
		VALUES (1, 'Test Album', '', '', '', '', '', '', '', '', '', '1968', '', '')`)
	require.NoError(t, err)
	_, err = db.Exec(`INSERT INTO songs (id, title, fonograma_id, filename, lyrics) VALUES (1, 'Test Song', 1, 'test.txt', 'This is a test lyric about love')`)
	require.NoError(t, err)
	// Additional songs for pagination tests. Titles avoid the word "test" so existing
	// title-based search assertions remain valid.
	_, err = db.Exec(`INSERT INTO songs (id, title, fonograma_id, filename, lyrics) VALUES (2, 'Another Song', 1, 'another.txt', 'Another lyric about joy')`)
	require.NoError(t, err)
	_, err = db.Exec(`INSERT INTO songs (id, title, fonograma_id, filename, lyrics) VALUES (3, 'Final Song', 1, 'final.txt', 'Final lyric about closure')`)
	require.NoError(t, err)

	database.DB = db
}

func TestSearchSongsIntegration(t *testing.T) {
	gin.SetMode(gin.TestMode)
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()

	r := gin.New()
	r.GET("/search", SearchSongs)

	type searchResponse struct {
		Results []models.Song `json:"results"`
		Total   int           `json:"total"`
	}

	// Test Case 1: Search by title
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/search?query=test&field=title", nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var resp searchResponse
	err := json.Unmarshal(w.Body.Bytes(), &resp)
	require.NoError(t, err)
	assert.Equal(t, 1, resp.Total)
	assert.Len(t, resp.Results, 1)
	assert.Equal(t, "Test Song", resp.Results[0].Title)

	// Test Case 2: No results
	w2 := httptest.NewRecorder()
	req2, _ := http.NewRequest("GET", "/search?query=nonexistent", nil)
	r.ServeHTTP(w2, req2)

	var emptyResp searchResponse
	err = json.Unmarshal(w2.Body.Bytes(), &emptyResp)
	require.NoError(t, err)
	assert.Equal(t, 0, emptyResp.Total)
	assert.Empty(t, emptyResp.Results)
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

func TestSearchSongsPagination(t *testing.T) {
	gin.SetMode(gin.TestMode)
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()

	r := gin.New()
	r.GET("/search", SearchSongs)

	type searchResponse struct {
		Results []models.Song `json:"results"`
		Total   int           `json:"total"`
	}

	// With three songs whose titles contain "Song", verify that limit/page slice correctly.
	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/search?query=Song&field=title&limit=1&page=2", nil)
	r.ServeHTTP(w, req)

	require.Equal(t, http.StatusOK, w.Code)

	var page2Resp searchResponse
	err := json.Unmarshal(w.Body.Bytes(), &page2Resp)
	require.NoError(t, err)
	assert.Equal(t, 3, page2Resp.Total)
	assert.Len(t, page2Resp.Results, 1)
	// Assuming deterministic ordering by ID or insertion, the second page should
	// return the song with ID 2 ("Another Song").
	assert.Equal(t, "Another Song", page2Resp.Results[0].Title)

	// Verify that invalid page values are clamped (e.g., page=0 behaves like page=1).
	wPage1 := httptest.NewRecorder()
	reqPage1, _ := http.NewRequest("GET", "/search?query=Song&field=title&limit=1&page=1", nil)
	r.ServeHTTP(wPage1, reqPage1)

	wPage0 := httptest.NewRecorder()
	reqPage0, _ := http.NewRequest("GET", "/search?query=Song&field=title&limit=1&page=0", nil)
	r.ServeHTTP(wPage0, reqPage0)

	require.Equal(t, http.StatusOK, wPage1.Code)
	require.Equal(t, http.StatusOK, wPage0.Code)
	assert.Equal(t, wPage1.Body.Bytes(), wPage0.Body.Bytes())

	// Verify that invalid limit values (e.g., limit=0) are handled as intended by
	// comparing with the default behavior when limit is omitted.
	wDefaultLimit := httptest.NewRecorder()
	reqDefaultLimit, _ := http.NewRequest("GET", "/search?query=Song&field=title", nil)
	r.ServeHTTP(wDefaultLimit, reqDefaultLimit)

	wLimitZero := httptest.NewRecorder()
	reqLimitZero, _ := http.NewRequest("GET", "/search?query=Song&field=title&limit=0", nil)
	r.ServeHTTP(wLimitZero, reqLimitZero)

	require.Equal(t, http.StatusOK, wDefaultLimit.Code)
	require.Equal(t, http.StatusOK, wLimitZero.Code)
	assert.Equal(t, wDefaultLimit.Body.Bytes(), wLimitZero.Body.Bytes())
}

// TestGetTimelineCoversAllYears is a regression test for the
// "LIMIT 1000 hides most years" bug. The seed only has 3 songs in one
// year, so we add a few more years and confirm the response still lists
// every year (and per-year cap is respected).
func TestGetTimelineCoversAllYears(t *testing.T) {
	gin.SetMode(gin.TestMode)
	setupTestDB(t)
	defer func() { _ = database.DB.Close() }()

	// Add a second fonograma/year and three more songs so the catalog
	// spans two distinct years and the per-year cap kicks in for the
	// second year when we set a tight limit.
	_, err := database.DB.Exec(
		`INSERT INTO fonogramas (clave_fonograma, titulo, anio) VALUES (2, 'Album Dos', '1970')`,
	)
	require.NoError(t, err)
	for i, title := range []string{"A", "B", "C", "D", "E"} {
		_, err = database.DB.Exec(
			`INSERT INTO songs (title, fonograma_id) VALUES (?, 2)`,
			fmt.Sprintf("Song %s", title),
		)
		require.NoError(t, err, "seed song %d", i)
	}

	r := gin.New()
	r.GET("/timeline", GetTimeline)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/timeline?limit=2", nil)
	r.ServeHTTP(w, req)
	require.Equal(t, http.StatusOK, w.Code)

	var resp struct {
		Years     []string         `json:"years"`
		Timeline  map[string][]any `json:"timeline"`
		Total     int              `json:"total"`
		Truncated bool             `json:"truncated"`
	}
	require.NoError(t, json.Unmarshal(w.Body.Bytes(), &resp))

	// Both years must be present, even though 1970 alone has 5 songs and
	// the per-year cap is 2.
	assert.ElementsMatch(t, []string{"1968", "1970"}, resp.Years)
	assert.LessOrEqual(t, len(resp.Timeline["1968"]), 2, "1968 respects the per-year cap")
	assert.Len(t, resp.Timeline["1970"], 2, "1970 is capped at the per-year limit")
	assert.Equal(t, 8, resp.Total)
	assert.True(t, resp.Truncated, "truncated must be true when a year is capped")
}
