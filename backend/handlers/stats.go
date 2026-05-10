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

	// Songs by year
	yearRows, yearErr := database.DB.Query(`
		SELECT COALESCE(f.anio, 'Unknown'), COUNT(*) 
		FROM songs s 
		JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma 
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
		var clas string
		var count int
		if err := clasRows.Scan(&clas, &count); err == nil {
			stats.SongsByClasificacion[clas] = count
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

	c.JSON(http.StatusOK, stats)
}
