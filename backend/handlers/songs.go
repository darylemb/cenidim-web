package handlers

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"strconv"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/daryl/cenidim-go-api/models"
	"github.com/gin-gonic/gin"
)

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
		SELECT s.id, s.title, a.name as album, s.filename
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
		if err := rows.Scan(&s.ID, &s.Title, &s.Album, &s.Filename); err != nil {
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

func GetSong(c *gin.Context) {
	idStr := c.Param("song_id")
	id, err := strconv.Atoi(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid song ID"})
		return
	}

	query := `
		SELECT s.id, s.title, a.name as album, s.filename, s.lyrics
		FROM songs s
		JOIN albums a ON s.album_id = a.id
		WHERE s.id = ?
	`

	var s models.SongDetail
	err = database.DB.QueryRow(query, id).Scan(&s.ID, &s.Title, &s.Album, &s.Filename, &s.Lyrics)

	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"error": "Song not found"})
		return
	} else if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, s)
}
