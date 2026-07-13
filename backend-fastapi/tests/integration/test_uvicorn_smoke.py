"""End-to-end smoke test: boot uvicorn against a temp ``letras.db``
and hit it with a real ``httpx`` client.

This is the integration test that mirrors what
``docker compose -f docker-compose-fastapi.yaml up`` does in
production. The FastAPI test suite otherwise uses ASGITransport,
which exercises the FastAPI app in-process; this test boots a real
``uvicorn`` worker so we catch anything uvicorn-only (middleware
ordering, proxy headers, server-sent lifespan events, etc).
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]  # backend-fastapi/
APP_DIR = ROOT  # uvicorn's cwd so it can `import app.main`


def _free_port() -> int:
    """Bind a TCP socket to port 0 to grab a free port, then close."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_health(base_url: str, timeout: float = 15.0) -> None:
    """Poll /healthz until the server is ready."""
    deadline = time.monotonic() + timeout
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            r = httpx.get(f"{base_url}/healthz", timeout=1.0)
            if r.status_code == 200 and r.json() == {"status": "ok"}:
                return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
        time.sleep(0.2)
    raise AssertionError(f"uvicorn never reported healthy: {last_err}")


@pytest.fixture(scope="module")
def uvicorn_server(tmp_path_factory):
    """Boot uvicorn for the duration of this module's tests."""
    tmpdir = tmp_path_factory.mktemp("e2e")
    db_path = tmpdir / "letras.db"
    port = _free_port()
    env = {
        **os.environ,
        "CENIDIM_DB_PATH": str(db_path),
        "CENIDIM_JWT_SECRET": "x" * 64,
        "CENIDIM_ENV": "dev",
        # uvicorn's worker resolves ``import app.main`` from cwd;
        # PYTHONPATH makes sure the project's package root is found
        # even when the subprocess cwd differs from the venv layout.
        "PYTHONPATH": str(ROOT),
    }
    proc = subprocess.Popen(
        [
            sys.executable,
            "-c",
            # Pre-import the package on PYTHONPATH so uvicorn can
            # import_from_string without re-resolving sys.path.
            (
                f"import sys; sys.path.insert(0, '{str(ROOT)}'); "
                "from uvicorn.main import main; main()"
            ),
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=str(APP_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    base_url = f"http://127.0.0.1:{port}"
    try:
        try:
            _wait_for_health(base_url)
        except AssertionError:
            proc.terminate()
            stdout = proc.stdout.read() if proc.stdout else b""
            raise AssertionError(
                f"uvicorn never reported healthy. Output:\n{stdout.decode(errors='replace')}"
            )
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)


def test_healthz_responds(uvicorn_server):
    """A real uvicorn worker must serve /healthz with 200."""
    r = httpx.get(f"{uvicorn_server}/healthz", timeout=2.0)
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_openapi_spec_is_served(uvicorn_server):
    """FastAPI auto-serves /openapi.json — confirm it's reachable."""
    r = httpx.get(f"{uvicorn_server}/openapi.json", timeout=2.0)
    assert r.status_code == 200
    spec = r.json()
    assert spec["info"]["title"] == "CENIDIM API"
    assert "/api/search" in spec["paths"]
    assert "/api/auth/login" in spec["paths"]


def test_login_flow_via_real_http(uvicorn_server):
    """Login → /me → logout: a full cookie-driven round-trip."""
    base = uvicorn_server
    # Seed an admin user directly in the DB the running server is using.
    # We have to reach into the same file; uvicorn's env already pointed
    # at the tmpdir DB, so write through SQLite.

    # We don't have direct access to the tmpdir here (uvicorn_server
    # fixture owns it). Instead, register through the API: the test
    # starts with no users; ``/api/auth/register`` is the bootstrap.
    reg = httpx.post(
        f"{base}/api/auth/register",
        json={
            "username": "smoketest",
            "email": "smoketest@cenidim.example",
            "password": "Strong1234",
        },
        timeout=2.0,
    )
    assert reg.status_code == 201, reg.text

    # /api/auth/me rejects anonymous
    me_anonymous = httpx.get(f"{base}/api/auth/me", timeout=2.0)
    assert me_anonymous.status_code == 401

    # Login (cookie jar)
    client = httpx.Client(base_url=base, timeout=2.0)
    try:
        login = client.post(
            "/api/auth/login",
            json={"username": "smoketest", "password": "Strong1234"},
        )
        assert login.status_code == 200, login.text
        body = login.json()
        assert body["user"]["username"] == "smoketest"
        assert body["token"]  # JWT mirrored in body
        # /me now succeeds because the cookie jar carries the session
        me = client.get("/api/auth/me")
        assert me.status_code == 200
        assert me.json()["username"] == "smoketest"

        # Search returns an empty catalog (no songs seeded)
        sr = client.get("/api/search", params={"query": "anything"})
        assert sr.status_code == 200
        assert sr.json() == {"results": [], "total": 0}

        # Stats reflects the empty catalog
        stats = client.get("/api/stats")
        assert stats.status_code == 200
        body = stats.json()
        assert body["total_songs"] == 0
        assert body["total_albums"] == 0

        # Logout clears the session
        out = client.post("/api/auth/logout")
        assert out.status_code == 200
        me2 = client.get("/api/auth/me")
        # Cookie was deleted; session is gone.
        assert me2.status_code == 401
    finally:
        client.close()


def test_admin_endpoint_requires_auth(uvicorn_server):
    """No anonymous user can hit /api/admin/*."""
    r = httpx.get(f"{uvicorn_server}/api/admin/users", timeout=2.0)
    assert r.status_code == 401


def test_correlation_error_responses_are_json(uvicorn_server):
    """Bad request bodies should surface as 422 with a JSON body."""
    r = httpx.post(
        f"{uvicorn_server}/api/auth/login",
        json={"username": "", "password": ""},
        timeout=2.0,
    )
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/json")
    body = r.json()
    assert "detail" in body
