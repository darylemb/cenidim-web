# syntax=docker/dockerfile:1.4
# ── Stage 1: Build SQLite DB from CSV + lyrics ──────────────────────────────
FROM golang:alpine AS db-builder

WORKDIR /app

RUN apk add --no-cache git

# Copy ONLY the module manifests first so this layer is cacheable
# across builds that don't touch dependencies.
COPY backend/go.mod backend/go.sum ./backend/
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    cd /app/backend && go mod download

# Now copy the rest of the source plus the inputs the db-builder needs
# at runtime (CSV + lyrics corpus).
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


# ── Stage 2: Classify songs with spaCy (Python, Debian slim for wheel support)
FROM python:3.12-slim AS classifier

WORKDIR /app

RUN pip install --no-cache-dir click spacy && \
    python -m spacy download es_core_news_md

COPY --from=db-builder /app/letras.db ./letras.db
COPY scripts/ ./scripts/

RUN python scripts/classify_songs.py --db letras.db


# ── Stage 3: Build Go API binary ─────────────────────────────────────────────
FROM golang:alpine AS api-builder

WORKDIR /app

RUN apk add --no-cache git

# Copy ONLY the module manifests first so this layer is cacheable
# across builds that don't touch dependencies.
COPY backend/go.mod backend/go.sum ./backend/
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    cd /app/backend && go mod download

# Now copy the source and build the binary.
COPY backend/ ./backend/
WORKDIR /app/backend
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    export PATH=$PATH:$(go env GOPATH)/bin && \
    go install github.com/swaggo/swag/cmd/swag@v1.16.6 && \
    swag init -g main.go && \
    CGO_ENABLED=0 GOOS=linux go build -o /app/main ./main.go

# Tiny healthcheck binary (distroless has no curl)
RUN printf 'package main\nimport ("net/http"; "os")\nfunc main() { _, err := http.Get("http://localhost:8080/health"); if err != nil { os.Exit(1) }; os.Exit(0) }\n' > /app/healthcheck.go
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux go build -o /app/healthcheck /app/healthcheck.go


# ── Stage 4: Final (Distroless) ───────────────────────────────────────────────
FROM gcr.io/distroless/static-debian12

WORKDIR /app

COPY --from=api-builder /app/main .
COPY --from=api-builder /app/healthcheck .
COPY --from=api-builder /app/backend/database/migrations ./database/migrations
COPY --from=classifier --chown=nonroot:nonroot /app/letras.db /data/

USER nonroot:nonroot

EXPOSE 8080

CMD ["./main"]
