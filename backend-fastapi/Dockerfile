# syntax=docker/dockerfile:1.4
# Multi-stage FastAPI image (uv-managed deps, non-root runtime).
#
# The ``letras.db`` itself is NOT built here: the ``db-init`` sidecar
# (docker/db-init.Dockerfile, Python+spaCy) produces it and it is
# bind/named-mounted into /data. This image only runs the API and
# applies Alembic migrations on boot.

# ── Stage 1: Install Python deps with uv (FastAPI runtime) ──────────
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


# ── Stage 2: Final runtime ──────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Non-root for parity with the retired Go image.
RUN groupadd --system app && useradd --system --gid app --no-create-home app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=deps /app/.venv ./.venv
COPY backend-fastapi/app ./app
# Alembic config + migration scripts. The runtime image runs
# ``alembic upgrade head`` before uvicorn so the db-init-produced
# ``letras.db`` (base schema from scripts/build_db.py) gets the
# FastAPI columns before the API serves requests.
COPY backend-fastapi/alembic.ini ./alembic.ini
COPY backend-fastapi/alembic ./alembic

EXPOSE 8000

# The CMD honours $CENIDIM_WORKERS (default 2); Coolify / k8s override.
#
# The entrypoint script does the chown + alembic as root (the
# letras.db volume is created by the root-only db-init container)
# and then drops to the non-root \`app\` user via
# \`setpriv\` for the uvicorn process.
COPY backend-fastapi/scripts/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD []
