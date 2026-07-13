#!/usr/bin/env bash
# scripts/smoke.sh — post-deploy health check for the FastAPI backend.
#
# Usage:
#   scripts/smoke.sh http://localhost:8000
#   scripts/smoke.sh                            # defaults to localhost:8000
#
# Hits /healthz and a representative subset of the public + auth routes.
# Exits 0 when every check passes, 1 on the first failure.
set -euo pipefail

BASE="${1:-http://localhost:8000}"

fail() {
  echo "  FAIL: $1" >&2
  exit 1
}

step() {
  printf "%-32s " "$1"
}

check_status() {
  local expected="$1"; shift
  local url="$1"; shift
  local actual
  actual=$(curl -s -o /dev/null -w "%{http_code}" "$url")
  if [[ "$actual" != "$expected" ]]; then
    echo "FAIL (expected $expected, got $actual for $url)"
    exit 1
  fi
  echo "OK ($actual)"
}

echo "Smoke-testing $BASE"

step "healthz 200"
check_status 200 "$BASE/healthz"

step "/metrics 200 (Prometheus exposition)"
check_status 200 "$BASE/metrics"

step "openapi.json 200"
check_status 200 "$BASE/openapi.json"

step "/api/search 200 (empty catalog)"
check_status 200 "$BASE/api/search"

step "/api/song/9999 404"
check_status 404 "$BASE/api/song/9999"

step "/api/stats 200"
check_status 200 "$BASE/api/stats"

step "/api/timeline 200"
check_status 200 "$BASE/api/timeline"

step "/api/word-cloud 200"
check_status 200 "$BASE/api/word-cloud"

step "/api/admin/users 401 (no auth)"
check_status 401 "$BASE/api/admin/users"

step "/api/auth/login 422 (empty POST body)"
actual=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H 'Content-Type: application/json' \
    -d '{}' "$BASE/api/auth/login")
if [[ "$actual" != "422" ]]; then
  echo "FAIL (expected 422, got $actual)"
  exit 1
fi
echo "OK ($actual)"

step "/api/auth/google/start 302 (or 500 when env unset)"
actual=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/api/auth/google/start")
if [[ "$actual" != "302" && "$actual" != "500" ]]; then
  echo "FAIL (expected 302/500, got $actual)"
  exit 1
fi
echo "OK ($actual)"

echo
echo "All smoke checks passed."
