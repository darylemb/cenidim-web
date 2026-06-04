package database

import (
	"database/sql"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	_ "modernc.org/sqlite"
)

var DB *sql.DB

// InitDB configures SQLite with proper connection pool settings and retry logic
func InitDB() error {
	dbPath := os.Getenv("DB_PATH")
	if dbPath == "" {
		dbPath = "letras.db"
	}

	var err error
	DB, err = sql.Open("sqlite", dbPath+"?_busy_timeout=30000&_journal_mode=WAL&_synchronous=NORMAL")
	if err != nil {
		return fmt.Errorf("error opening database: %w", err)
	}

	// SQLite: only one writer at a time, limit connections accordingly
	DB.SetMaxOpenConns(1)
	DB.SetMaxIdleConns(1)
	DB.SetConnMaxLifetime(time.Hour)

	if err = DB.Ping(); err != nil {
		return fmt.Errorf("error connecting to database: %w", err)
	}

	log.Println("Connected to SQLite database successfully")
	return nil
}

// ExecWithRetry executes a query with automatic retry on SQLITE_BUSY / "database is locked" errors
func ExecWithRetry(query string, args ...interface{}) (sql.Result, error) {
	const maxRetries = 3
	const retryDelay = 100 * time.Millisecond

	var res sql.Result
	var err error
	for i := 0; i < maxRetries; i++ {
		res, err = DB.Exec(query, args...)
		if err == nil {
			return res, nil
		}
		// Check if it's a "database is locked" or "busy" error
		if !isLockedError(err) {
			return res, err
		}
		if i < maxRetries-1 {
			time.Sleep(retryDelay * time.Duration(i+1))
		}
	}
	return res, err
}

// QueryRowWithRetry executes a query that returns a single row with retry on locked errors
func QueryRowWithRetry(query string, args ...interface{}) *sql.Row {
	return DB.QueryRow(query, args...)
}

// BeginTxWithRetry starts a transaction with retry logic for locked errors
func BeginTxWithRetry() (*sql.Tx, error) {
	const maxRetries = 3
	const retryDelay = 100 * time.Millisecond

	var tx *sql.Tx
	var err error
	for i := 0; i < maxRetries; i++ {
		tx, err = DB.Begin()
		if err == nil {
			return tx, nil
		}
		if !isLockedError(err) {
			return nil, err
		}
		if i < maxRetries-1 {
			time.Sleep(retryDelay * time.Duration(i+1))
		}
	}
	return nil, err
}

// isLockedError checks if the error is a SQLite "database is locked" or "busy" error
func isLockedError(err error) bool {
	if err == nil {
		return false
	}
	errStr := err.Error()
	return strings.Contains(errStr, "database is locked") ||
		strings.Contains(errStr, "SQLITE_BUSY") ||
		strings.Contains(errStr, "SQLITE_LOCKED")
}
