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

// setupWordCloudDB seeds the minimal schema and one song per row used
// by the word-cloud regression tests.
func setupWordCloudDB(t *testing.T) {
	t.Helper()
	database.DB = nil
	db, err := sql.Open("sqlite", ":memory:")
	require.NoError(t, err)
	schema := `
	CREATE TABLE fonogramas (
		clave_fonograma INTEGER PRIMARY KEY,
		titulo TEXT NOT NULL,
		anio TEXT
	);
	CREATE TABLE songs (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		fonograma_id INTEGER,
		title TEXT NOT NULL,
		filename TEXT,
		lyrics TEXT,
		clasificacion TEXT,
		tema TEXT
	);
	`
	_, err = db.Exec(schema)
	require.NoError(t, err)
	_, err = db.Exec(`INSERT INTO fonogramas (clave_fonograma, titulo, anio) VALUES (1, 'Album Uno', '1968')`)
	require.NoError(t, err)
	database.DB = db
}

// TestGetWordCloudCaseFoldsMixedCase verifies that "Mamá" and "mamá"
// collapse under one bucket. Before fix the word cloud stored words
// verbatim, so "Mamá" and "mamá" appeared as separate chips.
func TestGetWordCloudCaseFoldsMixedCase(t *testing.T) {
	gin.SetMode(gin.TestMode)
	setupWordCloudDB(t)
	defer func() { _ = database.DB.Close() }()

	_, err := database.DB.Exec(`
		INSERT INTO songs (fonograma_id, title, lyrics, tema) VALUES
		(1, 'Mixed', 'Mamá canta Mamá duerme mamá baja y mamá sube', 'Amor')
	`)
	require.NoError(t, err)

	r := gin.New()
	r.GET("/word-cloud", GetWordCloud)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/word-cloud", nil)
	r.ServeHTTP(w, req)
	require.Equal(t, http.StatusOK, w.Code)

	var resp WordCloudResponse
	require.NoError(t, json.Unmarshal(w.Body.Bytes(), &resp))

	// "mamá" should appear exactly once (the four case variants +
	// one "Mamá" extra collapse into a single bucket). The response's
	// `Size` field is a normalised 10..100 percentage used by the
	// front for font sizing, so we cannot compare it against raw
	// counts. Instead we count how many entries with the lowercased
	// key "mamá" appear — should be exactly 1.
	count := 0
	for _, wf := range resp.Words {
		if wf.Text == "mamá" {
			count++
		}
		assert.NotEqual(t, "Mamá", wf.Text, "case variants should not appear in original form")
		assert.NotEqual(t, "Mama", wf.Text)
	}
	assert.Equal(t, 1, count, "all case variants of mamá must collapse into a single bucket")

	// And totalWords reflects raw counts: 5 of mamá + 1 each of
	// canta, duerme, baja, sube, y (y = stop, not in Words).
	assert.Equal(t, 8, resp.TotalWords,
		"totalWords counts raw tokens before stop-word exclusion")
}

// TestGetWordCloudDropsShortAndStopWords verifies that single-char
// tokens and the Spanish stop-word set never appear in the response.
func TestGetWordCloudDropsShortAndStopWords(t *testing.T) {
	gin.SetMode(gin.TestMode)
	setupWordCloudDB(t)
	defer func() { _ = database.DB.Close() }()

	// Several words plus short tokens and stop words; the surviving
	// token should be just the non-stop, multi-character one.
	_, err := database.DB.Exec(`
		INSERT INTO songs (fonograma_id, title, lyrics, tema) VALUES
		(1, 'Short', 'de la casa por el tejado bajo la luna llena', 'Amor')
	`)
	require.NoError(t, err)

	r := gin.New()
	r.GET("/word-cloud", GetWordCloud)

	w := httptest.NewRecorder()
	req, _ := http.NewRequest("GET", "/word-cloud", nil)
	r.ServeHTTP(w, req)
	require.Equal(t, http.StatusOK, w.Code)

	var resp WordCloudResponse
	require.NoError(t, json.Unmarshal(w.Body.Bytes(), &resp))

	// Lyrics: 'de la casa por el tejado bajo la luna llena'.
	// After filter:
	//   * de, la, el, por, bajo: Spanish stop words → dropped
	//     ('bajo' is on the stop-word list because the common
	//     Spanish word 'bajo' = 'low' carries no semantic weight;
	//     the boxer's 'golpe bajo' or a choreography note is
	//     filtered out of the word cloud intentionally.)
	//   * casa, tejado, luna, llena: 4-6 chars → KEPT
	for _, wf := range resp.Words {
		assert.GreaterOrEqual(t, len(wf.Text), 2,
			"every word must be at least 2 chars (got %q)", wf.Text)
		for _, stop := range []string{"de", "la", "el", "por", "bajo"} {
			assert.NotEqual(t, stop, wf.Text,
				"stop word %q must not appear (got %q)", stop, wf.Text)
		}
	}
	words := make(map[string]int)
	for _, wf := range resp.Words {
		words[wf.Text]++
	}
	for _, expected := range []string{"casa", "tejado", "luna", "llena"} {
		assert.Equal(t, 1, words[expected], "%q must appear once", expected)
	}
}
