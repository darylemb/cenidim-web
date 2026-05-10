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

	// Seed songs with different years and clasificaciones
	_, err = db.Exec(`INSERT INTO songs (fonograma_id, title, filename, lyrics, clasificacion) VALUES 
		(1, 'Song One', 'song1.txt', 'Lyrics one', 'ESPAÑOL_ESTANDAR'),
		(1, 'Song Two', 'song2.txt', 'Lyrics two', 'ESPAÑOL_REGIONAL'),
		(2, 'Song Three', 'song3.txt', 'Lyrics three', 'LENGUA_INDIGENA'),
		(2, 'Song Four', 'song4.txt', 'Lyrics four', 'ESPAÑOL_ESTANDAR'),
		(3, 'Song Five', 'song5.txt', 'Lyrics five', 'ESPAÑOL_ESTANDAR')`)
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
		titulo TEXT NOT NULL
	);
	CREATE TABLE songs (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		fonograma_id INTEGER
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
