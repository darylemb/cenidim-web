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

max_wait=30
count=0
while [ $count -lt $max_wait ]; do
  if curl -sf http://localhost:8000/health 2>/dev/null; then
    echo "Health check passed"
    break
  fi
  count=$((count+1))
  sleep 1
done

if [ $count -eq $max_wait ]; then
  echo "FAIL: health check timed out after ${max_wait}s"
  docker compose logs
  docker compose down
  exit 1
fi

docker compose down

echo "=== All checks passed ==="