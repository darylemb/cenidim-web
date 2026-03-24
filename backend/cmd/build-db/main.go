package main

import (
	"database/sql"
	"flag"
	"log"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/PuerkitoBio/goquery"
	"golang.org/x/text/runes"
	"golang.org/x/text/transform"
	"golang.org/x/text/unicode/norm"
	"unicode"
	_ "modernc.org/sqlite"
)

var articles = []string{"el ", "la ", "los ", "las ", "un ", "una ", "unos ", "unas "}

func normalize(s string) string {
	// Remove content in parentheses (metadata)
	s = regexp.MustCompile(`\s*\(.*?\)`).ReplaceAllString(s, "")
	// Remove content in brackets
	s = regexp.MustCompile(`\s*\[.*?\]`).ReplaceAllString(s, "")
	
	s = strings.ToLower(s)
	// Remove diacritics
	t := transform.Chain(norm.NFD, runes.Remove(runes.In(unicode.Mn)), norm.NFC)
	s, _, _ = transform.String(t, s)
	
	// Remove articles
	for _, a := range articles {
		s = strings.TrimPrefix(s, a)
		s = strings.ReplaceAll(s, " "+a, " ")
	}
	
	// Remove non-alphanumeric
	s = regexp.MustCompile(`[^\w\s]`).ReplaceAllString(s, "")
	return strings.TrimSpace(regexp.MustCompile(`\s+`).ReplaceAllString(s, " "))
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
				d[i][j] = min(d[i-1][j]+1, min(d[i][j-1]+1, d[i-1][j-1]+1))
			}
		}
	}

	return d[len(s)][len(t)]
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func main() {
	// Paths relative to the project root
	htmlPath := flag.String("html", "../datos.html", "Path to the datos.html file")
	dbPath := flag.String("db", "letras.db", "Path to the SQLite database file")
	flag.Parse()

	log.Printf("🚀 Parsing %s and building database at %s...", *htmlPath, *dbPath)

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

	// Create tables
	_, err = db.Exec(`
		CREATE TABLE albums (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT UNIQUE NOT NULL,
			year TEXT,
			performer TEXT
		);
		CREATE TABLE songs (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			album_id INTEGER,
			title TEXT NOT NULL,
			filename TEXT,
			lyrics TEXT,
			FOREIGN KEY (album_id) REFERENCES albums(id)
		);
	`)
	if err != nil {
		log.Fatalf("❌ Failed to create tables: %v", err)
	}

	file, err := os.Open(*htmlPath)
	if err != nil {
		log.Fatalf("❌ Failed to open HTML file: %v", err)
	}
	defer file.Close()

	doc, err := goquery.NewDocumentFromReader(file)
	if err != nil {
		log.Fatalf("❌ Failed to parse HTML: %v", err)
	}

	letrasRoot := filepath.Dir(*htmlPath)

	// Start transaction
	tx, err := db.Begin()
	if err != nil {
		log.Fatalf("❌ Failed to start transaction: %v", err)
	}

	albumCount := 0
	songCount := 0

	// Regex to extract path from showTrack('./path/to/file.txt')
	re := regexp.MustCompile(`showTrack\(['"](.+)['"]\)`)

	doc.Find("#myTable tbody tr").Each(func(i int, s *goquery.Selection) {
		tds := s.Find("td")
		if tds.Length() < 5 {
			return
		}

		// Table columns: 0:ClavedeFonograma, 1:Año, 2:Intérprete principal, 3:Titulo (Album), 4:Pistas
		year := strings.TrimSpace(tds.Eq(1).Text())
		performer := strings.TrimSpace(tds.Eq(2).Text())
		albumName := strings.TrimSpace(tds.Eq(3).Text())

		if albumName == "" {
			return
		}

		// Insert album
		_, err := tx.Exec("INSERT OR IGNORE INTO albums (name, year, performer) VALUES (?, ?, ?)", albumName, year, performer)
		if err != nil {
			log.Printf("⚠️ Error inserting album %s: %v", albumName, err)
			return
		}

		var albumID int64
		err = tx.QueryRow("SELECT id FROM albums WHERE name = ?", albumName).Scan(&albumID)
		if err != nil {
			log.Printf("⚠️ Error getting ID for album %s: %v", albumName, err)
			return
		}
		albumCount++

		// Process tracks in the last column
		pistasTd := tds.Eq(4)
		
		// Each track is typically followed by a <br>
		// We can look for buttons or just text
		pistasTd.Contents().Each(func(j int, node *goquery.Selection) {
			var trackTitle string
			var lyricsPath string

			if node.Is("button") {
				trackTitle = strings.TrimSpace(node.Text())
				onclick, _ := node.Attr("onclick")
				match := re.FindStringSubmatch(onclick)
				if len(match) > 1 {
					lyricsPath = match[1]
				}
			} else if goquery.NodeName(node) == "#text" {
				trackTitle = strings.TrimSpace(node.Text())
			}

			if trackTitle == "" {
				return
			}

			var lyrics string
			var filename string
			
			// Resolve lyrics path
			actualLyricsPath := ""
			if lyricsPath != "" {
				actualLyricsPath = filepath.Join(letrasRoot, lyricsPath)
				if _, err := os.Stat(actualLyricsPath); err != nil {
					actualLyricsPath = "" // Link might be broken
				}
			}
			
			// If still no path, try fuzzy finding
			if actualLyricsPath == "" {
				found, _ := findLyricsFile(filepath.Join(letrasRoot, "LetrasTXT"), trackTitle)
				if found != "" {
					actualLyricsPath = found
					log.Printf("🔍 Fuzzy matched: '%s' -> %s", trackTitle, found)
				}
			}

			if actualLyricsPath != "" {
				content, err := os.ReadFile(actualLyricsPath)
				if err != nil {
					log.Printf("⚠️ Error reading lyrics for %s at %s: %v", trackTitle, actualLyricsPath, err)
				} else {
					lyrics = string(content)
					filename = filepath.Base(actualLyricsPath)
					
					// Clean up title if it's the first line
					lines := strings.SplitN(lyrics, "\n", 2)
					if len(lines) > 0 {
						firstLine := strings.TrimSpace(lines[0])
						if normalize(firstLine) == normalize(trackTitle) {
							if len(lines) > 1 {
								lyrics = strings.TrimSpace(lines[1])
							} else {
								lyrics = ""
							}
						}
					}
				}
			}

			_, err = tx.Exec(`
				INSERT INTO songs (album_id, title, filename, lyrics)
				VALUES (?, ?, ?, ?)
			`, albumID, trackTitle, filename, strings.TrimSpace(lyrics))
			if err != nil {
				log.Printf("⚠️ Error inserting song %s: %v", trackTitle, err)
				return
			}
			songCount++
		})
	})

	if err := tx.Commit(); err != nil {
		log.Fatalf("❌ Failed to commit transaction: %v", err)
	}

	log.Printf("✅ Database built successfully in '%s'!", *dbPath)
	log.Printf("📊 Summary: %d Albums and %d Songs inserted.", albumCount, songCount)
}
