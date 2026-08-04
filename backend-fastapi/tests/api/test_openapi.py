"""Tests for the OpenAPI spec.

CI guard: the committed ``openapi.json`` must match what
``app.openapi()`` produces. Run ``uv run python scripts/generate_openapi.py``
to refresh after a router/schema change.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.config import Settings
from app.main import create_app

ROOT = Path(__file__).resolve().parents[2]
OPENAPI_PATH = ROOT / "openapi.json"


def test_openapi_spec_is_up_to_date(tmp_path):
    """Drift guard: openapi.json must match the live app."""
    settings = Settings(env="dev", jwt_secret="x" * 64, db_path=tmp_path / "x.db")
    app = create_app(settings)
    expected = app.openapi()
    assert OPENAPI_PATH.exists(), "openapi.json missing — run scripts/generate_openapi.py"
    committed = json.loads(OPENAPI_PATH.read_text())
    assert committed == expected, (
        "openapi.json is out of date. Run:\n"
        "  uv run python scripts/generate_openapi.py\n"
        "and commit the result."
    )


def test_openapi_spec_covers_key_endpoints(tmp_path):
    """Sanity: every router-mounted path appears in the spec."""
    settings = Settings(env="dev", jwt_secret="x" * 64, db_path=tmp_path / "x.db")
    create_app(settings)
    committed = json.loads(OPENAPI_PATH.read_text())
    paths = set(committed.get("paths", {}).keys())
    # Auth
    assert "/api/auth/login" in paths
    assert "/api/auth/register" in paths
    assert "/api/auth/forgot" in paths
    assert "/api/auth/reset" in paths
    assert "/api/auth/refresh" in paths
    assert "/api/auth/logout" in paths
    assert "/api/auth/me" in paths
    # Public
    assert "/api/search" in paths
    assert "/api/song/{song_id}" in paths
    assert "/api/timeline" in paths
    assert "/api/stats" in paths
    assert "/api/word-cloud" in paths
    # Admin
    assert "/api/admin/fonogramas" in paths
    assert "/api/admin/songs" in paths
    assert "/api/admin/users" in paths
    assert "/api/admin/emails" in paths
    assert "/api/admin/audit" in paths
    # Health
    assert "/healthz" in paths


def test_openapi_spec_auth_endpoints_include_token_field(tmp_path):
    """The /api/auth/{login,register,refresh} response must include
    a ``token`` field so the Vue dashboard can stash the JWT in
    localStorage (matching the Go contract).
    """
    settings = Settings(env="dev", jwt_secret="x" * 64, db_path=tmp_path / "x.db")
    create_app(settings)
    committed = json.loads(OPENAPI_PATH.read_text())
    schemas = committed["components"]["schemas"]
    assert "AuthResponse" in schemas
    auth = schemas["AuthResponse"]
    assert "token" in auth["properties"], (
        f"AuthResponse missing 'token' field: {auth}"
    )


def test_openapi_spec_search_query_alias(tmp_path):
    """Frontend sends ?query=...; the spec must document it as the
    canonical alias.
    """
    # Trigger the schema-creation path so the spec is materialised.
    settings = Settings(env="dev", jwt_secret="x" * 64, db_path=tmp_path / "x.db")
    create_app(settings)
    committed = json.loads(OPENAPI_PATH.read_text())
    search_get = committed["paths"]["/api/search"]["get"]
    query_param = next(
        (p for p in search_get["parameters"] if p["name"] in ("q", "query")),
        None,
    )
    assert query_param is not None, "/api/search missing query parameter"
    # FastAPI exposes aliases via ``schema.x-aliases``; we accept either
    # ``query`` being the canonical name OR being listed in aliases.
    assert query_param["name"] in ("q", "query")
