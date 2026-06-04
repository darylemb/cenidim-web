package main

import (
	"database/sql"
	"encoding/csv"
	"flag"
	"io"
	"log"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"unicode"

	"golang.org/x/crypto/bcrypt"
	"golang.org/x/text/runes"
	"golang.org/x/text/transform"
	"golang.org/x/text/unicode/norm"
	_ "modernc.org/sqlite"
)

var articles = []string{"el ", "la ", "los ", "las ", "un ", "una ", "unos ", "unas "}

var (
	parenRe      = regexp.MustCompile(`\s*\(.*?\)`)
	bracketRe    = regexp.MustCompile(`\s*\[.*?\]`)
	nonAlnumRe   = regexp.MustCompile(`[^\w\s]`)
	spaceRe      = regexp.MustCompile(`\s+`)
	trackRe      = regexp.MustCompile(`\d+\.\s+`)
	trailingParen = regexp.MustCompile(`\s*\([^)]*\)\s*$`)
)

func normalize(s string) string {
	s = parenRe.ReplaceAllString(s, "")
	s = bracketRe.ReplaceAllString(s, "")

	s = strings.ToLower(s)
	t := transform.Chain(norm.NFD, runes.Remove(runes.In(unicode.Mn)), norm.NFC)
	s, _, _ = transform.String(t, s)

	for _, a := range articles {
		s = strings.TrimPrefix(s, a)
		s = strings.ReplaceAll(s, " "+a, " ")
	}

	s = nonAlnumRe.ReplaceAllString(s, "")
	return strings.TrimSpace(spaceRe.ReplaceAllString(s, " "))
}

func findLyricsFile(root, targetTitle string) (string, error) {
	normalizedTarget := normalize(targetTitle)
	if len(normalizedTarget) < 3 {
		return "", nil
	}

	var bestMatch string
	bestScore := -1.0

	err := filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() || !strings.HasSuffix(strings.ToLower(path), ".txt") {
			return nil
		}

		base := filepath.Base(path)
		if strings.HasPrefix(base, ".") || base == ".txt" {
			return nil
		}

		filename := strings.TrimSuffix(base, filepath.Ext(path))
		normalizedFile := normalize(filename)
		if len(normalizedFile) < 3 {
			return nil
		}

		score := calculateMatchScore(normalizedTarget, normalizedFile)

		if score > 0.6 && score > bestScore {
			bestScore = score
			bestMatch = path
		}

		return nil
	})

	return bestMatch, err
}

func calculateMatchScore(s1, s2 string) float64 {
	if s1 == s2 {
		return 1.0
	}

	dist := levenshteinDistance(s1, s2)
	maxLen := len(s1)
	if len(s2) > maxLen {
		maxLen = len(s2)
	}

	if maxLen == 0 {
		return 0
	}

	score := 1.0 - float64(dist)/float64(maxLen)

	// Bonus for prefix/substring
	if strings.Contains(s1, s2) || strings.Contains(s2, s1) {
		score += 0.1
	}

	return score
}

func levenshteinDistance(s, t string) int {
	d := make([][]int, len(s)+1)
	for i := range d {
		d[i] = make([]int, len(t)+1)
	}

	for i := 0; i <= len(s); i++ {
		d[i][0] = i
	}
	for j := 0; j <= len(t); j++ {
		d[0][j] = j
	}

	for j := 1; j <= len(t); j++ {
		for i := 1; i <= len(s); i++ {
			if s[i-1] == t[j-1] {
				d[i][j] = d[i-1][j-1]
			} else {
				d[i][j] = minInt(d[i-1][j]+1, minInt(d[i][j-1]+1, d[i-1][j-1]+1))
			}
		}
	}

	return d[len(s)][len(t)]
}

func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// extractSongTitles parses the Pistas column text and returns individual song titles.
// Format example: "Lado 1: 1. Song title (composer), 2. Another song; Lado 2: ..."
func extractSongTitles(pistas string) []string {
	idxPairs := trackRe.FindAllStringIndex(pistas, -1)
	if len(idxPairs) == 0 {
		return nil
	}

	var titles []string
	for i, idx := range idxPairs {
		start := idx[1]
		var raw string
		if i+1 < len(idxPairs) {
			end := idxPairs[i+1][0]
			raw = strings.TrimRight(pistas[start:end], " ,;")
		} else {
			raw = strings.TrimRight(pistas[start:], " ,;")
		}

		raw = trailingParen.ReplaceAllString(raw, "")
		raw = strings.TrimSpace(raw)
		if raw != "" {
			titles = append(titles, raw)
		}
	}
	return titles
}

