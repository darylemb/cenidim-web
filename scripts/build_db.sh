#!/bin/bash
set -e

# Run the database builder from the backend directory
echo "Building database from db_fonografia.csv using Go..."
cd backend && go run cmd/build-db/main.go \
  -csv ../db_fonografia.csv \
  -db ../letras.db \
  -letras ../LetrasTXT \
  ${ADMIN_PASS:+-admin-pass "$ADMIN_PASS"}
cd ..

echo "Classifying songs with spaCy..."
python3 scripts/classify_songs.py --db letras.db

echo "Done."
