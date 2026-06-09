package handlers

import (
	"database/sql"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	_ "modernc.org/sqlite"
)

func setupTestDBForStats(t *testing.T) {
	t.Helper()
	database.DB = nil

	db, err := sql.Open("sqlite", ":memory:")
	if err != nil {
		t.Fatalf("Failed to open test db: %v", err)
	}

	schema := `
	CREATE TABLE fonogramas (
		clave_fonograma         INTEGER PRIMARY KEY,
		titulo                  TEXT NOT NULL,
		subtitulo               TEXT,
		interprete_principal    TEXT,
		interpretes_invitados   TEXT,
		interprete_participante TEXT,
		soporte_fisico          TEXT,
		editora                 TEXT,
		numero_catalogo         TEXT,
		ciudad_edicion          TEXT,
		pais_edicion            TEXT,
		anio                    TEXT,
		pistas                  TEXT,
		observaciones           TEXT
	);
	CREATE TABLE songs (
		id           INTEGER PRIMARY KEY AUTOINCREMENT,
		fonograma_id INTEGER,
		title        TEXT NOT NULL,
		filename     TEXT,
		lyrics       TEXT,
		clasificacion TEXT,
		tema         TEXT,
		created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (fonograma_id) REFERENCES fonogramas(clave_fonograma)
	);
	CREATE TABLE users (
		id            INTEGER PRIMARY KEY AUTOINCREMENT,
		username      TEXT UNIQUE NOT NULL,
		email         TEXT UNIQUE NOT NULL,
		password_hash TEXT NOT NULL,
		role          TEXT NOT NULL DEFAULT 'viewer',
		created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
	);`
	if _, err = db.Exec(schema); err != nil {
		t.Fatalf("Failed to create schema: %v", err)
	}

	// Seed fonogramas
	_, err = db.Exec(`INSERT INTO fonogramas (clave_fonograma, titulo, anio) VALUES 
		(1, 'Album Uno', '1968'),
		(2, 'Album Dos', '1970'),
		(3, 'Album Tres', '1972')`)
	require.NoError(t, err)

	// Seed songs with different years, clasificaciones, and themes
	_, err = db.Exec(`INSERT INTO songs (fonograma_id, title, filename, lyrics, clasificacion, tema) VALUES
		(1, 'Song One', 'song1.txt', 'Lyrics one', 'ESPAÑOL_ESTANDAR', 'AMOR'),
		(1, 'Song Two', 'song2.txt', 'Lyrics two', 'ESPAÑOL_REGIONAL', 'AMOR'),
		(2, 'Song Three', 'song3.txt', 'Lyrics three', 'LENGUA_INDIGENA', 'NAVIDAD'),
		(2, 'Song Four', 'song4.txt', 'Lyrics four', 'ESPAÑOL_ESTANDAR', 'FIESTA'),
		(3, 'Song Five', 'song5.txt', 'Lyrics five', 'ESPAÑOL_ESTANDAR', NULL)`)
	require.NoError(t, err)

	database.DB = db
}

func TestGetStatsIntegration(t *testing.T) {
	gin.SetMode(gin.TestMode)
	setupTestDBForStats(t)
	defer func() { _ = database.DB.Close() }()

	r := gin.New()
	r.GET("/stats", GetStats)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/stats", nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var stats StatsResponse
	err := json.Unmarshal(w.Body.Bytes(), &stats)
	require.NoError(t, err)

	assert.Equal(t, 5, stats.TotalSongs)
	assert.Equal(t, 3, stats.TotalAlbums)

	// Check songs by year
	assert.Equal(t, 2, stats.SongsByYear["1968"])
	assert.Equal(t, 2, stats.SongsByYear["1970"])
	assert.Equal(t, 1, stats.SongsByYear["1972"])

	// Check songs by clasificacion
	assert.Equal(t, 3, stats.SongsByClasificacion["ESPAÑOL_ESTANDAR"])
	assert.Equal(t, 1, stats.SongsByClasificacion["ESPAÑOL_REGIONAL"])
	assert.Equal(t, 1, stats.SongsByClasificacion["LENGUA_INDIGENA"])

	// Check top albums - sorted by song count desc
	assert.Len(t, stats.TopAlbums, 3)
	// Album Uno and Album Dos both have 2 songs, order between them may vary
	assert.Equal(t, 2, stats.TopAlbums[0].Count)
	assert.Equal(t, 2, stats.TopAlbums[1].Count)
	assert.Equal(t, 1, stats.TopAlbums[2].Count)
}

func TestGetStatsEmptyDatabase(t *testing.T) {
	gin.SetMode(gin.TestMode)

	db, err := sql.Open("sqlite", ":memory:")
	if err != nil {
		t.Fatalf("Failed to open test db: %v", err)
	}

	schema := `
	CREATE TABLE fonogramas (
		clave_fonograma INTEGER PRIMARY KEY,
		titulo TEXT NOT NULL,
		anio TEXT
	);
	CREATE TABLE songs (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		fonograma_id INTEGER,
		clasificacion TEXT,
		tema TEXT,
		created_at DATETIME DEFAULT CURRENT_TIMESTAMP
	);`
	if _, err = db.Exec(schema); err != nil {
		t.Fatalf("Failed to create schema: %v", err)
	}

	database.DB = db
	defer func() { _ = database.DB.Close() }()

	r := gin.New()
	r.GET("/stats", GetStats)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/stats", nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var stats StatsResponse
	err = json.Unmarshal(w.Body.Bytes(), &stats)
	require.NoError(t, err)

	assert.Equal(t, 0, stats.TotalSongs)
	assert.Equal(t, 0, stats.TotalAlbums)
	assert.Empty(t, stats.TopAlbums)
}

