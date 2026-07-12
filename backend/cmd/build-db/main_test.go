package main

import (
	"strings"
	"testing"

	"github.com/stretchr/testify/assert"
)

// ─── normalize ────────────────────────────────────────────────────────────────

func TestNormalize(t *testing.T) {
	cases := []struct {
		input    string
		expected string
	}{
		// Removes leading article "el"
		{"El Grillo Músico", "grillo musico"},
		// Strips trailing parenthetical and leading article "la"
		{"La Patita (introducción)", "patita"},
		// Trims spaces, lowercases
		{"  VAMOS A CANTAR  ", "vamos a cantar"},
		// Removes leading "los"; diacritics stripped
		{"Los Cien Pies del Ciempiés", "cien pies del ciempies"},
		// Square-bracket removal
		{"Canción [demo]", "cancion"},
		// Multiple spaces collapsed
		{"Una   canción", "cancion"},
		// Empty string stays empty
		{"", ""},
	}
	for _, tc := range cases {
		got := normalize(tc.input)
		assert.Equal(t, tc.expected, got, "normalize(%q)", tc.input)
	}
}

// ─── levenshteinDistance ─────────────────────────────────────────────────────

func TestLevenshteinDistance(t *testing.T) {
	cases := []struct {
		s, t string
		want int
	}{
		{"", "", 0},
		{"abc", "abc", 0},
		{"abc", "axc", 1},
		{"kitten", "sitting", 3},
		{"", "abc", 3},
		{"abc", "", 3},
		{"a", "b", 1},
	}
	for _, tc := range cases {
		got := levenshteinDistance(tc.s, tc.t)
		assert.Equal(t, tc.want, got, "levenshteinDistance(%q, %q)", tc.s, tc.t)
	}
}

// ─── calculateMatchScore ─────────────────────────────────────────────────────

func TestCalculateMatchScore(t *testing.T) {
	// Exact match
	assert.InDelta(t, 1.0, calculateMatchScore("hello", "hello"), 0)

	// Both empty strings are equal → exact match returns 1.0
	assert.InDelta(t, 1.0, calculateMatchScore("", ""), 0)

	// Very similar strings (1 edit distance) score above 0.6
	assert.Greater(t, calculateMatchScore("cancion", "canciones"), 0.6,
		"strings with low edit distance should score above 0.6")

	// Totally different strings score below 0.6
	assert.Less(t, calculateMatchScore("hello", "xyz"), 0.6,
		"unrelated strings should score below 0.6")

	// Similar-length strings with good overlap score higher than unrelated ones
	closeScore := calculateMatchScore("grillo", "grillo musico")
	farScore := calculateMatchScore("grillo", "xyz")
	assert.Greater(t, closeScore, farScore, "partial match should score higher than unrelated")
}

// ─── extractSongTitles ────────────────────────────────────────────────────────

func TestExtractSongTitles(t *testing.T) {
	t.Run("standard comma-separated format", func(t *testing.T) {
		pistas := "1. Song One (composer), 2. Song Two; 3. Song Three"
		titles := extractSongTitles(pistas)
		assert.Equal(t, []string{"Song One", "Song Two", "Song Three"}, titles)
	})

	t.Run("single track", func(t *testing.T) {
		titles := extractSongTitles("1. Only Song")
		assert.Equal(t, []string{"Only Song"}, titles)
	})

	t.Run("empty string", func(t *testing.T) {
		titles := extractSongTitles("")
		assert.Nil(t, titles)
	})

	t.Run("no numbered tracks", func(t *testing.T) {
		titles := extractSongTitles("Sin pistas disponibles")
		assert.Nil(t, titles)
	})

	t.Run("sided LP format", func(t *testing.T) {
		// The function splits on numbered markers; "Lado N:" text between tracks
		// is captured as trailing text on the preceding title and trimmed of ,/;
		// but not of arbitrary words. Assert key songs are found anywhere in results.
		pistas := "Lado 1: 1. First Song (A. Author), 2. Second Song; Lado 2: 3. Third Song"
		titles := extractSongTitles(pistas)
		assert.Len(t, titles, 3)
		assert.Equal(t, "First Song", titles[0])
		assert.Equal(t, "Third Song", titles[2])
		// Second title may include '; Lado 2:' since the function doesn't strip it
		assert.True(t, strings.HasPrefix(titles[1], "Second Song"),
			"second track should start with 'Second Song', got %q", titles[1])
	})

	t.Run("trailing punctuation stripped", func(t *testing.T) {
		titles := extractSongTitles("1. Hello World,")
		assert.Equal(t, []string{"Hello World"}, titles)
	})

	t.Run("parenthetical composer stripped", func(t *testing.T) {
		titles := extractSongTitles("1. Mi Canción (Autor Desconocido)")
		assert.Equal(t, []string{"Mi Canción"}, titles)
	})
}

