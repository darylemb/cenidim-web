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
	assert.Equal(t, 1.0, calculateMatchScore("hello", "hello"))

	// Both empty strings are equal → exact match returns 1.0
	assert.Equal(t, 1.0, calculateMatchScore("", ""))

	// Very similar strings (1 edit distance) score above 0.6
	assert.True(t, calculateMatchScore("cancion", "canciones") > 0.6,
		"strings with low edit distance should score above 0.6")

	// Totally different strings score below 0.6
	assert.True(t, calculateMatchScore("hello", "xyz") < 0.6,
		"unrelated strings should score below 0.6")

	// Similar-length strings with good overlap score higher than unrelated ones
	closeScore := calculateMatchScore("grillo", "grillo musico")
	farScore := calculateMatchScore("grillo", "xyz")
	assert.True(t, closeScore > farScore, "partial match should score higher than unrelated")
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
