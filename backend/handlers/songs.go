package handlers

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"
	"regexp"
	"sort"
	"strconv"
	"strings"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/daryl/cenidim-go-api/models"
	"github.com/gin-gonic/gin"
)

// SearchSongs godoc
// @Summary Search songs
// @Description Search songs by title, album, or lyrics with pagination. Honors
// @Description the shared filter parameters: theme, year_from, year_to,
// @Description clasificacion, album, q.
// @Tags songs
// @Accept  json
// @Produce  json
// @Param query         query string false "Search query (deprecated alias for q)"
// @Param q             query string false "Search query"
// @Param field         query string false "Field to search in (title, album, lyrics, all)"
// @Param theme         query string false "Comma-separated theme list; use __none__ for unclassified"
// @Param year_from     query int    false "Inclusive lower bound on year"
// @Param year_to       query int    false "Inclusive upper bound on year"
// @Param clasificacion query string false "Filter by clasificacion (ESPAÑOL_ESTANDAR, ESPAÑOL_REGIONAL, LENGUA_INDIGENA)"
// @Param album         query string false "Exact album match"
// @Param order_by      query string false "Sort field (id, clave, title, album, year, filename, clasificacion)"
// @Param order_dir     query string false "Sort direction (asc, desc)"
// @Param page          query int    false "Page number"
// @Param limit         query int    false "Items per page"
// @Success 200 {object} map[string]interface{}
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /search [get]
func SearchSongs(c *gin.Context) {
	// `q` wins; `query` is kept as a deprecated alias.
	qRaw := strings.TrimSpace(c.Query("q"))
	if qRaw == "" {
		qRaw = strings.TrimSpace(c.Query("query"))
	}
	field := c.DefaultQuery("field", "all")
	clasificacion := c.DefaultQuery("clasificacion", "")
	orderBy := c.DefaultQuery("order_by", "id")
	orderDir := c.DefaultQuery("order_dir", "asc")
	pageStr := c.DefaultQuery("page", "1")
	limitStr := c.DefaultQuery("limit", "20")

	fp := ParseFilterParams(c)
	// If the caller used the legacy `query` parameter, route it through the
	// shared `Q` field so ApplySongFilters can find it.
	if fp.Q == "" {
		fp.Q = qRaw
	}
	if msg := fp.ValidateYearRange(); msg != "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": msg})
		return
	}
	if msg := fp.ValidateQueryLength(256); msg != "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": msg})
		return
	}

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

	searchTerm := fmt.Sprintf("%%%s%%", qRaw)

	countQuery := "SELECT COUNT(*) FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma"
	searchQuery := `
		SELECT s.id, s.fonograma_id, s.title, COALESCE(s.filename,''),
		       f.titulo, COALESCE(f.subtitulo,''), COALESCE(f.interprete_principal,''), COALESCE(f.interpretes_invitados,''),
		       COALESCE(f.interprete_participante,''), COALESCE(f.soporte_fisico,''), COALESCE(f.editora,''), COALESCE(f.numero_catalogo,''),
		       COALESCE(f.ciudad_edicion,''), COALESCE(f.pais_edicion,''), COALESCE(f.anio,''), COALESCE(f.pistas,''), COALESCE(f.observaciones,''),
		       COALESCE(s.clasificacion,''), COALESCE(s.tema,'')
		FROM songs s
		JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma
	`

	var conditions []string
	var args []interface{}

	if qRaw != "" {
		switch field {
		case "title":
			conditions = append(conditions, "s.title LIKE ?")
			args = append(args, searchTerm)
		case "album":
			conditions = append(conditions, "f.titulo LIKE ?")
			args = append(args, searchTerm)
		case "lyrics":
			conditions = append(conditions, "s.lyrics LIKE ?")
			args = append(args, searchTerm)
		default: // "all"
			conditions = append(conditions, "(s.title LIKE ? OR f.titulo LIKE ? OR s.lyrics LIKE ?)")
			args = append(args, searchTerm, searchTerm, searchTerm)
		}
	}

	if clasificacion != "" {
		if clasificacion == "ESPAÑOL_ESTANDAR" {
			// Songs with empty/NULL clasificacion are treated as Español Estándar
			conditions = append(conditions, "(s.clasificacion = ? OR COALESCE(s.clasificacion,'') = '')")
			args = append(args, clasificacion)
		} else {
			conditions = append(conditions, "s.clasificacion = ?")
			args = append(args, clasificacion)
		}
	}

	// Apply the shared filter parameters (theme, year range, etc.).
	prior := ""
	if len(conditions) > 0 {
		prior = conditions[0]
		for _, c := range conditions[1:] {
			prior += " AND " + c
		}
	}
	filterCond, filterArgs := fp.ApplySongFilters(prior)
	args = append(args, filterArgs...)

	validOrderFields := map[string]bool{
		"id": true, "clave": true, "title": true, "album": true,
		"year": true, "filename": true, "clasificacion": true,
	}
	if !validOrderFields[orderBy] {
		orderBy = "id"
	}

	orderFieldMap := map[string]string{
		"id":            "s.id",
		"clave":         "s.fonograma_id",
		"title":         "s.title",
		"album":         "f.titulo",
		"year":          "f.anio",
		"filename":      "s.filename",
		"clasificacion": "s.clasificacion",
	}
	sqlOrderField := orderFieldMap[orderBy]
	orderDir = strings.ToLower(orderDir)
	if orderDir != "desc" {
		orderDir = "asc"
	}

	// Always push empty/NULL values to the end regardless of sort direction.
	orderClause := " ORDER BY CASE WHEN COALESCE(" + sqlOrderField + ", '') = '' THEN 1 ELSE 0 END ASC, " + sqlOrderField + " " + orderDir

	var whereClause string
	if filterCond != "" {
		whereClause = " WHERE " + filterCond
	}

	// Get total count
	var total int
	err = database.DB.QueryRow(countQuery+whereClause, args...).Scan(&total)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error counting results"})
		return
	}

	// Get paginated results
	finalQuery := searchQuery + whereClause + orderClause + " LIMIT ? OFFSET ?"
	paginatedArgs := append(args, limit, offset)

	rows, err := database.DB.Query(finalQuery, paginatedArgs...)
	if err != nil {
		log.Printf("error querying songs: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error searching results"})
		return
	}
	defer func() { _ = rows.Close() }()

	songs := []models.Song{}
	for rows.Next() {
		var s models.Song
		if err := rows.Scan(
			&s.ID, &s.FonogramaID, &s.Title, &s.Filename,
			&s.Album, &s.Subtitulo, &s.InterpretePrincipal, &s.InterpretesInvitados,
			&s.InterpreteParticipante, &s.SoporteFisico, &s.Editora, &s.NumeroCatalogo,
			&s.CiudadEdicion, &s.PaisEdicion, &s.Year, &s.Pistas, &s.Observaciones,
			&s.Clasificacion, &s.Tema,
		); err != nil {
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
		SELECT s.id, s.fonograma_id, s.title, COALESCE(s.filename,''),
		       f.titulo, COALESCE(f.subtitulo,''), COALESCE(f.interprete_principal,''), COALESCE(f.interpretes_invitados,''),
		       COALESCE(f.interprete_participante,''), COALESCE(f.soporte_fisico,''), COALESCE(f.editora,''), COALESCE(f.numero_catalogo,''),
		       COALESCE(f.ciudad_edicion,''), COALESCE(f.pais_edicion,''), COALESCE(f.anio,''), COALESCE(f.pistas,''), COALESCE(f.observaciones,''),
		       COALESCE(s.clasificacion,''), COALESCE(s.lyrics,'')
		FROM songs s
		JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma
		WHERE s.id = ?
	`

	var s models.SongDetail
	err = database.DB.QueryRow(query, id).Scan(
		&s.ID, &s.FonogramaID, &s.Title, &s.Filename,
		&s.Album, &s.Subtitulo, &s.InterpretePrincipal, &s.InterpretesInvitados,
		&s.InterpreteParticipante, &s.SoporteFisico, &s.Editora, &s.NumeroCatalogo,
		&s.CiudadEdicion, &s.PaisEdicion, &s.Year, &s.Pistas, &s.Observaciones,
		&s.Clasificacion, &s.Lyrics,
	)

	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"error": "Song not found"})
		return
	} else if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
		return
	}

	c.JSON(http.StatusOK, s)
}

// GetTimeline godoc
// @Summary Get songs timeline
// @Description Get songs grouped by year for the timeline view. Honors the
// @Description shared filter parameters: theme, year_from, year_to,
// @Description clasificacion, album, q. Songs without a year (s/d) are
// @Description grouped under the literal key "s/d" in the response; when a
// @Description year range is supplied, the s/d bucket is omitted.
// @Tags songs
// @Accept  json
// @Produce  json
// @Param theme         query string false "Comma-separated theme list; use __none__ for unclassified"
// @Param year_from     query int    false "Inclusive lower bound on year"
// @Param year_to       query int    false "Inclusive upper bound on year"
// @Param clasificacion query string false "Comma-separated classification list"
// @Param album         query string false "Exact album match"
// @Param q             query string false "Free-text search across title, lyrics, and album"
// @Success 200 {object} map[string][]models.Song
// @Failure 400 {object} map[string]string
// @Failure 500 {object} map[string]string
// @Router /timeline [get]
func GetTimeline(c *gin.Context) {
	limitStr := c.DefaultQuery("limit", "1000")
	limit := 1000
	if l, err := strconv.Atoi(limitStr); err == nil && l > 0 && l <= 5000 {
		limit = l
	}

	fp := ParseFilterParams(c)
	if msg := fp.ValidateYearRange(); msg != "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": msg})
		return
	}
	if msg := fp.ValidateQueryLength(256); msg != "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": msg})
		return
	}

	priorWhere := "f.anio IS NOT NULL AND f.anio != ''"
	// When a year range is supplied the s/d bucket is omitted; the SQL "no
	// year" predicate becomes redundant so we drop it.
	if fp.YearFrom != nil || fp.YearTo != nil {
		priorWhere = "f.anio != ''"
	}
	whereCond, whereArgs := fp.ApplySongFilters(priorWhere)

	query := `
		SELECT s.id, s.fonograma_id, s.title, COALESCE(s.filename,''),
		       f.titulo, COALESCE(f.subtitulo,''), COALESCE(f.interprete_principal,''), COALESCE(f.interpretes_invitados,''),
		       COALESCE(f.interprete_participante,''), COALESCE(f.soporte_fisico,''), COALESCE(f.editora,''), COALESCE(f.numero_catalogo,''),
		       COALESCE(f.ciudad_edicion,''), COALESCE(f.pais_edicion,''), COALESCE(f.anio,''), COALESCE(f.pistas,''), COALESCE(f.observaciones,''),
		       COALESCE(s.clasificacion,''), COALESCE(s.tema,'')
		FROM songs s
		JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma
	` + whereWrap(whereCond) + `
		LIMIT ?
	`
	args := append(whereArgs, limit)

	countQuery := `SELECT COUNT(*) FROM songs s JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma ` + whereWrap(whereCond)
	var total int
	if err := database.DB.QueryRow(countQuery, whereArgs...).Scan(&total); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error counting timeline data"})
		return
	}

	rows, err := database.DB.Query(query, args...)
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
		if err := rows.Scan(
			&s.ID, &s.FonogramaID, &s.Title, &s.Filename,
			&s.Album, &s.Subtitulo, &s.InterpretePrincipal, &s.InterpretesInvitados,
			&s.InterpreteParticipante, &s.SoporteFisico, &s.Editora, &s.NumeroCatalogo,
			&s.CiudadEdicion, &s.PaisEdicion, &s.Year, &s.Pistas, &s.Observaciones,
			&s.Clasificacion, &s.Tema,
		); err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Error reading timeline results"})
			return
		}

		key := re.FindString(s.Year)
		if key == "" {
			key = s.Year
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
		if len(timeline[key]) > 100 {
			continue
		}
	}

	sort.Slice(yearGroups, func(i, j int) bool {
		if yearGroups[i].SortKey != yearGroups[j].SortKey {
			return yearGroups[i].SortKey < yearGroups[j].SortKey
		}
		return yearGroups[i].Key < yearGroups[j].Key
	})

	sortedKeys := make([]string, len(yearGroups))
	for i, yg := range yearGroups {
		sortedKeys[i] = yg.Key
	}

	c.JSON(http.StatusOK, gin.H{
		"years":    sortedKeys,
		"timeline": timeline,
		"total":    total,
		"truncated": total > limit,
	})
}
