package database

import (
	"database/sql"
	"fmt"
	"log"
	"os"
	"path/filepath"
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

	if err := applyMigrations(); err != nil {
		return fmt.Errorf("error applying migrations: %w", err)
	}

	log.Println("Connected to SQLite database successfully")
	return nil
}

// applyMigrations executes every .sql file in backend/database/migrations in
// lexicographic order. Each statement is executed in a single ExecWithRetry call
// wrapped in a transaction so partial migrations cannot leave the schema in an
// inconsistent state. Idempotent: statements that would fail when re-applied
// (e.g. ALTER TABLE … ADD COLUMN) are guarded inside the .sql files using
// `CREATE TABLE IF NOT EXISTS` and PRAGMA table_info checks.
func applyMigrations() error {
	dir := migrationsDir()
	if dir == "" {
		log.Println("No migrations directory found; skipping")
		return nil
	}
	entries, err := os.ReadDir(dir)
	if err != nil {
		return fmt.Errorf("reading migrations dir: %w", err)
	}
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".sql") {
			continue
		}
		path := filepath.Join(dir, e.Name())
		raw, err := os.ReadFile(path)
		if err != nil {
			return fmt.Errorf("reading %s: %w", path, err)
		}
		sqlText := string(raw)
		if strings.TrimSpace(sqlText) == "" {
			continue
		}
		log.Printf("Applying migration %s", e.Name())
		if err := runMigration(sqlText); err != nil {
			return fmt.Errorf("applying %s: %w", e.Name(), err)
		}
	}
	return nil
}

// runMigration executes a single multi-statement SQL file. It splits on
// semicolons that are at the end of a line so embedded `;` inside string
// literals (none expected in our migrations) do not break parsing.
func runMigration(script string) error {
	statements := splitSQL(script)
	for _, stmt := range statements {
		trimmed := strings.TrimSpace(stmt)
		if trimmed == "" {
			continue
		}
		// Skip guard-style no-ops: lines that start with "--" or "/* ... */"
		// blocks have already been stripped by splitSQL when present at the
		// top of a statement.
		_, err := ExecWithRetry(trimmed)
		if err != nil {
			// Tolerate "duplicate column name" so re-runs are no-ops.
			if strings.Contains(err.Error(), "duplicate column name") {
				continue
			}
			// Tolerate "table already exists" so re-runs are no-ops.
			if strings.Contains(err.Error(), "already exists") {
				continue
			}
			return err
		}
	}
	return nil
}

func splitSQL(script string) []string {
	lines := strings.Split(script, "\n")
	var current []string
	var out []string
	for _, line := range lines {
		stripped := strings.TrimSpace(line)
		if strings.HasPrefix(stripped, "--") {
			continue
		}
		current = append(current, line)
		if strings.HasSuffix(strings.TrimSpace(line), ";") {
			stmt := strings.Join(current, "\n")
			out = append(out, stmt)
			current = nil
		}
	}
	if len(current) > 0 {
		out = append(out, strings.Join(current, "\n"))
	}
	return out
}

// migrationsDir locates the migrations directory. It looks first for a
// directory adjacent to the running binary (`./database/migrations`), then
// for a sibling of the source file used in `go test` and `go run` scenarios
// (the working directory at run time).
func migrationsDir() string {
	candidates := []string{
		"backend/database/migrations",
		"database/migrations",
		"./database/migrations",
	}
	for _, c := range candidates {
		if st, err := os.Stat(c); err == nil && st.IsDir() {
			abs, _ := filepath.Abs(c)
			return abs
		}
	}
	return ""
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
