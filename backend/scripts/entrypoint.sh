#!/bin/sh
# entrypoint for the FastAPI container.
set -eu

# The compose bind-mounts ./data into /data. The
# db-init container runs as root and creates /data/letras.db owned by
# root:root. The FastAPI image runs the `app` user, which needs write
# access to BOTH the file (for the SQLite db itself) AND the parent
# directory (for the WAL journal `-wal` and `-shm` files).
#
# On CI the chown to `app:app` fails silently because the host user
# namespace doesn't have a matching UID, so the chown call returns
# EPERM. We work around this by chmod'ing the directory to 0777
# (world-writable) which lets the `app` user create the journal
# files regardless of who owns the directory.
chmod 0777 /data 2>/dev/null || true
chmod 0666 /data/letras.db 2>/dev/null || true

# Pre-switch the DB to WAL while still single-processed: switching the
# journal mode needs a momentary exclusive lock and journal-mode
# PRAGMAs can bypass SQLite's busy handler, so two uvicorn workers
# racing on a freshly-built DB crash with "database is locked" on
# first boot (recovering only via the container restart policy). WAL
# mode is persistent in the file, so the workers' own PRAGMA becomes
# a no-op afterwards.
if [ -f "${CENIDIM_DB_PATH:-/data/letras.db}" ]; then
    .venv/bin/python -c "import sqlite3; c = sqlite3.connect('${CENIDIM_DB_PATH:-/data/letras.db}'); c.execute('PRAGMA journal_mode=WAL'); c.close()" || true
fi

# Idempotent migration: no-op if alembic is already at head.
.venv/bin/alembic upgrade head || true

# Drop to the non-root `app` user via setpriv, then exec uvicorn.
if [ "$(id -u)" = "0" ]; then
    exec setpriv --reuid="$(id -u app)" --regid="$(id -g app)" --clear-groups -- \
        .venv/bin/uvicorn app.main:app \
        --host 0.0.0.0 --port 8000 \
        --workers ${CENIDIM_WORKERS:-2}
else
    exec .venv/bin/uvicorn app.main:app \
        --host 0.0.0.0 --port 8000 \
        --workers ${CENIDIM_WORKERS:-2}
fi
