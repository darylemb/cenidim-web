package handlers

import (
	"net/http"
	"regexp"
	"strings"
	"time"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/gin-gonic/gin"
)

// StatsResponse holds aggregate metrics for the dashboard
type StatsResponse struct {
	TotalSongs           int            `json:"total_songs"`
	TotalAlbums          int            `json:"total_albums"`
	SongsByYear          map[string]int `json:"songs_by_year"`
	SongsByClasificacion map[string]int `json:"songs_by_clasificacion"`
	SongsByTheme         map[string]int `json:"songs_by_theme"`
	DistinctThemes       int            `json:"distinct_themes"`
	RecentlyAdded        int            `json:"recently_added"`
	TopAlbums            []AlbumCount   `json:"top_albums"`
	AvgLyricsLength     float64        `json:"avg_lyrics_length"`
	SongsWithLyrics      int            `json:"songs_with_lyrics"`
	SongsByOovLevel      map[string]int `json:"songs_by_oov_level"`
	SongsByIndigena      map[string]int `json:"songs_by_indigena"`
	SongsWithoutYear     int            `json:"songs_without_year"`
}

// AlbumCount represents the number of songs per album
type AlbumCount struct {
	Album string `json:"album"`
	Year  string `json:"year"`
	Count int    `json:"count"`
}

