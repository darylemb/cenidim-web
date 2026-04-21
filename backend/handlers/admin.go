package handlers

import (
	"database/sql"
	"net/http"
	"strconv"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/daryl/cenidim-go-api/models"
	"github.com/gin-gonic/gin"
	"golang.org/x/crypto/bcrypt"
)

// ─── Fonogramas CRUD ─────────────────────────────────────────────────────────

func AdminListFonogramas(c *gin.Context) {
	pageStr := c.DefaultQuery("page", "1")
	limitStr := c.DefaultQuery("limit", "20")
	page, _ := strconv.Atoi(pageStr)
	limit, _ := strconv.Atoi(limitStr)
	if page < 1 {
		page = 1
	}
	if limit < 1 || limit > 200 {
		limit = 20
	}
	offset := (page - 1) * limit

	var total int
	if err := database.DB.QueryRow("SELECT COUNT(*) FROM fonogramas").Scan(&total); err != nil {
		total = 0
	}

	rows, err := database.DB.Query(`
		SELECT clave_fonograma, titulo, subtitulo, interprete_principal, interpretes_invitados,
		       interprete_participante, soporte_fisico, editora, numero_catalogo,
		       ciudad_edicion, pais_edicion, anio, pistas, observaciones
		FROM fonogramas ORDER BY clave_fonograma LIMIT ? OFFSET ?`, limit, offset)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer func() { _ = rows.Close() }()

	var list []models.Fonograma
	for rows.Next() {
		var f models.Fonograma
		if err := rows.Scan(&f.ClaveFonograma, &f.Titulo, &f.Subtitulo, &f.InterpretePrincipal,
			&f.InterpretesInvitados, &f.InterpreteParticipante, &f.SoporteFisico,
			&f.Editora, &f.NumeroCatalogo, &f.CiudadEdicion, &f.PaisEdicion,
			&f.Anio, &f.Pistas, &f.Observaciones); err != nil {
			continue
		}
		list = append(list, f)
	}
	if list == nil {
		list = []models.Fonograma{}
	}
	c.JSON(http.StatusOK, gin.H{"results": list, "total": total})
}

func AdminGetFonograma(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
		return
	}
	var f models.Fonograma
	err = database.DB.QueryRow(`
		SELECT clave_fonograma, titulo, subtitulo, interprete_principal, interpretes_invitados,
		       interprete_participante, soporte_fisico, editora, numero_catalogo,
		       ciudad_edicion, pais_edicion, anio, pistas, observaciones
		FROM fonogramas WHERE clave_fonograma = ?`, id).Scan(
		&f.ClaveFonograma, &f.Titulo, &f.Subtitulo, &f.InterpretePrincipal,
		&f.InterpretesInvitados, &f.InterpreteParticipante, &f.SoporteFisico,
		&f.Editora, &f.NumeroCatalogo, &f.CiudadEdicion, &f.PaisEdicion,
		&f.Anio, &f.Pistas, &f.Observaciones)
	if err == sql.ErrNoRows {
		c.JSON(http.StatusNotFound, gin.H{"error": "Fonograma not found"})
		return
	}
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, f)
}

