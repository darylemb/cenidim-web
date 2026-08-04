"""Smoke test: app boots, /healthz returns 200, the auth router mounts."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import create_app


@pytest.mark.asyncio
async def test_app_boots_and_healthz_responds(tmp_path):
    settings = Settings(
        env="dev",
        db_path=tmp_path / "smoke.db",
        jwt_secret="x" * 64,
        admin_bootstrap_username="admin",
        admin_bootstrap_email="admin@cenidim.test",
        admin_bootstrap_password="admin1234",
    )
    app = create_app(settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_app_exposes_openapi_docs_in_dev(tmp_path):
    settings = Settings(
        env="dev",
        db_path=tmp_path / "smoke2.db",
        jwt_secret="x" * 64,
        admin_bootstrap_username="admin",
        admin_bootstrap_email="admin@cenidim.test",
        admin_bootstrap_password="admin1234",
    )
    app = create_app(settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        assert "/api/auth/login" in response.json()["paths"]
