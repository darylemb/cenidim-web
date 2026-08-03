#!/bin/bash
set -e

DB_NAME="letras.db"
DB_TMP="${DB_NAME}.tmp.$$"
DB_FINAL="${DB_NAME}"

cleanup() {
  rm -f "${DB_TMP}"
}
trap cleanup EXIT

echo "Building database from db_fonografia.csv using Go..."

cd backend
if [ -n "${ADMIN_PASS}" ]; then
  go run cmd/build-db/main.go \
    -csv ../db_fonografia.csv \
    -db "${DB_TMP}" \
    -letras ../LetrasTXT \
    -admin-pass "${ADMIN_PASS}"
else
  go run cmd/build-db/main.go \
    -csv ../db_fonografia.csv \
    -db "${DB_TMP}" \
    -letras ../LetrasTXT
fi
cd ..

echo "Classifying songs with spaCy..."
if ! python3 scripts/classify_songs.py --db "${DB_TMP}"; then
  echo "Error: Classification failed. Database not updated."
  exit 1
fi

echo "Normalizing lyrics + themes (normalize_db.py)..."
if ! python3 scripts/normalize_db.py --db "${DB_TMP}" --fix-lyrics-match --letras-dir LetrasTXT; then
  echo "Error: Normalization failed. Database not updated."
  exit 1
fi

if [ -f "${DB_FINAL}" ]; then
  rm -f "${DB_FINAL}.bak"
  cp "${DB_FINAL}" "${DB_FINAL}.bak"
fi

mv "${DB_TMP}" "${DB_FINAL}"

echo "Done."