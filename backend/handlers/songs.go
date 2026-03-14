package handlers

import (
	"database/sql"
	"fmt"
	"net/http"
	"strconv"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/daryl/cenidim-go-api/models"
	"github.com/gin-gonic/gin"
)

func SearchSongs(c *gin.Context) {
	query := c.DefaultQuery("query", "")
	field := c.DefaultQuery("field", "all")

	baseQuery := `
		SELECT s.id, s.title, a.name as album, s.filename
		FROM songs s
		JOIN albums a ON s.album_id = a.id
	`

	var rows *sql.Rows
	var err error
	searchTerm := fmt.Sprintf("%%%s%%", query)

	if query != "" {
		switch field {
		case "title":
			rows, err = database.DB.Query(baseQuery+" WHERE s.title LIKE ?", searchTerm)
		case "album":
			rows, err = database.DB.Query(baseQuery+" WHERE a.name LIKE ?", searchTerm)
		case "lyrics":
			rows, err = database.DB.Query(baseQuery+" WHERE s.lyrics LIKE ?", searchTerm)
		default: // "all"
			rows, err = database.DB.Query(
				baseQuery+" WHERE s.title LIKE ? OR a.name LIKE ? OR s.lyrics LIKE ?",
				searchTerm, searchTerm, searchTerm,
			)
		}
	} else {
		rows, err = database.DB.Query(baseQuery + " LIMIT 100")
	}

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer func() { _ = rows.Close() }()

	songs := []models.Song{}
	for rows.Next() {
		var s models.Song
		if err := rows.Scan(&s.ID, &s.Title, &s.Album, &s.Filename); err != nil {
			continue
		}
		songs = append(songs, s)
	}

	c.JSON(http.StatusOK, songs)
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