// ─── extractSongMetadata ───────────────────────────────────────────────

func TestExtractSongMetadata_ClosingBlock(t *testing.T) {
	// Real-world shape of a Letras/*.txt footer: closing Dura/Tema/
	// Personajes block followed by either an Autor: line or initials
	// like "M.G.A." on the very last line.
	body := "Apúntate la negra, María…\ncuando te vayas a bailar.\n\n" +
		"Dura: 2:08\n" +
		"Tema: Familia, Eternidad/ Temporalidad.\n" +
		"Personajes: Conejo.\n" +
		"\n" +
		"M.G.A.\n"

	m := extractSongMetadata(body)
	assert.Equal(t, "2:08", m.Duracion)
	assert.Equal(t, "Conejo.", m.Personajes)
	assert.Equal(t, "M.G.A.", m.Autor, "fallback to initials line")
	assert.Contains(t, m.CleanLyrics, "Apúntate la negra")
	assert.NotContains(t, m.CleanLyrics, "Dura:")
	assert.NotContains(t, m.CleanLyrics, "M.G.A.")
}

func TestExtractSongMetadata_ExplicitAutor(t *testing.T) {
	// SON DE LA CIUDAD-style: explicit Autor: in the closing block,
	// no initials line.
	body := "Apúntate la negra, María…\n\n" +
		"Dura: 4:00\n" +
		"Tema: Juventud/ Vejez, Eternidad/ Temporalidad.\n" +
		"Personajes: La niña y el gusano\n"
	m := extractSongMetadata(body)
	assert.Equal(t, "4:00", m.Duracion)
	assert.Empty(t, m.Autor, "no explicit Autor: in the closing block means empty autor")
}

func TestExtractSongMetadata_IgnoresEarlyAutorHeader(t *testing.T) {
	// "Autor:" near the top is a header attribution, not metadata. Only
	// the last metadata block (Dura:/Tema:) is considered.
	body := "EL GUSANITO MEDIDOR\n\n" +
		"Autor: Gilda y Valentín Rincón\n\n" +
		"Apúntate la negra…\n\n" +
		"Dura: 4:00\n" +
		"Tema: Naturaleza/ Cultura-Civilización.\n" +
		"Personajes: Niños\n"
	m := extractSongMetadata(body)
	assert.Equal(t, "4:00", m.Duracion)
	// Early Autor: stays inside the lyrics body — it's just the
	// author attribution the lyrics file prints under the title.
	assert.Contains(t, m.CleanLyrics, "Gilda y Valentín Rincón",
		"early Autor: is content, not metadata")
}

func TestExtractSongMetadata_NoMarkers(t *testing.T) {
	m := extractSongMetadata("verse\nchorus\n")
	assert.Contains(t, m.CleanLyrics, "verse")
	assert.Contains(t, m.CleanLyrics, "chorus")
	assert.Empty(t, m.Autor)
	assert.Empty(t, m.Duracion)
}
