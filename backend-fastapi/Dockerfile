# syntax=docker/dockerfile:1.4
# ── Stage 1: Build letras.db (same as the Go Dockerfile) ──────────────
FROM golang:alpine AS db-builder

WORKDIR /app

RUN apk add --no-cache git

COPY backend/go.mod backend/go.sum ./backend/
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    cd /app/backend && go mod download

COPY backend/ ./backend/
COPY LetrasTXT/ ./LetrasTXT/
COPY db_fonografia.csv ./db_fonografia.csv

WORKDIR /app/backend
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux go build -o /app/db-builder ./cmd/build-db/

WORKDIR /app
ARG ADMIN_PASS=${ADMIN_PASS:-admin123}
RUN ./db-builder -csv db_fonografia.csv -db letras.db -letras LetrasTXT -admin-pass "${ADMIN_PASS}"


# ── Stage 2: spaCy classifier (writes song_stats rows) ──────────────
FROM python:3.12-slim AS classifier

WORKDIR /app

RUN pip install --no-cache-dir click spacy && \
    python -m spacy download es_core_news_md

COPY --from=db-builder /app/letras.db ./letras.db
COPY scripts/ ./scripts/

RUN python scripts/classify_songs.py --db letras.db


# ── Stage 3: Install Python deps with uv (FastAPI runtime) ──────────
FROM python:3.12-slim AS deps

WORKDIR /app

# uv ships as a static binary; installing it via the official image
# keeps the final layer small.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

COPY backend-fastapi/pyproject.toml backend-fastapi/uv.lock ./

# --no-dev keeps the runtime image lean (no pytest, ruff, etc.).
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen


# ── Stage 4: Final runtime ──────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Non-root for parity with the distroless Go image.
RUN groupadd --system app && useradd --system --gid app --no-create-home app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=deps /app/.venv ./.venv
COPY backend-fastapi/app ./app
# Alembic config + migration scripts. The runtime image runs
# ``alembic upgrade head`` before uvicorn so the Go-seeded
# ``letras.db`` (which lacks autor / compositor / duracion / personajes /
# temas_raw / editora / last_sign_in_*) gets the FastAPI columns
# before the API serves requests.
COPY backend-fastapi/alembic.ini ./alembic.ini
COPY backend-fastapi/alembic ./alembic

EXPOSE 8000

# The CMD honours $CENIDIM_WORKERS (default 2); Coolify / k8s override.
#
# The entrypoint script does the chown + alembic as root (the
# letras.db volume is created by the root-only Go db-init
# container) and then drops to the non-root \`app\` user via
# \`setpriv\` for the uvicorn process.
COPY backend-fastapi/scripts/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD []
