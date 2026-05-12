#!/bin/bash
set -e

# Run the database builder from the backend directory
echo "Building database from db_fonografia.csv using Go..."
args=(
  -csv ../db_fonografia.csv
  -db ../letras.db
  -letras ../LetrasTXT
)

if [ -n "${ADMIN_PASS}" ]; then
  args+=(-admin-pass "${ADMIN_PASS}")
fi

cd backend
go run cmd/build-db/main.go "${args[@]}"
cd ..

echo "Classifying songs with spaCy..."
python3 scripts/classify_songs.py --db letras.db

echo "Done."
