#!/bin/bash
set -e

# Run the database builder from the backend directory
echo "Building database using Go..."
cd backend && go run cmd/build-db/main.go -html ../datos.html -db ../letras.db
echo "Done."