// GetStats godoc
// @Summary Get database statistics
// @Description Returns aggregate metrics for the dashboard. Honors the
// @Description shared filter query parameters: theme, year_from, year_to,
// @Description clasificacion, album, q.
// @Tags stats
// @Accept json
// @Produce json
// @Param theme         query string false "Comma-separated theme list; use __none__ for unclassified"
// @Param year_from     query int    false "Inclusive lower bound on year"
// @Param year_to       query int    false "Inclusive upper bound on year"
// @Param clasificacion query string false "Comma-separated classification list"
// @Param album         query string false "Exact album match"
// @Param q             query string false "Free-text search across title, lyrics, and album"
// @Success 200 {object} StatsResponse
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /stats [get]
func GetStats(c *gin.Context) {
	fp := ParseFilterParams(c)
	if msg := fp.ValidateYearRange(); msg != "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": msg})
		return
	}
	if msg := fp.ValidateQueryLength(256); msg != "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": msg})
		return
	}

	stats := StatsResponse{
		SongsByYear:          make(map[string]int),
		SongsByClasificacion: make(map[string]int),
		SongsByTheme:         make(map[string]int),
		TopAlbums:            []AlbumCount{},
		SongsByOovLevel:      make(map[string]int),
		SongsByIndigena:      make(map[string]int),
	}

	songFrom := "FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma"
	filterWhere, filterArgs := fp.ApplySongFilters("")

	countSongs := "SELECT COUNT(*) " + songFrom + whereWrap(filterWhere)
	if err := database.DB.QueryRow(countSongs, filterArgs...).Scan(&stats.TotalSongs); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error fetching total songs"})
		return
	}

	// Total albums in the filtered set.
	countAlbums := `
		SELECT COUNT(DISTINCT f.clave_fonograma) ` + songFrom + whereWrap(filterWhere)
	if err := database.DB.QueryRow(countAlbums, filterArgs...).Scan(&stats.TotalAlbums); err != nil {
		stats.TotalAlbums = 0
	}

	// Songs by year (excluding "s/d" and empty years, applying the shared filter)
	yearRows, yearErr := database.DB.Query(`
		SELECT COALESCE(f.anio, 'Unknown'), COUNT(*)
		`+songFrom+whereWrap(whereAnd(filterWhere, "f.anio IS NOT NULL AND f.anio != '' AND f.anio != 's/d'"))+`
		GROUP BY f.anio
		ORDER BY f.anio`, filterArgs...)
	if yearErr != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error fetching songs by year"})
		return
	}
	defer func() { _ = yearRows.Close() }()

	for yearRows.Next() {
		var year string
		var count int
		if err := yearRows.Scan(&year, &count); err == nil {
			if year == "" {
				year = "Unknown"
			}
			stats.SongsByYear[year] = count
		}
	}

	// Songs by clasificacion (filtered)
	clasRows, clasErr := database.DB.Query(`
		SELECT COALESCE(s.clasificacion, 'ESPAÑOL_ESTANDAR'), COUNT(*)
		`+songFrom+whereWrap(filterWhere)+`
		GROUP BY s.clasificacion`, filterArgs...)
	if clasErr != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error fetching songs by clasificacion"})
		return
	}
	defer func() { _ = clasRows.Close() }()

	for clasRows.Next() {
		var class string
		var count int
		if err := clasRows.Scan(&class, &count); err == nil {
			stats.SongsByClasificacion[class] = count
		}
	}

	// Recently added (last 30 days) — global, not filter-aware by design.
	thirtyDaysAgo := time.Now().AddDate(0, 0, -30).Format("2006-01-02")
	if err := database.DB.QueryRow(
		"SELECT COUNT(*) FROM songs WHERE created_at > ?", thirtyDaysAgo,
	).Scan(&stats.RecentlyAdded); err != nil {
		stats.RecentlyAdded = 0
	}

	// Top albums by song count (filtered)
	topRows, topErr := database.DB.Query(`
		SELECT f.titulo, f.anio, COUNT(*) as song_count
		`+songFrom+whereWrap(filterWhere)+`
		GROUP BY f.clave_fonograma
		ORDER BY song_count DESC
		LIMIT 10`, filterArgs...)
	if topErr != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error fetching top albums"})
		return
	}
	defer func() { _ = topRows.Close() }()

	for topRows.Next() {
		var ac AlbumCount
		if err := topRows.Scan(&ac.Album, &ac.Year, &ac.Count); err == nil {
			stats.TopAlbums = append(stats.TopAlbums, ac)
		}
	}

	// Songs with lyrics count (filtered)
	if err := database.DB.QueryRow(
		"SELECT COUNT(*) "+songFrom+whereWrap(whereAnd(filterWhere, "s.lyrics IS NOT NULL AND s.lyrics != ''")),
		filterArgs...,
	).Scan(&stats.SongsWithLyrics); err != nil {
		stats.SongsWithLyrics = 0
	}

	// Average lyrics length (filtered)
	_ = database.DB.QueryRow(
		"SELECT AVG(LENGTH(s.lyrics)) "+songFrom+whereWrap(whereAnd(filterWhere, "s.lyrics IS NOT NULL AND s.lyrics != ''")),
		filterArgs...,
	).Scan(&stats.AvgLyricsLength)

	// Songs by OOV level (filtered). song_stats has no fonograma join, so we
	// sub-select distinct song_ids matching the filter.
	oovRows, oovErr := database.DB.Query(`
		SELECT
			CASE
				WHEN pct_oov < 5 THEN 'BAJA'
				WHEN pct_oov >= 5 AND pct_oov < 18 THEN 'MEDIA'
				ELSE 'ALTA'
			END as oov_level,
			COUNT(*) as count
		FROM song_stats
		WHERE song_id IN (SELECT s.id `+songFrom+whereWrap(filterWhere)+`)
		GROUP BY oov_level`, filterArgs...)
	if oovErr == nil {
		defer func() { _ = oovRows.Close() }()
		for oovRows.Next() {
			var level string
			var cnt int
			if err := oovRows.Scan(&level, &cnt); err == nil {
				stats.SongsByOovLevel[level] = cnt
			}
		}
	}

	// Songs by indigena presence (filtered)
	indRows, indErr := database.DB.Query(`
		SELECT
			CASE WHEN contiene_indigena = 1 THEN 'CON_INDIGENA' ELSE 'SIN_INDIGENA' END,
			COUNT(*) as count
		FROM song_stats
		WHERE song_id IN (SELECT s.id `+songFrom+whereWrap(filterWhere)+`)
		GROUP BY contiene_indigena`, filterArgs...)
	if indErr == nil {
		defer func() { _ = indRows.Close() }()
		for indRows.Next() {
			var label string
			var cnt int
			if err := indRows.Scan(&label, &cnt); err == nil {
				stats.SongsByIndigena[label] = cnt
			}
		}
	}

	// Songs without year (s/d or empty/null) — filter-aware.
	if err := database.DB.QueryRow(
		"SELECT COUNT(*) "+songFrom+whereWrap(whereAnd(filterWhere, "(f.anio IS NULL OR f.anio = '' OR f.anio = 's/d')")),
		filterArgs...,
	).Scan(&stats.SongsWithoutYear); err != nil {
		stats.SongsWithoutYear = 0
	}

	// Songs by theme (counts). We deliberately skip the empty string
	// bucket — "Sin tema" / unclassified songs are not part of the
	// thematic category dashboard. The dashboard filter chip list is
	// derived from this same aggregate.
	themeQuery := `
		SELECT s.tema, COUNT(*)
		` + songFrom + whereWrap(whereAnd(filterWhere, "s.tema IS NOT NULL AND s.tema != ''")) + `
		GROUP BY s.tema
		ORDER BY COUNT(*) DESC
	`
	themeRows, themeErr := database.DB.Query(themeQuery, filterArgs...)
	if themeErr == nil {
		defer func() { _ = themeRows.Close() }()
		for themeRows.Next() {
			var t string
			var cnt int
			if err := themeRows.Scan(&t, &cnt); err == nil {
				if t != "" {
					stats.SongsByTheme[t] = cnt
				}
			}
		}
		stats.DistinctThemes = len(stats.SongsByTheme)
	}

	c.JSON(http.StatusOK, stats)
}

