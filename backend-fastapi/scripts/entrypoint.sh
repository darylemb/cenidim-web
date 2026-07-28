#!/bin/sh
# entrypoint for the FastAPI container.
set -eu

# The compose overlay bind-mounts ./backend/data into /data. The
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
