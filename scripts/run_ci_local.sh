#!/bin/bash
# scripts/run_ci_local.sh — full local CI sequence.
#
# Mirrors the GitHub Actions workflow so we can sanity-check before
# pushing. Order:
#   1. Backend (FastAPI) lint + tests + openapi drift guard.
#   2. Frontend lint + typecheck + tests.
#   3. Docker compose build + boot + smoke check + teardown.
#
# Exits non-zero on the first failure so we can chain it under
# `set -e` in CI.

set -e

echo "=== Backend (FastAPI) lint + tests ==="
cd backend-fastapi
uv sync --frozen
uv run ruff check app/ tests/
PYTHONPATH=. uv run pytest tests/ -q
uv run python scripts/generate_openapi.py
git diff --exit-with-stat -- openapi.json
bash -n scripts/smoke.sh
cd ..

echo "=== Frontend lint + typecheck + tests ==="
cd frontend
npm ci
npm run lint
npm run build
npm run test -- --run
cd ..

echo "=== Docker compose build + smoke check ==="
docker compose build

# Boot the FastAPI stack (default compose after Phase 7).
docker compose up -d

# Wait for /healthz (FastAPI endpoint).
max_wait=45
count=0
while [ $count -lt $max_wait ]; do
  if curl -sf http://localhost:8000/healthz 2>/dev/null; then
    echo "FastAPI /healthz OK"
    break
  fi
  count=$((count+1))
  sleep 1
done

if [ $count -eq $max_wait ]; then
  echo "FAIL: /healthz timed out after ${max_wait}s"
  docker compose logs
  docker compose down
  exit 1
fi

# Run the full smoke script against the live stack.
backend-fastapi/scripts/smoke.sh http://localhost:8000

docker compose down

echo "=== All checks passed ==="