// whereWrap joins a non-empty filter expression into a WHERE clause. Returns
// the empty string when no filter is active so the query remains a bare FROM.
func whereWrap(cond string) string {
	if cond == "" {
		return ""
	}
	return " WHERE " + cond
}

// whereAnd concatenates a prior filter condition and a free-form predicate
// with an AND. Empty inputs are skipped so a one-sided condition does not
// produce " AND foo" (a syntax error).
func whereAnd(prior, extra string) string {
	switch {
	case prior == "" && extra == "":
		return ""
	case prior == "":
		return extra
	case extra == "":
		return prior
	default:
		return prior + " AND " + extra
	}
}

// WordCloudResponse holds word frequency data for the word cloud visualization
type WordCloudResponse struct {
	Words              []WordFreq `json:"words"`
	TotalWords        int         `json:"totalWords"`
	ExcludedStopWords  int         `json:"excludedStopWords"`
}

// WordFreq represents a word and its frequency
type WordFreq struct {
	Text string `json:"text"`
	Size int    `json:"size"`
}

// Spanish stop words to exclude from word cloud
var spanishStopWords = map[string]bool{
	"el": true, "la": true, "los": true, "las": true,
	"un": true, "una": true, "unos": true, "unas": true,
	"de": true, "del": true, "al": true,
	"en": true, "a": true, "ante": true, "bajo": true, "con": true, "contra": true,
	"desde": true, "entre": true, "hacia": true, "hasta": true, "para": true, "por": true, "sin": true, "sobre": true, "tras": true,
	"y": true, "o": true, "u": true, "e": true,
	"ser": true, "estar": true, "haber": true, "tener": true, "hacer": true, "poder": true, "querer": true, "saber": true,
	"es": true, "son": true, "está": true, "están": true, "fue": true, "fueron": true, "era": true, "eran": true,
	"lo": true, "que": true, "como": true, "cuando": true, "donde": true, "quien": true,
	"me": true, "te": true, "se": true, "nos": true, "les": true, "nosotros": true, "vosotros": true, "ellos": true, "ellas": true,
	"mi": true, "tu": true, "su": true, "nuestro": true, "vuestro": true,
	"más": true, "mas": true, "muy": true, "menos": true,
	"si": true, "no": true, "ni": true, "ya": true, "aunque": true, "pero": true, "porque": true, "pues": true,
	"este": true, "esta": true, "estos": true, "estas": true, "ese": true, "esa": true, "esos": true, "esas": true,
	"aquel": true, "aquella": true, "aquellos": true, "aquellas": true,
	"todo": true, "toda": true, "todos": true, "todas": true, "algo": true, "alguien": true, "nada": true, "nadie": true,
	"cada": true, "tantos": true, "tanta": true, "tantas": true, "tanto": true,
	"uno": true, "dos": true, "tres": true, "cuatro": true, "cinco": true, "seis": true, "siete": true, "ocho": true, "nueve": true, "diez": true,
}

