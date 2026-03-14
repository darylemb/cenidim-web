package main

import (
	"bufio"
	"database/sql"
	"flag"
	"log"
	"os"
	"path/filepath"
	"strings"

	_ "modernc.org/sqlite"
)

func main() {
	// Paths relative to the project root
	baseDir := flag.String("dir", "LetrasTXT", "Directory containing the albums")
	dbPath := flag.String("db", "letras.db", "Path to the SQLite database file")
	flag.Parse()

	log.Printf("🚀 Creating SQLite database at %s and building tables...", *dbPath)

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
			name TEXT UNIQUE NOT NULL
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

	log.Println("📂 Processing files...")

	// Start transaction for efficiency
	tx, err := db.Begin()
	if err != nil {
		log.Fatalf("❌ Failed to start transaction: %v", err)
	}

	albums, err := os.ReadDir(*baseDir)
	if err != nil {
		log.Fatalf("❌ Failed to read base directory %s: %v", *baseDir, err)
	}

	albumCount := 0
	songCount := 0

	for _, albumEntry := range albums {
		if !albumEntry.IsDir() {
			continue
		}

		albumName := albumEntry.Name()
		albumPath := filepath.Join(*baseDir, albumName)

		// Insert album
		_, err := tx.Exec("INSERT OR IGNORE INTO albums (name) VALUES (?)", albumName)
		if err != nil {
			log.Printf("⚠️ Error inserting album %s: %v", albumName, err)
			continue
		}

		var albumID int64
		err = tx.QueryRow("SELECT id FROM albums WHERE name = ?", albumName).Scan(&albumID)
		if err != nil {
			log.Printf("⚠️ Error getting ID for album %s: %v", albumName, err)
			continue
		}
		albumCount++

		songs, err := os.ReadDir(albumPath)
		if err != nil {
			log.Printf("⚠️ Error reading album directory %s: %v", albumName, err)
			continue
		}

		for _, songEntry := range songs {
			if songEntry.IsDir() || !strings.HasSuffix(songEntry.Name(), ".txt") {
				continue
			}

			songFilename := songEntry.Name()
			songPath := filepath.Join(albumPath, songFilename)

			file, err := os.Open(songPath)
			if err != nil {
				log.Printf("⚠️ Error opening song file %s: %v", songFilename, err)
				continue
			}

			scanner := bufio.NewScanner(file)
			var title string
			var lyricsBuilder strings.Builder

			firstLine := true
			for scanner.Scan() {
				line := scanner.Text()
				if firstLine {
					title = strings.TrimSpace(line)
					firstLine = false
				} else {
					lyricsBuilder.WriteString(line)
					lyricsBuilder.WriteString("\n")
				}
			}
			_ = file.Close()

			if title == "" {
				continue
			}

			_, err = tx.Exec(`
				INSERT INTO songs (album_id, title, filename, lyrics)
				VALUES (?, ?, ?, ?)
			`, albumID, title, songFilename, strings.TrimSpace(lyricsBuilder.String()))
			if err != nil {
				log.Printf("⚠️ Error inserting song %s: %v", songFilename, err)
				continue
			}
			songCount++
		}
	}

	if err := tx.Commit(); err != nil {
		log.Fatalf("❌ Failed to commit transaction: %v", err)
	}

	log.Printf("✅ Database built successfully in '%s'!", *dbPath)
	log.Printf("📊 Summary: %d Albums and %d Songs inserted.", albumCount, songCount)
}
