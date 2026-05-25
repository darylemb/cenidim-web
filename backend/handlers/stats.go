package handlers

import (
	"net/http"
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
// @Description Returns aggregate metrics for the dashboard
// @Tags stats
// @Accept json
// @Produce json
// @Success 200 {object} StatsResponse
// @Failure 500 {object} map[string]string
// @Router /stats [get]
func GetStats(c *gin.Context) {
	stats := StatsResponse{
		SongsByYear:          make(map[string]int),
		SongsByClasificacion: make(map[string]int),
		TopAlbums:            []AlbumCount{},
		SongsByOovLevel:      make(map[string]int),
		SongsByIndigena:      make(map[string]int),
	}

	// Total songs
	if err := database.DB.QueryRow("SELECT COUNT(*) FROM songs").Scan(&stats.TotalSongs); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error fetching total songs"})
		return
	}

	// Total albums
	if err := database.DB.QueryRow("SELECT COUNT(*) FROM fonogramas").Scan(&stats.TotalAlbums); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error fetching total albums"})
		return
	}

	// Songs by year (excluding "s/d" and empty years)
	yearRows, yearErr := database.DB.Query(`
		SELECT COALESCE(f.anio, 'Unknown'), COUNT(*)
		FROM songs s
		JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma
		WHERE f.anio IS NOT NULL AND f.anio != '' AND f.anio != 's/d'
		GROUP BY f.anio
		ORDER BY f.anio`)
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

	// Songs by clasificacion
	clasRows, clasErr := database.DB.Query(`
		SELECT COALESCE(s.clasificacion, 'ESPAÑOL_ESTANDAR'), COUNT(*) 
		FROM songs s 
		GROUP BY s.clasificacion`)
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

	// Recently added (last 30 days)
	thirtyDaysAgo := time.Now().AddDate(0, 0, -30).Format("2006-01-02")
	if err := database.DB.QueryRow(
		"SELECT COUNT(*) FROM songs WHERE created_at > ?", thirtyDaysAgo,
	).Scan(&stats.RecentlyAdded); err != nil {
		stats.RecentlyAdded = 0
	}

	// Top albums by song count
	topRows, topErr := database.DB.Query(`
		SELECT f.titulo, f.anio, COUNT(*) as song_count
		FROM songs s
		JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma
		GROUP BY f.clave_fonograma
		ORDER BY song_count DESC
		LIMIT 10`)
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

	// Songs with lyrics count
	if err := database.DB.QueryRow(
		"SELECT COUNT(*) FROM songs WHERE lyrics IS NOT NULL AND lyrics != ''",
	).Scan(&stats.SongsWithLyrics); err != nil {
		stats.SongsWithLyrics = 0
	}

	// Average lyrics length
	if err := database.DB.QueryRow(
		"SELECT AVG(LENGTH(lyrics)) FROM songs WHERE lyrics IS NOT NULL AND lyrics != ''",
	).Scan(&stats.AvgLyricsLength); err != nil {
		stats.AvgLyricsLength = 0
	}

	// Songs by OOV level (from song_stats table)
	oovRows, oovErr := database.DB.Query(`
		SELECT
			CASE
				WHEN pct_oov < 5 THEN 'BAJA'
				WHEN pct_oov >= 5 AND pct_oov < 18 THEN 'MEDIA'
				ELSE 'ALTA'
			END as oov_level,
			COUNT(*) as count
		FROM song_stats
		GROUP BY oov_level`)
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

	// Songs by indigena presence (from song_stats table)
	indRows, indErr := database.DB.Query(`
		SELECT
			CASE WHEN contiene_indigena = 1 THEN 'CON_INDIGENA' ELSE 'SIN_INDIGENA' END,
			COUNT(*) as count
		FROM song_stats
		GROUP BY contiene_indigena`)
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

	// Songs without year (s/d or empty/null)
	if err := database.DB.QueryRow(`
		SELECT COUNT(*) FROM songs s
		JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma
		WHERE f.anio IS NULL OR f.anio = '' OR f.anio = 's/d'
	`).Scan(&stats.SongsWithoutYear); err != nil {
		stats.SongsWithoutYear = 0
	}

	c.JSON(http.StatusOK, stats)
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
// @Description Returns word frequencies from song lyrics excluding stop words
// @Tags stats
// @Produce json
// @Success 200 {object} WordCloudResponse
// @Failure 500 {object} map[string]string
// @Router /word-cloud [get]
func GetWordCloud(c *gin.Context) {
	wordCounts := make(map[string]int)
	totalWords := 0
	excludedCount := 0

	// Get all lyrics
	rows, err := database.DB.Query("SELECT lyrics FROM songs WHERE lyrics IS NOT NULL AND lyrics != ''")
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error fetching lyrics"})
		return
	}
	defer func() { _ = rows.Close() }()

	for rows.Next() {
		var letra string
		if err := rows.Scan(&letra); err == nil {
			words := extractWords(letra)
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

	// Convert to sorted slice and limit to top 100
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

	// Limit to top 100 words
	if len(wordFreqs) > 100 {
		wordFreqs = wordFreqs[:100]
	}

	// Scale sizes for visualization (min 10, max 100)
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
		TotalWords:       totalWords,
		ExcludedStopWords: excludedCount,
	})
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