// GetWordCloud godoc
// @Summary Get word frequency data for word cloud
// @Description Returns word frequencies from song lyrics excluding stop
// @Description words. Honors the shared filter query parameters so the
// @Description word cloud stays in sync with the dashboard charts:
// @Description theme, year_from, year_to, clasificacion, album, q.
// @Tags stats
// @Produce json
// @Param theme         query string false "Comma-separated theme list; use __none__ for unclassified"
// @Param year_from     query int    false "Inclusive lower bound on year"
// @Param year_to       query int    false "Inclusive upper bound on year"
// @Param clasificacion query string false "Comma-separated classification list"
// @Param album         query string false "Exact album match"
// @Param q             query string false "Free-text search across title, lyrics, and album"
// @Success 200 {object} WordCloudResponse
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /word-cloud [get]
func GetWordCloud(c *gin.Context) {
	fp := ParseFilterParams(c)
	if msg := fp.ValidateYearRange(); msg != "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": msg})
		return
	}
	if msg := fp.ValidateQueryLength(256); msg != "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": msg})
		return
	}

	songFrom := "FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma"
	filterWhere, filterArgs := fp.ApplySongFilters("")

	// Cap on the number of songs scanned to keep the query fast even when
	// the catalog grows. We raise this to 8000 so a future catalog
	// expansion doesn't truncate the vocabulary the user sees in the
	// cloud.
	const maxSongs = 8000
	rows, err := database.DB.Query(
		"SELECT s.lyrics "+songFrom+whereWrap(filterWhere)+" LIMIT ?",
		append(filterArgs, maxSongs)...,
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error fetching lyrics"})
		return
	}
	defer func() { _ = rows.Close() }()

	wordCounts := make(map[string]int)
	totalWords := 0
	excludedCount := 0

	for rows.Next() {
		var letra string
		if err := rows.Scan(&letra); err == nil {
			words := extractWords(cleanLyrics(letra))
			for _, word := range words {
				wordLower := word
				totalWords++
				if spanishStopWords[wordLower] {
					excludedCount++
					continue
				}
				wordCounts[wordLower]++
			}
		}
	}

	// Convert to sorted slice and limit to top 500. The user wants a
	// dense cloud with the most frequent words from every song in the
	// filtered subset. The frontend placement algorithm picks which
	// of these actually render inside the viewBox.
	const topN = 500
	wordFreqs := make([]WordFreq, 0, len(wordCounts))
	for word, count := range wordCounts {
		wordFreqs = append(wordFreqs, WordFreq{Text: word, Size: count})
	}

	// Sort by size descending
	for i := 0; i < len(wordFreqs)-1; i++ {
		for j := i + 1; j < len(wordFreqs); j++ {
			if wordFreqs[j].Size > wordFreqs[i].Size {
				wordFreqs[i], wordFreqs[j] = wordFreqs[j], wordFreqs[i]
			}
		}
	}

	if len(wordFreqs) > topN {
		wordFreqs = wordFreqs[:topN]
	}

	// Scale sizes for visualization (min 10, max 100). The frontend
	// uses these as percentages of the SVG viewBox; the larger numbers
	// help the most-frequent words dominate visually.
	maxSize := 0
	if len(wordFreqs) > 0 {
		maxSize = wordFreqs[0].Size
	}
	for i := range wordFreqs {
		if maxSize > 0 {
			wordFreqs[i].Size = 10 + (wordFreqs[i].Size * 90 / maxSize)
		}
	}

	c.JSON(http.StatusOK, WordCloudResponse{
		Words:             wordFreqs,
		TotalWords:        totalWords,
		ExcludedStopWords: excludedCount,
	})
}

// cleanLyrics removes metadata markers and short parentheticals from raw lyrics text.
// This replicates the preprocessing in scripts/classify_songs.py.
func cleanLyrics(text string) string {
	// Cut at metadata markers (these appear at end of lyrics files)
	if idx := strings.Index(text, "Personajes:"); idx != -1 {
		text = text[:idx]
	}
	if idx := strings.Index(text, "Tema:"); idx != -1 {
		text = text[:idx]
	}
	if idx := strings.Index(text, "Dura:"); idx != -1 {
		text = text[:idx]
	}

	// Remove short parentheticals (content in parens shorter than 19 chars is metadata noise)
	// e.g. "(F. Gabilondo S.)" is metadata, but meaningful lyrics in parens are kept
	re := regexp.MustCompile(`\(.{0,18}\)`)
	text = re.ReplaceAllString(text, "")

	// Remove | and - used as separators in lyrics files
	text = strings.ReplaceAll(text, "|", "")
	text = strings.ReplaceAll(text, "-", "")

	// Collapse whitespace
	spaceRe := regexp.MustCompile(`\s+`)
	text = spaceRe.ReplaceAllString(text, " ")
	return strings.TrimSpace(text)
}

// extractWords splits text into words
func extractWords(text string) []string {
	var words []string
	var currentWord []rune
	for _, r := range text {
		if (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || (r >= 'á' && r <= 'ú') || (r >= 'Á' && r <= 'Ú') || (r >= 'ñ' && r <= 'ü') || (r >= 'Ñ' && r <= 'Ü') {
			currentWord = append(currentWord, r)
		} else {
			if len(currentWord) > 0 {
				words = append(words, string(currentWord))
				currentWord = nil
			}
		}
	}
	if len(currentWord) > 0 {
		words = append(words, string(currentWord))
	}
	return words
}
