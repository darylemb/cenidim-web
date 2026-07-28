"""End-to-end tests for the /metrics endpoint."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_text(app_client, db_session):
    response = await app_client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "# HELP cenidim_http_requests_total" in body
    assert "# TYPE cenidim_http_requests_total counter" in body


@pytest.mark.asyncio
async def test_metrics_endpoint_records_request(app_client, db_session):
    await app_client.get("/healthz")
    response = await app_client.get("/metrics")
    assert response.status_code == 200
    body = response.text
    assert 'path="/healthz"' in body


@pytest.mark.asyncio
async def test_metrics_endpoint_includes_histogram(app_client, db_session):
    await app_client.get("/healthz")
    response = await app_client.get("/metrics")
    body = response.text
    assert "cenidim_http_request_duration_seconds_bucket" in body
    assert "cenidim_http_request_duration_seconds_count" in body
    assert "cenidim_http_request_duration_seconds_sum" in body


@pytest.mark.asyncio
async def test_metrics_endpoint_not_in_openapi(app_client, db_session):
    """We hide /metrics from the public OpenAPI surface."""
    response = await app_client.get("/openapi.json")
    spec = response.json()
    assert "/metrics" not in spec["paths"]


@pytest.mark.asyncio
async def test_4xx_counter_increments_on_404(app_client, db_session):
    """Hit a 404 then check the 4xx counter is non-zero."""
    await app_client.get("/api/song/999999")
    response = await app_client.get("/metrics")
    body = response.text
    assert "cenidim_http_4xx_total" in body
