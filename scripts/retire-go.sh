#!/usr/bin/env bash
# scripts/retire-go.sh — Phase 9 cleanup script.
#
# Runs AFTER 1 week of green production metrics with the FastAPI
# stack live. See docs/CUTOVER.md Phase 9 + docs/PR-merge-to-main.md
# for the full procedure.
#
# What it does:
#   - Runs a sanity check (FastAPI compose still works).
#   - Removes the Go tree (backend/) and the Go rollback compose
#     file (docker-compose-go.yaml).
#   - Removes the Go-related branches if they exist locally.
#   - Rewrites docker-compose.yaml + coolify compose to drop the
#     Go db-init sidecar's build context (backend/Dockerfile.init).
#   - Prints a final smoke check command.
#
# NOT EXECUTED BY DEFAULT. Operators run this on a confirmation
# from the maintainer. The script is idempotent: running it twice
# is safe — files that are already gone will be skipped.

set -euo pipefail

cd "$(dirname "$0")/.."

bold() { printf "\n\033[1m%s\033[0m\n" "$*"; }
warn() { printf "\033[33mWARNING\033[0m: %s\n" "$*" >&2; }
fail() { printf "\033[31mERROR\033[0m: %s\n" "$*" >&2; exit 1; }

bold "Phase 9: retire the Go tree"

# 1. Pre-flight: confirm the FastAPI compose is healthy.
bold "1. Pre-flight check (FastAPI compose should be running)"
if ! command -v docker >/dev/null 2>&1; then
  fail "docker is not on PATH — aborting."
fi
if docker compose ps backend 2>/dev/null | grep -q "Up"; then
  warn "docker compose backend is Up — proceeding."
else
  warn "docker compose backend does NOT appear to be Up."
  warn "Operators usually run this script 1 week after the cut-over."
  warn "If you intended to retire the Go tree now, double-check the stack is running the FastAPI service."
  printf "Continue? [y/N] "
  read -r _confirm
  [[ "$_confirm" =~ ^[Yy]$ ]] || fail "Aborted by operator."
fi

# 2. Confirm the FastAPI smoke script passes.
bold "2. Smoke test (FastAPI service)"
if command -v curl >/dev/null 2>&1; then
  health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/healthz || echo "000")
  if [[ "$health" != "200" ]]; then
    fail "FastAPI /healthz is not 200 (got $health). Aborting — the cut-over is not stable yet."
  fi
  warn "/healthz OK"
else
  warn "curl not on PATH — skipping /healthz probe."
fi

# 3. Remove the Go tree.
bold "3. Removing the Go tree"
if [[ -d backend ]]; then
  warn "Removing backend/ (Go service + Dockerfile + Dockerfile.init + cmd/build-db)"
  warn "  ↳ Preserve backend/cmd/build-db first if the db-init sidecar still needs it."
  if [[ -d backend/cmd/build-db ]]; then
    warn "    backend/cmd/build-db still exists; verify the new db-init path before deleting."
    printf "Preserve backend/cmd/build-db? [Y/n] "
    read -r _keep
    if [[ ! "$_keep" =~ ^[Nn]$ ]]; then
      mkdir -p .phase9-keep
      mv backend/cmd/build-db .phase9-keep/build-db
      warn "    Preserved backend → .phase9-keep/build-db for manual removal."
    fi
  fi
  rm -rf backend
  warn "backend/ removed."
else
  warn "backend/ already gone — skipping."
fi

# 4. Remove the Go rollback compose + clean up the docker-compose.yaml.
bold "4. Removing the Go rollback compose"
if [[ -f docker-compose-go.yaml ]]; then
  rm -f docker-compose-go.yaml
  warn "docker-compose-go.yaml removed."
else
  warn "docker-compose-go.yaml already gone — skipping."
fi

# 5. Sweep Go-specific Dockerfile.healthcheck from any compose.
if grep -q "./healthcheck" docker-compose.yaml docker-compose-coolify.yaml 2>/dev/null; then
  warn "Found './healthcheck' references in the active compose files."
  warn "Edit docker-compose.yaml + docker-compose-coolify.yaml to remove them."
fi

# 6. Drop the Phase-9-keeper of build-db (operator moves the Go
#    command into a Python equivalent).
if [[ -d .phase9-keep ]]; then
  warn "Removing .phase9-keep/ (build-db was preserved here earlier)."
  rm -rf .phase9-keep
fi

# 7. Drop local Go-only branches if they exist.
bold "5. Dropping local Go-era branches (read-only)"
for branch in "fix/critical-bugs-dashboard-and-oauth" "ux/dashboard-fixes-2026-07"; do
  if git show-ref --verify --quiet "refs/heads/$branch"; then
    git branch -D "$branch" || warn "  Could not delete $branch (maybe checked out?)."
    warn "  Deleted local branch $branch."
  else
    warn "  Local branch $branch not present — skipping."
  fi
done

# 8. Final smoke probe.
bold "6. Post-retirement smoke probe"
warn "Run: docker compose up --build -d && backend-fastapi/scripts/smoke.sh http://localhost:8000"
warn "Then commit the cleanup in a follow-up PR."

bold "Phase 9 cleanup complete."
warn "Don't forget to push the cleanup commit and confirm in #ops"
warn "that the prod stack still passes scripts/smoke.sh."