func TestGetStatsIncludesThemeAggregation(t *testing.T) {
	gin.SetMode(gin.TestMode)
	setupTestDBForStats(t)
	defer func() { _ = database.DB.Close() }()

	r := gin.New()
	r.GET("/stats", GetStats)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/stats", nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var stats StatsResponse
	err := json.Unmarshal(w.Body.Bytes(), &stats)
	require.NoError(t, err)

	// Themes seeded: AMOR x2, NAVIDAD x1, FIESTA x1, NULL x1.
	// The "Sin tema" / empty bucket is intentionally EXCLUDED from the
	// response — the thematic-categories dashboard does not show it.
	assert.Equal(t, 2, stats.SongsByTheme["AMOR"])
	assert.Equal(t, 1, stats.SongsByTheme["NAVIDAD"])
	assert.Equal(t, 1, stats.SongsByTheme["FIESTA"])
	_, hasEmpty := stats.SongsByTheme[""]
	assert.False(t, hasEmpty, "unclassified songs must NOT appear in any bucket")
	assert.Equal(t, 3, stats.DistinctThemes, "3 distinct buckets (AMOR, NAVIDAD, FIESTA) — empty excluded")
}

func TestGetStatsWithThemeFilter(t *testing.T) {
	gin.SetMode(gin.TestMode)
	setupTestDBForStats(t)
	defer func() { _ = database.DB.Close() }()

	r := gin.New()
	r.GET("/stats", GetStats)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/stats?theme=AMOR", nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var stats StatsResponse
	err := json.Unmarshal(w.Body.Bytes(), &stats)
	require.NoError(t, err)

	assert.Equal(t, 2, stats.SongsByTheme["AMOR"])
	assert.Equal(t, 1, stats.DistinctThemes)
	_, hasNavidad := stats.SongsByTheme["NAVIDAD"]
	assert.False(t, hasNavidad, "NAVIDAD should be filtered out")
}

func TestGetStatsWithUnclassifiedThemeFilter(t *testing.T) {
	gin.SetMode(gin.TestMode)
	setupTestDBForStats(t)
	defer func() { _ = database.DB.Close() }()

	r := gin.New()
	r.GET("/stats", GetStats)

	w := httptest.NewRecorder()
	// __none__ matches the unclassified song (the seed has one song
	// with tema = NULL). The filter still counts that song in the
	// overall totals, but the songs_by_theme map no longer includes
	// an empty bucket — the dashboard's thematic-categories chart
	// does not surface "Sin tema".
	req, _ := http.NewRequest("GET", "/stats?theme=__none__", nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var stats StatsResponse
	err := json.Unmarshal(w.Body.Bytes(), &stats)
	require.NoError(t, err)

	_, hasEmpty := stats.SongsByTheme[""]
	assert.False(t, hasEmpty, "unclassified songs are not part of songs_by_theme")
	assert.Equal(t, 0, stats.DistinctThemes, "empty bucket is excluded from distinct count")
	// The unclassified song is still counted in TotalSongs — the
	// filter narrows to that 1 song, just not into a theme bucket.
	assert.Equal(t, 1, stats.TotalSongs, "filtering on __none__ still counts the 1 unclassified song")
}

func TestGetStatsRejectsInvalidYearRange(t *testing.T) {
	gin.SetMode(gin.TestMode)
	setupTestDBForStats(t)
	defer func() { _ = database.DB.Close() }()

	r := gin.New()
	r.GET("/stats", GetStats)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/stats?year_from=2020&year_to=1990", nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusBadRequest, w.Code)
}

func TestGetStatsWithYearRange(t *testing.T) {
	gin.SetMode(gin.TestMode)
	setupTestDBForStats(t)
	defer func() { _ = database.DB.Close() }()

	r := gin.New()
	r.GET("/stats", GetStats)

	w := httptest.NewRecorder()
	// Seed has 1968 (2 songs) and 1970 (2 songs) and 1972 (1 song).
	req, _ := http.NewRequest("GET", "/stats?year_from=1970&year_to=1970", nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var stats StatsResponse
	err := json.Unmarshal(w.Body.Bytes(), &stats)
	require.NoError(t, err)

	// Only songs from 1970 should be counted.
	assert.Equal(t, 2, stats.SongsByYear["1970"])
	assert.Equal(t, 2, stats.TotalSongs, "filtered TotalSongs respects year range")
}

func TestGetStatsWithFreeTextQuery(t *testing.T) {
	gin.SetMode(gin.TestMode)
	setupTestDBForStats(t)
	defer func() { _ = database.DB.Close() }()

	r := gin.New()
	r.GET("/stats", GetStats)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/stats?q=Song+One", nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var stats StatsResponse
	err := json.Unmarshal(w.Body.Bytes(), &stats)
	require.NoError(t, err)

	assert.Equal(t, 1, stats.TotalSongs, "q filter narrows dataset to one match")
}

func TestGetStatsRejectsLongQuery(t *testing.T) {
	gin.SetMode(gin.TestMode)
	setupTestDBForStats(t)
	defer func() { _ = database.DB.Close() }()

	r := gin.New()
	r.GET("/stats", GetStats)

	w := httptest.NewRecorder()
	long := ""
	for i := 0; i < 300; i++ {
		long += "x"
	}
	req, _ := http.NewRequest("GET", "/stats?q="+long, nil)
	r.ServeHTTP(w, req)

	assert.Equal(t, http.StatusBadRequest, w.Code)
}
