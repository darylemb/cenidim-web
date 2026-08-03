# syntax=docker/dockerfile:1.4
# Dockerfile.init — sidecar that regenerates letras.db from source
# on every container start.
#
# Single stage: Python + spaCy + bcrypt. The db build, the spaCy
# classifier and the lyric/theme normalization are all Python scripts
# under scripts/ (build_db.py, classify_songs.py, normalize_db.py), so
# no Go toolchain is needed (the Go db-builder was ported to Python).

FROM python:3.12-slim

WORKDIR /app

# Single apt call for the system's only CLI tool we actually need
# (ca-certificates for HTTPS). We deliberately do NOT install
# sqlite3 — pulling a second apt layer after the heavy pip install
# below would risk running out of /var/cache/apt space.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# spaCy + Spanish model + bcrypt (for the admin password hash).
# We install the model wheel directly via pip instead of
# `python -m spacy download` because the latter silently fails to
# copy the model files into site-packages in some Docker/network
# environments (spaCy 3.8.x). --no-cache-dir keeps pip's cache from
# growing; the final `find` scrubs any leftover __pycache__.
RUN pip install --no-cache-dir click spacy bcrypt \
    && pip install --no-cache-dir https://github.com/explosion/spacy-models/releases/download/es_core_news_md-3.8.0/es_core_news_md-3.8.0-py3-none-any.whl \
    && find / -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

# Source tree: scripts (build_db.py, classify_songs.py, normalize_db.py),
# lyrics corpus, CSV. Mounted as RO in compose for the actual source
# files but baked into the image here so the very first
# `docker compose up` works even before the bind mount is attached.
COPY scripts/ ./scripts/
COPY LetrasTXT/ ./LetrasTXT/
COPY db_fonografia.csv ./db_fonografia.csv

# normalize_db.py loads canonical_tema from the FastAPI tree via a bare
# importlib load (it must not import the SQLAlchemy package); ship just
# that one file so the same path resolves inside the container.
COPY backend-fastapi/app/models/theme_normalization.py \
    ./backend-fastapi/app/models/theme_normalization.py

# Entrypoint script: re-runs the build + classify + normalize steps
# every time the container starts so a `docker compose up` against an
# already-built image still produces a fresh DB.
COPY backend/db-init-entrypoint.sh /app/db-init-entrypoint.sh
RUN chmod +x /app/db-init-entrypoint.sh \
    && mkdir -p /data

ARG ADMIN_PASS=admin123
ENV ADMIN_PASS=${ADMIN_PASS} \
    DB_PATH=/data/letras.db

CMD ["/app/db-init-entrypoint.sh"]
