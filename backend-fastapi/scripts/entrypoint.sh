#!/bin/sh
# entrypoint for the FastAPI container.
# Runs as root (the image's USER directive is the `app` user, but
# the compose override executes this entrypoint directly which
# inherits root from the docker exec).
set -eu

# letras.db is created by the Go db-init container as root. The
# FastAPI runtime runs as the non-root `app` user, so we chown the
# file *and* its parent directory so SQLite's WAL journal can be
# created (SQLite needs write access to the directory, not just the
# file). Without this the dev startup's engine.begin() fails with
# `attempt to write a readonly database`.
chown -R app:app /data 2>/dev/null || true
chmod -R u+rwX /data 2>/dev/null || true

# Idempotent migration: continue even if it fails so /healthz can
# still diagnose the rest of the boot.
.venv/bin/alembic upgrade head || true

# Run uvicorn as the `app` user. We can't use `su` (no password)
# so we use `setpriv` (provided by util-linux) or just exec
# under a subshell that drops to app.
if [ "$(id -u)" = "0" ]; then
    # Drop to app user via setpriv, then exec uvicorn.
    exec setpriv --reuid="$(id -u app)" --regid="$(id -g app)" -- \
        .venv/bin/uvicorn app.main:app \
        --host 0.0.0.0 --port 8000 \
        --workers ${CENIDIM_WORKERS:-2}
else
    # Already non-root (e.g. local dev with `docker run --user 1000`).
    exec .venv/bin/uvicorn app.main:app \
        --host 0.0.0.0 --port 8000 \
        --workers ${CENIDIM_WORKERS:-2}
fi
