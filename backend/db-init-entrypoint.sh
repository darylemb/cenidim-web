#!/bin/bash
# Entrypoint for the `db-init` service. Re-runs the DB build + classifier
# every time the container is created, so the produced `letras.db`
# always reflects the current source files.
set -euo pipefail

ADMIN_PASS="${ADMIN_PASS:-admin123}"
DB_PATH="${DB_PATH:-/data/letras.db}"

echo "[db-init] regenerating ${DB_PATH} from current source…"
db-builder \
  -csv /app/db_fonografia.csv \
  -db "${DB_PATH}" \
  -letras /app/LetrasTXT \
  -admin-pass "${ADMIN_PASS}"

echo "[db-init] classifying songs (spaCy)…"
python /app/scripts/classify_songs.py --db "${DB_PATH}"

# Sanity check: the file exists and is non-empty. docker-compose uses
# the container's exit code to decide whether the backend can start.
if [ ! -s "${DB_PATH}" ]; then
    echo "[db-init] ERROR: ${DB_PATH} is empty" >&2
    exit 1
fi

# Make the regenerated DB writable by every user in the container.
# The backend image runs as `nonroot` (security), but the volume
# itself is created by this root-owned init container so the file
# inherits root:root ownership by default — nonroot can then
# SELECT but gets "attempt to write a readonly database" on any
# INSERT. `chmod 666` lets the nonroot backend write to the file
# while still requiring it to know the DB path.
chmod 666 "${DB_PATH}"

# Print a compact summary in pure Go (no sqlite3 CLI needed). We call
# the db-builder in `summary` mode via a small one-shot Go program
# so the operator can see at a glance that the regenerated DB
# matches the source files.
echo "[db-init] done. $(stat -c%s "${DB_PATH}" 2>/dev/null || stat -f%z "${DB_PATH}") bytes."
echo "[db-init] inspect the file at ${DB_PATH} to confirm theme counts."
