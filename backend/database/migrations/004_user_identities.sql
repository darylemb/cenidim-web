-- 004_user_identities.sql
-- Adds the user_identities table for OAuth provider links and two new audit columns
-- on the users table. Idempotent: re-running is safe; the migration loader guards
-- each ALTER TABLE with PRAGMA table_info.

ALTER TABLE users ADD COLUMN last_sign_in_method TEXT;
ALTER TABLE users ADD COLUMN last_sign_in_at    TEXT;

CREATE TABLE IF NOT EXISTS user_identities (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    provider        TEXT    NOT NULL,
    subject         TEXT    NOT NULL,
    email_at_link   TEXT    NOT NULL,
    linked_at       TEXT    NOT NULL,
    UNIQUE (provider, subject),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_identities_user_id
    ON user_identities(user_id);