func loadLyrics(letrasRoot, trackTitle string) (lyrics, filename string) {
	found, _ := findLyricsFile(letrasRoot, trackTitle)
	if found == "" {
		return "", ""
	}
	content, err := os.ReadFile(found)
	if err != nil {
		log.Printf("⚠️ Error reading lyrics for %s: %v", trackTitle, err)
		return "", ""
	}
	lyricsText := string(content)
	filename = filepath.Base(found)
	// Remove first line if it matches the title
	lines := strings.SplitN(lyricsText, "\n", 2)
	if len(lines) > 0 && normalize(strings.TrimSpace(lines[0])) == normalize(trackTitle) {
		if len(lines) > 1 {
			lyricsText = strings.TrimSpace(lines[1])
		} else {
			lyricsText = ""
		}
	}
	return strings.TrimSpace(lyricsText), filename
}

func main() {
	csvPath := flag.String("csv", "../db_fonografia.csv", "Path to db_fonografia.csv")
	dbPath := flag.String("db", "letras.db", "Path to the SQLite database file")
	letrasDir := flag.String("letras", "../LetrasTXT", "Path to LetrasTXT directory")
	adminPass := flag.String("admin-pass", "", "Initial admin user password (required)")
	flag.Parse()

	if *adminPass == "" {
		log.Fatal("❌ --admin-pass is required")
	}

	log.Printf("🚀 Parsing %s and building database at %s...", *csvPath, *dbPath)

	// Remove existing DB
	if _, err := os.Stat(*dbPath); err == nil {
		if err := os.Remove(*dbPath); err != nil {
			log.Fatalf("❌ Failed to remove existing database: %v", err)
		}
	}

	db, err := sql.Open("sqlite", *dbPath)
	if err != nil {
		log.Fatalf("❌ Failed to open database: %v", err)
	}
	defer func() { _ = db.Close() }()

_, err = db.Exec(`
		CREATE TABLE fonogramas (
			clave_fonograma    INTEGER PRIMARY KEY,
			titulo             TEXT NOT NULL,
			subtitulo          TEXT,
			interprete_principal   TEXT,
			interpretes_invitados  TEXT,
			interprete_participante TEXT,
			soporte_fisico     TEXT,
			editoria            TEXT,
			numero_catalogo    TEXT,
			ciudad_edicion     TEXT,
			pais_edicion       TEXT,
			anio               TEXT,
			pistas             TEXT,
			observaciones      TEXT,
			version            INTEGER DEFAULT 0
		);
		CREATE TABLE songs (
			id             INTEGER PRIMARY KEY AUTOINCREMENT,
			fonograma_id   INTEGER NOT NULL,
			title          TEXT NOT NULL,
			filename       TEXT,
			lyrics         TEXT,
			clasificacion  TEXT,
			tema           TEXT,
			created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
			version        INTEGER DEFAULT 0,
			FOREIGN KEY (fonograma_id) REFERENCES fonogramas(clave_fonograma)
		);
		CREATE TABLE users (
			id            INTEGER PRIMARY KEY AUTOINCREMENT,
			username      TEXT UNIQUE NOT NULL,
			email         TEXT UNIQUE NOT NULL,
			password_hash TEXT NOT NULL,
			role          TEXT NOT NULL DEFAULT 'viewer',
			created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
			version       INTEGER DEFAULT 0
		);
	`)
	if err != nil {
		log.Fatalf("❌ Failed to create tables: %v", err)
	}

	// Open and parse CSV
	csvFile, err := os.Open(*csvPath)
	if err != nil {
		log.Fatalf("❌ Failed to open CSV: %v", err)
	}
	defer func() { _ = csvFile.Close() }()

	reader := csv.NewReader(csvFile)
	reader.LazyQuotes = true
	reader.FieldsPerRecord = -1 // allow variable number of fields

	// Skip header
	if _, headerErr := reader.Read(); headerErr != nil {
		log.Fatalf("❌ Failed to read CSV header: %v", headerErr)
	}

	tx, err := db.Begin()
	if err != nil {
		log.Fatalf("❌ Failed to start transaction: %v", err)
	}

	fonogramaCount := 0
	songCount := 0

	for {
		record, rerr := reader.Read()
		if rerr == io.EOF {
			break
		}
		if rerr != nil {
			log.Printf("⚠️ CSV read error, skipping row: %v", rerr)
			continue
		}

		// Pad record to 14 fields
		for len(record) < 14 {
			record = append(record, "")
		}

		claveStr := strings.TrimSpace(record[0])
		if claveStr == "" {
			continue
		}
		clave, claveErr := strconv.Atoi(claveStr)
		if claveErr != nil {
			log.Printf("⚠️ Non-numeric ClavedeFonograma '%s', skipping", claveStr)
			continue
		}

		titulo := strings.TrimSpace(record[1])
		if titulo == "" {
			continue
		}

		subtitulo := strings.TrimSpace(record[2])
		interpretePrincipal := strings.TrimSpace(record[3])
		interpretesInvitados := strings.TrimSpace(record[4])
		interpreteParticipante := strings.TrimSpace(record[5])
		soporteFisico := strings.TrimSpace(record[6])
		editoria := strings.TrimSpace(record[7])
		numeroCatalogo := strings.TrimSpace(record[8])
		ciudadEdicion := strings.TrimSpace(record[9])
		paisEdicion := strings.TrimSpace(record[10])
		anio := strings.TrimSpace(record[11])
		pistas := strings.TrimSpace(record[12])
		observaciones := strings.TrimSpace(record[13])

		_, err = tx.Exec(`
			INSERT OR REPLACE INTO fonogramas
			(clave_fonograma, titulo, subtitulo, interprete_principal, interpretes_invitados,
			 interprete_participante, soporte_fisico, editoria, numero_catalogo, ciudad_edicion,
			 pais_edicion, anio, pistas, observaciones)
			VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
			clave, titulo, subtitulo, interpretePrincipal, interpretesInvitados,
			interpreteParticipante, soporteFisico, editoria, numeroCatalogo, ciudadEdicion,
			paisEdicion, anio, pistas, observaciones,
		)
		if err != nil {
			log.Printf("⚠️ Error inserting fonograma %d: %v", clave, err)
			continue
		}
		fonogramaCount++

		// Extract individual songs from Pistas and link lyrics
		songTitles := extractSongTitles(pistas)
		for _, trackTitle := range songTitles {
			lyricsText, filename := loadLyrics(*letrasDir, trackTitle)
			if filename != "" {
				log.Printf("🔍 Matched: '%s' -> %s", trackTitle, filename)
			}
			_, err = tx.Exec(`
				INSERT INTO songs (fonograma_id, title, filename, lyrics)
				VALUES (?, ?, ?, ?)`,
				clave, trackTitle, filename, lyricsText,
			)
			if err != nil {
				log.Printf("⚠️ Error inserting song '%s': %v", trackTitle, err)
				continue
			}
			songCount++
		}
	}

	// Create default admin user
	hash, err := bcrypt.GenerateFromPassword([]byte(*adminPass), bcrypt.DefaultCost)
	if err != nil {
		log.Fatalf("❌ Failed to hash admin password: %v", err)
	}
	_, err = tx.Exec(`
		INSERT OR IGNORE INTO users (username, email, password_hash, role)
		VALUES ('admin', 'admin@cenidim.mx', ?, 'admin')`, string(hash))
	if err != nil {
		log.Printf("⚠️ Error creating admin user: %v", err)
	}

	if err := tx.Commit(); err != nil {
		log.Fatalf("❌ Failed to commit transaction: %v", err)
	}

	log.Printf("✅ Database built successfully in '%s'!", *dbPath)
	log.Printf("📊 Summary: %d Fonogramas, %d Songs inserted.", fonogramaCount, songCount)
	log.Printf("👤 Admin user created: admin")
}