func AdminCreateFonograma(c *gin.Context) {
	var f models.Fonograma
	if err := c.ShouldBindJSON(&f); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	_, err := database.DB.Exec(`
		INSERT INTO fonogramas (clave_fonograma, titulo, subtitulo, interprete_principal,
		  interpretes_invitados, interprete_participante, soporte_fisico, editora,
		  numero_catalogo, ciudad_edicion, pais_edicion, anio, pistas, observaciones)
		VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
		f.ClaveFonograma, f.Titulo, f.Subtitulo, f.InterpretePrincipal,
		f.InterpretesInvitados, f.InterpreteParticipante, f.SoporteFisico,
		f.Editora, f.NumeroCatalogo, f.CiudadEdicion, f.PaisEdicion,
		f.Anio, f.Pistas, f.Observaciones)
	if err != nil {
		c.JSON(http.StatusConflict, gin.H{"error": "ClaveFonograma already exists or invalid data"})
		return
	}
	c.JSON(http.StatusCreated, f)
}

func AdminUpdateFonograma(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
		return
	}
	var f models.Fonograma
	if bindErr := c.ShouldBindJSON(&f); bindErr != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": bindErr.Error()})
		return
	}
	res, err := database.DB.Exec(`
		UPDATE fonogramas SET titulo=?, subtitulo=?, interprete_principal=?,
		  interpretes_invitados=?, interprete_participante=?, soporte_fisico=?,
		  editora=?, numero_catalogo=?, ciudad_edicion=?, pais_edicion=?,
		  anio=?, pistas=?, observaciones=?
		WHERE clave_fonograma=?`,
		f.Titulo, f.Subtitulo, f.InterpretePrincipal, f.InterpretesInvitados,
		f.InterpreteParticipante, f.SoporteFisico, f.Editora, f.NumeroCatalogo,
		f.CiudadEdicion, f.PaisEdicion, f.Anio, f.Pistas, f.Observaciones, id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "Fonograma not found"})
		return
	}
	f.ClaveFonograma = id
	c.JSON(http.StatusOK, f)
}

func AdminDeleteFonograma(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
		return
	}
	// Delete associated songs first
	if _, execErr := database.DB.Exec("DELETE FROM songs WHERE fonograma_id = ?", id); execErr != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": execErr.Error()})
		return
	}
	res, err := database.DB.Exec("DELETE FROM fonogramas WHERE clave_fonograma = ?", id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "Fonograma not found"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Fonograma deleted"})
}

// ─── Songs CRUD ───────────────────────────────────────────────────────────────

func AdminListSongs(c *gin.Context) {
	fonogramaIDStr := c.DefaultQuery("fonograma_id", "")
	pageStr := c.DefaultQuery("page", "1")
	limitStr := c.DefaultQuery("limit", "50")
	page, _ := strconv.Atoi(pageStr)
	limit, _ := strconv.Atoi(limitStr)
	if page < 1 {
		page = 1
	}
	if limit < 1 || limit > 500 {
		limit = 50
	}
	offset := (page - 1) * limit

	where := ""
	var args []interface{}
	if fonogramaIDStr != "" {
		where = " WHERE s.fonograma_id = ?"
		args = append(args, fonogramaIDStr)
	}

	var total int
	if err := database.DB.QueryRow("SELECT COUNT(*) FROM songs s"+where, args...).Scan(&total); err != nil {
		total = 0
	}

	queryArgs := append(args, limit, offset)
	rows, err := database.DB.Query(`
		SELECT s.id, s.fonograma_id, s.title, f.titulo, f.anio, s.filename, s.lyrics
		FROM songs s
		JOIN fonogramas f ON s.fonograma_id = f.clave_fonograma`+where+
		` ORDER BY s.id LIMIT ? OFFSET ?`, queryArgs...)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer func() { _ = rows.Close() }()

	type AdminSong struct {
		models.SongDetail
	}
	var list []AdminSong
	for rows.Next() {
		var s AdminSong
		if err := rows.Scan(&s.ID, &s.FonogramaID, &s.Title, &s.Album, &s.Year, &s.Filename, &s.Lyrics); err != nil {
			continue
		}
		list = append(list, s)
	}
	if list == nil {
		list = []AdminSong{}
	}
	c.JSON(http.StatusOK, gin.H{"results": list, "total": total})
}

func AdminUpdateSong(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
		return
	}
	var input struct {
		Title  string `json:"title"`
		Lyrics string `json:"lyrics"`
	}
	if bindErr := c.ShouldBindJSON(&input); bindErr != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": bindErr.Error()})
		return
	}
	res, err := database.DB.Exec(
		`UPDATE songs SET title=?, lyrics=? WHERE id=?`,
		input.Title, input.Lyrics, id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "Song not found"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Song updated"})
}

func AdminDeleteSong(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
		return
	}
	res, err := database.DB.Exec("DELETE FROM songs WHERE id = ?", id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "Song not found"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "Song deleted"})
}

func AdminCreateSong(c *gin.Context) {
	var input struct {
		FonogramaID int    `json:"fonograma_id" binding:"required"`
		Title       string `json:"title"        binding:"required"`
		Lyrics      string `json:"lyrics"`
	}
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	res, err := database.DB.Exec(
		`INSERT INTO songs (fonograma_id, title, lyrics) VALUES (?,?,?)`,
		input.FonogramaID, input.Title, input.Lyrics)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	id, _ := res.LastInsertId()
	c.JSON(http.StatusCreated, gin.H{"id": id, "message": "Song created"})
}

// ─── Users CRUD (admin only) ─────────────────────────────────────────────────

func AdminListUsers(c *gin.Context) {
	rows, err := database.DB.Query(
		`SELECT id, username, email, role, created_at FROM users ORDER BY id`)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer func() { _ = rows.Close() }()

	var list []models.User
	for rows.Next() {
		var u models.User
		if err := rows.Scan(&u.ID, &u.Username, &u.Email, &u.Role, &u.CreatedAt); err != nil {
			continue
		}
		list = append(list, u)
	}
	if list == nil {
		list = []models.User{}
	}
	c.JSON(http.StatusOK, list)
}

func AdminCreateUser(c *gin.Context) {
	var input models.UserInput
	if err := c.ShouldBindJSON(&input); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	role := input.Role
	if role == "" || (role != "admin" && role != "editor" && role != "viewer") {
		role = "viewer"
	}
	hash, err := bcrypt.GenerateFromPassword([]byte(input.Password), bcrypt.DefaultCost)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Error processing password"})
		return
	}
	res, err := database.DB.Exec(
		`INSERT INTO users (username, email, password_hash, role) VALUES (?,?,?,?)`,
		input.Username, input.Email, string(hash), role)
	if err != nil {
		c.JSON(http.StatusConflict, gin.H{"error": "Username or email already exists"})
		return
	}
	id, _ := res.LastInsertId()
	c.JSON(http.StatusCreated, gin.H{
		"user": gin.H{"id": id, "username": input.Username, "email": input.Email, "role": role},
	})
}

func AdminUpdateUser(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
		return
	}
	var input struct {
		Username string `json:"username"`
		Email    string `json:"email"`
		Role     string `json:"role"`
		Password string `json:"password"`
	}
	if bindErr := c.ShouldBindJSON(&input); bindErr != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": bindErr.Error()})
		return
	}
	if input.Role != "" && input.Role != "admin" && input.Role != "editor" && input.Role != "viewer" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid role"})
		return
	}

	if input.Password != "" {
		hash, hashErr := bcrypt.GenerateFromPassword([]byte(input.Password), bcrypt.DefaultCost)
		if hashErr != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Error processing password"})
			return
		}
		if _, execErr := database.DB.Exec(
			`UPDATE users SET password_hash=? WHERE id=?`, string(hash), id); execErr != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": execErr.Error()})
			return
		}
	}

	if input.Username != "" {
		if _, execErr := database.DB.Exec(`UPDATE users SET username=? WHERE id=?`, input.Username, id); execErr != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": execErr.Error()})
			return
		}
	}
	if input.Email != "" {
		if _, execErr := database.DB.Exec(`UPDATE users SET email=? WHERE id=?`, input.Email, id); execErr != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": execErr.Error()})
			return
		}
	}
	if input.Role != "" {
		if _, execErr := database.DB.Exec(`UPDATE users SET role=? WHERE id=?`, input.Role, id); execErr != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": execErr.Error()})
			return
		}
	}
	c.JSON(http.StatusOK, gin.H{"message": "User updated"})
}

func AdminDeleteUser(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid ID"})
		return
	}
	// Don't allow deleting the last admin
	var adminCount int
	if scanErr := database.DB.QueryRow(
		`SELECT COUNT(*) FROM users WHERE role='admin'`).Scan(&adminCount); scanErr != nil {
		adminCount = 0
	}

	var targetRole string
	if scanErr := database.DB.QueryRow(`SELECT role FROM users WHERE id=?`, id).Scan(&targetRole); scanErr != nil {
		targetRole = ""
	}
	if targetRole == "admin" && adminCount <= 1 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Cannot delete the last admin"})
		return
	}

	res, err := database.DB.Exec("DELETE FROM users WHERE id = ?", id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		c.JSON(http.StatusNotFound, gin.H{"error": "User not found"})
		return
	}
	c.JSON(http.StatusOK, gin.H{"message": "User deleted"})
}
