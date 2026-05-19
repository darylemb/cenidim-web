#!/bin/bash
set -e

echo "=== Backend lint + tests ==="
cd backend
go mod download
golangci-lint run
go test -v ./...
cd ..

echo "=== Frontend typecheck + lint ==="
cd frontend
npm ci
npm run lint
npm run build
npm run test -- --run
cd ..

echo "=== Docker build + health check ==="
docker compose build
docker compose up -d
sleep 5
curl -sf http://localhost:8000/health || {
  echo "FAIL: health check"
  docker compose down
  exit 1
}
docker compose down

echo "=== All checks passed ==="