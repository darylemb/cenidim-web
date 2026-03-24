package handlers

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"regexp"
	"sort"
	"strconv"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/daryl/cenidim-go-api/models"
	"github.com/gin-gonic/gin"
)

// SearchSongs godoc
// @Summary Search songs
// @Description Search songs by title, album, or lyrics with pagination
// @Tags songs
// @Accept  json
// @Produce  json
// @Param query query string false "Search query"
// @Param field query string false "Field to search in (title, album, lyrics, all)"
// @Param page query int false "Page number"
// @Param limit query int false "Items per page"
// @Success 200 {object} map[string]interface{}
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /search [get]
func SearchSongs(c *gin.Context) {
	query := c.DefaultQuery("query", "")
	field := c.DefaultQuery("field", "all")
	pageStr := c.DefaultQuery("page", "1")
	limitStr := c.DefaultQuery("limit", "20")

	page, err := strconv.Atoi(pageStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid 'page' parameter; must be an integer"})
		return
	}
	limit, err := strconv.Atoi(limitStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid 'limit' parameter; must be an integer"})
		return
	}
	if page < 1 {
		page = 1
	}
	if limit < 1 {
		limit = 20
	}
	if limit > 100 {
		limit = 100
	}
	offset := (page - 1) * limit

	searchTerm := fmt.Sprintf("%%%s%%", query)

	countQuery := "SELECT COUNT(*) FROM songs s JOIN albums a ON s.album_id = a.id"
	searchQuery := `
		SELECT s.id, s.title, a.name as album, a.year, s.filename
		FROM songs s
		JOIN albums a ON s.album_id = a.id
	`

	var whereClause string
	var args []interface{}

	if query != "" {
		switch field {
		case "title":
			whereClause = " WHERE s.title LIKE ?"
			args = append(args, searchTerm)
		case "album":
			whereClause = " WHERE a.name LIKE ?"
			args = append(args, searchTerm)
		case "lyrics":
			whereClause = " WHERE s.lyrics LIKE ?"
			args = append(args, searchTerm)
		default: // "all"
			whereClause = " WHERE s.title LIKE ? OR a.name LIKE ? OR s.lyrics LIKE ?"
			args = append(args, searchTerm, searchTerm, searchTerm)
		}
	}

	// Get total count
	var total int
	err = database.DB.QueryRow(countQuery+whereClause, args...).Scan(&total)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error counting results"})
		return
	}

	// Get paginated results
	finalQuery := searchQuery + whereClause + " ORDER BY s.id LIMIT ? OFFSET ?"
	args = append(args, limit, offset)

	rows, err := database.DB.Query(finalQuery, args...)
	if err != nil {
		log.Printf("error querying songs: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error searching results"})
		return
	}
	defer func() { _ = rows.Close() }()

	songs := []models.Song{}
	for rows.Next() {
		var s models.Song
		if err := rows.Scan(&s.ID, &s.Title, &s.Album, &s.Year, &s.Filename); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Error reading results"})
			return
		}
		songs = append(songs, s)
	}
	if err := rows.Err(); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error iterating results"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"results": songs,
		"total":   total,
	})
}

// GetSong godoc
// @Summary Get song detail
// @Description Get detailed information about a song by ID
// @Tags songs
// @Accept  json
// @Produce  json
// @Param song_id path int true "Song ID"
// @Success 200 {object} models.SongDetail
// @Failure 400 {object} map[string]string
// @Failure 404 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /song/{song_id} [get]
func GetSong(c *gin.Context) {
	idStr := c.Param("song_id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid song ID"})
		return
	}

	query := `
		SELECT s.id, s.title, a.name as album, a.year, s.filename, s.lyrics
		FROM songs s
		JOIN albums a ON s.album_id = a.id
		WHERE s.id = ?
	`

	var s models.SongDetail
	err = database.DB.QueryRow(query, id).Scan(&s.ID, &s.Title, &s.Album, &s.Year, &s.Filename, &s.Lyrics)

	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"error": "Song not found"})
		return
	} else if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, s)
}

// GetTimeline godoc
// @Summary Get songs timeline
// @Description Get songs grouped by year for the timeline view
// @Tags songs
// @Accept  json
// @Produce  json
// @Success 200 {object} map[string][]models.Song
// @Failure 500 {object} map[string]string
// @Router /timeline [get]
func GetTimeline(c *gin.Context) {
	query := `
		SELECT s.id, s.title, a.name as album, a.year, s.filename
		FROM songs s
		JOIN albums a ON s.album_id = a.id
		WHERE a.year IS NOT NULL AND a.year != ''
	`

	rows, err := database.DB.Query(query)
	if err != nil {
		log.Printf("error querying timeline: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error fetching timeline data"})
		return
	}
	defer func() { _ = rows.Close() }()

	timeline := make(map[string][]models.Song)
	re := regexp.MustCompile(`\d{4}`)
	
	type YearGroup struct {
		Key     string
		SortKey int
	}
	yearGroups := []YearGroup{}
	seenKeys := make(map[string]bool)

	for rows.Next() {
		var s models.Song
		if err := rows.Scan(&s.ID, &s.Title, &s.Album, &s.Year, &s.Filename); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Error reading timeline results"})
			return
		}
		
		// Normalize: Extract first 4 digits
		key := re.FindString(s.Year)
		if key == "" {
			key = s.Year // Fallback if no digits found
		}
		
		if !seenKeys[key] {
			sortKey := 0
			if k, err := strconv.Atoi(key); err == nil {
				sortKey = k
			}
			yearGroups = append(yearGroups, YearGroup{Key: key, SortKey: sortKey})
			seenKeys[key] = true
		}
		
		timeline[key] = append(timeline[key], s)
	}

	// Sort yearGroups by SortKey
	sort.Slice(yearGroups, func(i, j int) bool {
		if yearGroups[i].SortKey != yearGroups[j].SortKey {
			return yearGroups[i].SortKey < yearGroups[j].SortKey
		}
		return yearGroups[i].Key < yearGroups[j].Key
	})

	// Extract sorted keys
	sortedKeys := make([]string, len(yearGroups))
	for i, yg := range yearGroups {
		sortedKeys[i] = yg.Key
	}

	c.JSON(http.StatusOK, gin.H{
		"years":    sortedKeys,
		"timeline": timeline,
	})
}
