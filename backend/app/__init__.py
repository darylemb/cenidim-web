"""CENIDIM Archivo Musical API — FastAPI backend.

This package contains the FastAPI application factory, SQLAlchemy
models, Pydantic schemas, security helpers and FastAPI routers that
together replace the original Go (Gin) backend.

Layout:
  app/
    main.py            — create_app() factory
    config.py          — pydantic-settings base
    deps.py            — FastAPI dependencies (auth, db, current_user)
    db/                — SQLAlchemy 2.0 engine + session + base
    models/            — SQLAlchemy ORM models
    schemas/           — Pydantic v2 request/response DTOs
    security/          — JWT, password hashing, CSRF, rate limit
    services/          — business logic (auth, email, lyrics, search, audit)
    routers/           — FastAPI APIRouter modules (one per resource)
    cli/build_db.py    — seed CLI equivalent of cmd/build-db
    migrations/        — Alembic env + versions (placeholder)
"""
__version__ = "1.0.0"
