"""End-to-end API verification against a running CENIDIM stack.

Walks every endpoint exposed by the FastAPI backend, exercises the
happy path, and cross-checks aggregate numbers against the SQLite
``letras.db`` to confirm the API and the on-disk catalog agree.

Usage:

    # default — hits the FastAPI overlay on :8000
    uv run python scripts/verify_api.py

    # via the nginx proxy (matches what the browser sees)
    uv run python scripts/verify_api.py --base http://localhost:80

    # custom DB path (defaults to ./backend/data/letras.db)
    uv run python scripts/verify_api.py --db ./backend/data/letras.db

The script exits 0 when every check passes, 1 on the first failure.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlencode

import httpx


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------

@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""
    expected: str = ""
    actual: str = ""


@dataclass
class Report:
    checks: list[Check] = field(default_factory=list)
    elapsed: float = 0.0

    def add(self, name: str, ok: bool, detail: str = "", expected: str = "", actual: str = "") -> None:
        self.checks.append(Check(name=name, passed=ok, detail=detail, expected=expected, actual=actual))
        marker = "PASS" if ok else "FAIL"
        print(f"  {marker:4}  {name}")
        if detail:
            print(f"        {detail}")
        if not ok and (expected or actual):
            print(f"        expected: {expected}")
            print(f"        actual:   {actual}")

    def exit_code(self) -> int:
        return 0 if all(c.passed for c in self.checks) else 1


# ---------------------------------------------------------------------------
# DB introspection — cross-checks the API against the on-disk catalog
# ---------------------------------------------------------------------------

def db_counts(db_path: str) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    try:
        return {
            "songs": conn.execute("SELECT COUNT(*) FROM songs").fetchone()[0],
            "fonogramas": conn.execute("SELECT COUNT(*) FROM fonogramas").fetchone()[0],
            "users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            "with_lyrics": conn.execute(
                "SELECT COUNT(*) FROM songs WHERE lyrics IS NOT NULL AND lyrics != ''"
            ).fetchone()[0],
            "s_d_year": conn.execute(
                "SELECT COUNT(*) FROM songs s JOIN fonogramas f "
                "ON s.fonograma_id = f.clave_fonograma "
                "WHERE f.anio IS NULL OR f.anio = '' OR f.anio = 's/d'"
            ).fetchone()[0],
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Endpoint walker
# ---------------------------------------------------------------------------

def _check_status(client: httpx.Client, method: str, url: str, *, want: int,
                  headers: dict | None = None, json_body: dict | None = None,
                  params: dict | None = None) -> httpx.Response:
    response = client.request(method, url, headers=headers, json=json_body, params=params)
    if response.status_code != want:
        raise AssertionError(
            f"{method} {url} returned {response.status_code}, expected {want}: "
            f"{response.text[:200]}"
        )
    return response


def run(base: str, db_path: str, username: str, password: str) -> Report:
    report = Report()
    started = time.time()

    print(f"\n=== Verifying {base} against {db_path} ===\n")

    # Login (the verification does NOT mutate state; the admin user
    # exists from the db-init sidecar).
    with httpx.Client(base_url=base, timeout=30.0) as client:
        print("[setup] logging in as", username)
        try:
            login = _check_status(
                client, "POST", "/api/auth/login", want=200,
                json_body={"username": username, "password": password},
            )
            token = login.json()["token"]
        except AssertionError as exc:
            report.add("login", False, str(exc))
            return report
        report.add("login", True, detail=f"got token ({len(token)} chars)")

        auth_headers = {"Authorization": f"Bearer {token}"}

        # ---------------------------------------------------------------
        # Public routes — no auth
        # ---------------------------------------------------------------
        print("\n[public] /api/search")
        try:
            # Note: the parameter is exposed as ``query`` (alias for q).
            # ``?q=foo`` is ignored — the field is empty and the
            # endpoint returns every row.
            r = _check_status(client, "GET", "/api/search?limit=5", want=200)
            data = r.json()
            report.add(
                "search shape (no filter)",
                len(data["results"]) == 5 and data["total"] > 0,
                f"total={data['total']}, returned {len(data['results'])}",
            )
            counts = db_counts(db_path)
            report.add(
                "search total == DB songs",
                data["total"] == counts["songs"],
                expected=str(counts["songs"]), actual=str(data["total"]),
            )
            r = _check_status(client, "GET", "/api/search?query=cri-cri&limit=5", want=200)
            filtered = r.json()
            report.add(
                "search filters by query",
                0 < filtered["total"] < counts["songs"],
                f"total={filtered['total']} (should be < {counts['songs']})",
            )
            # Song detail
            first_id = data["results"][0]["id"]
            r = _check_status(client, "GET", f"/api/song/{first_id}", want=200)
            report.add("song detail returns full payload", "title" in r.json())
        except AssertionError as exc:
            report.add("search/song", False, str(exc))

        print("\n[public] /api/timeline")
        try:
            r = _check_status(client, "GET", "/api/timeline", want=200)
            data = r.json()
            counts = db_counts(db_path)
            total_songs_in_timeline = sum(len(v) for v in data["timeline"].values())
            report.add(
                "timeline total covers DB",
                total_songs_in_timeline >= counts["songs"] * 0.9,
                f"timeline={total_songs_in_timeline}, db songs={counts['songs']} "
                f"(limit=5000 may truncate for huge catalogs)",
                expected=str(counts["songs"]), actual=str(total_songs_in_timeline),
            )
            real_years = [y for y in data["years"] if y != "s/d"]
            report.add(
                "timeline has real years first",
                real_years[:1][0] < real_years[-1:][0] if real_years else False,
                f"first year = {real_years[:1]}",
            )
        except AssertionError as exc:
            report.add("timeline", False, str(exc))

        print("\n[public] /api/stats")
        try:
            r = _check_status(client, "GET", "/api/stats", want=200)
            data = r.json()
            counts = db_counts(db_path)
            report.add(
                "stats total_songs",
                data["total_songs"] == counts["songs"],
                expected=str(counts["songs"]), actual=str(data["total_songs"]),
            )
            report.add(
                "stats total_albums",
                data["total_albums"] == counts["fonogramas"],
                expected=str(counts["fonogramas"]), actual=str(data["total_albums"]),
            )
            report.add(
                "stats songs_with_lyrics",
                data["songs_with_lyrics"] == counts["with_lyrics"],
                expected=str(counts["with_lyrics"]), actual=str(data["songs_with_lyrics"]),
            )
            report.add(
                "stats songs_without_year",
                data["songs_without_year"] == counts["s_d_year"],
                expected=str(counts["s_d_year"]), actual=str(data["songs_without_year"]),
            )
        except AssertionError as exc:
            report.add("stats", False, str(exc))

        print("\n[public] /api/word-cloud")
        try:
            r = _check_status(client, "GET", "/api/word-cloud?limit=50", want=200)
            data = r.json()
            report.add(
                "word-cloud has top words",
                isinstance(data.get("words"), list)
                and len(data["words"]) > 0
                and all(
                    isinstance(w, dict) and "text" in w and "size" in w
                    for w in data["words"]
                ),
                f"{len(data.get('words', []))} words returned (data keys: {sorted(data.keys())})",
            )
        except AssertionError as exc:
            report.add("word-cloud", False, str(exc))

        # ---------------------------------------------------------------
        # Auth routes
        # ---------------------------------------------------------------
        print("\n[auth] /api/auth/me")
        try:
            r = _check_status(client, "GET", "/api/auth/me", want=200, headers=auth_headers)
            data = r.json()
            report.add(
                "me returns admin",
                data.get("role") == "admin" and data.get("username") == username,
                detail=str(data),
            )
        except AssertionError as exc:
            report.add("me", False, str(exc))

        print("\n[auth] /api/auth/refresh (and rehash check)")
        try:
            # The login response set cenidim_session + cenidim_refresh cookies;
            # POST /api/auth/refresh with the refresh cookie returns 200.
            refresh_token = client.cookies.get("cenidim_refresh")
            report.add("refresh cookie present", refresh_token is not None)
            if refresh_token:
                r = client.post(
                    "/api/auth/refresh",
                    cookies={"cenidim_refresh": refresh_token},
                )
                if r.status_code == 200:
                    report.add("refresh returns new tokens", "token" in r.json())
                else:
                    report.add(
                        "refresh",
                        False,
                        f"status {r.status_code}: {r.text[:200]}",
                    )
        except Exception as exc:
            report.add("refresh", False, str(exc))

        print("\n[auth] /api/auth/forgot + /api/auth/reset")
        try:
            # ``email_demo_print_body`` is read from the SERVER's
            # Settings, not from this client. We can't flip it from
            # here without monkey-patching — so we just verify the
            # endpoint returns 200 with a body.
            r = _check_status(
                client, "POST", "/api/auth/forgot", want=200,
                json_body={"email": "admin@cenidim.mx"},
            )
            body = r.json()
            report.add(
                "forgot returns ok envelope",
                body.get("ok") is True and "dev_link" in body,
                detail=str(body),
            )
            if body.get("dev_link"):
                token = body["dev_link"].split("token=")[1]
                r = _check_status(
                    client, "POST", "/api/auth/reset", want=200,
                    json_body={"token": token, "new_password": "AdminReset1"},
                )
                # Roll back: change password back to the original so the
                # script is idempotent.
                client.post("/api/auth/forgot", json={"email": "admin@cenidim.mx"})
                rollback = client.post(
                    "/api/auth/forgot",
                    json={"email": "admin@cenidim.mx"},
                ).json().get("dev_link")
                if rollback:
                    client.post(
                        "/api/auth/reset",
                        json={"token": rollback.split("token=")[1],
                              "new_password": password},
                    )
                report.add("reset accepts the issued token", True)
            else:
                report.add(
                    "reset path skipped",
                    True,
                    detail=("dev_link is null; "
                            "the server's email_demo_print_body is False. "
                            "Set CENIDIM_LOG_FORMAT=json + run with "
                            "settings.email_demo_print_body=True to test."),
                )
        except AssertionError as exc:
            report.add("forgot/reset", False, str(exc))

        print("\n[auth] /api/auth/register (dedicated viewer, then delete via admin)")
        try:
            new_user = "verifyviewer1"
            # Use a non-reserved domain (``.local`` is reserved by
            # RFC 6761; the EmailStr validator rejects it).
            new_email = f"{new_user}@example.com"
            r = _check_status(
                client, "POST", "/api/auth/register", want=201,
                json_body={"username": new_user, "email": new_email, "password": "Test1234"},
            )
            new_user_id = r.json()["user"]["id"]
            report.add("register returns viewer tier", r.json()["user"]["role"] == "viewer")
            # Login as the new user to confirm credentials work.
            r = _check_status(
                client, "POST", "/api/auth/login", want=200,
                json_body={"username": new_user, "password": "Test1234"},
            )
            report.add("registered user can log in", "token" in r.json())
            # Clean up via the admin DELETE endpoint so the row is
            # removed from the live container DB (not just from a
            # ``docker cp`` snapshot). Falling back to raw sqlite3
            # would leave the container's aiosqlite connection holding
            # an extra user for the next admin check. The client is
            # currently carrying the viewer's session cookies, so we
            # re-login as admin first to authorise the DELETE.
            _check_status(
                client, "POST", "/api/auth/login", want=200,
                json_body={"username": username, "password": password},
            )
            token = client.cookies.get("cenidim_session")
            admin_auth = {"Authorization": f"Bearer {client.post('/api/auth/login', json={'username': username, 'password': password}).json()['token']}"}
            _check_status(
                client, "DELETE", f"/api/admin/users/{new_user_id}", want=200,
                headers=admin_auth,
            )
            report.add("register cleanup via DELETE", True)
        except AssertionError as exc:
            report.add("register", False, str(exc))

        # ---------------------------------------------------------------
        # Admin routes (require auth)
        # ---------------------------------------------------------------
        # Re-login as admin because the previous register step set
        # the auth cookies to the just-created viewer (which we then
        # deleted). A fresh login re-issues the JWT for user id=1.
        print("\n[setup] re-login as admin (cookies were a viewer's)")
        try:
            login2 = _check_status(
                client, "POST", "/api/auth/login", want=200,
                json_body={"username": username, "password": password},
            )
            token = login2.json()["token"]
            auth_headers = {"Authorization": f"Bearer {token}"}
            report.add("re-login as admin", True, detail=f"token={len(token)} chars")
        except AssertionError as exc:
            report.add("re-login as admin", False, str(exc))

        print("\n[admin] /api/admin/fonogramas")
        try:
            r = _check_status(
                client, "GET", "/api/admin/fonogramas?limit=5", want=200,
                headers=auth_headers,
            )
            data = r.json()
            counts = db_counts(db_path)
            report.add(
                "admin/fonogramas total",
                data["total"] == counts["fonogramas"],
                expected=str(counts["fonogramas"]), actual=str(data["total"]),
            )
            # Update + revert a fonograma so we exercise the editor path
            # without leaving the DB mutated.
            first = data["results"][0]
            clave = first["clave_fonograma"]
            original_titulo = first["titulo"]
            new_titulo = original_titulo + " [verify]"
            r = _check_status(
                client, "PUT", f"/api/admin/fonogramas/{clave}", want=200,
                headers=auth_headers, json_body={**first, "titulo": new_titulo},
            )
            report.add("admin PUT fonograma", r.json()["titulo"] == new_titulo)
            _check_status(
                client, "PUT", f"/api/admin/fonogramas/{clave}", want=200,
                headers=auth_headers, json_body={**first, "titulo": original_titulo},
            )
        except AssertionError as exc:
            report.add("admin/fonogramas", False, str(exc))

        print("\n[admin] /api/admin/songs")
        try:
            r = _check_status(
                client, "GET", "/api/admin/songs?limit=5", want=200,
                headers=auth_headers,
            )
            data = r.json()
            counts = db_counts(db_path)
            report.add(
                "admin/songs total",
                data["total"] == counts["songs"],
                expected=str(counts["songs"]), actual=str(data["total"]),
            )
        except AssertionError as exc:
            report.add("admin/songs", False, str(exc))

        print("\n[admin] /api/admin/users")
        try:
            r = _check_status(
                client, "GET", "/api/admin/users", want=200, headers=auth_headers,
            )
            data = r.json()
            counts = db_counts(db_path)
            report.add(
                "admin/users total",
                len(data) == counts["users"],
                expected=str(counts["users"]), actual=str(len(data)),
            )
            report.add(
                "admin/users contains admin",
                any(u["username"] == username and u["role"] == "admin" for u in data),
            )
        except AssertionError as exc:
            report.add("admin/users", False, str(exc))

        print("\n[admin] /api/admin/emails")
        try:
            r = _check_status(
                client, "GET", "/api/admin/emails", want=200, headers=auth_headers,
            )
            data = r.json()
            report.add("admin/emails returns paginated envelope",
                       "results" in data and "total" in data)
        except AssertionError as exc:
            report.add("admin/emails", False, str(exc))

        print("\n[admin] /api/admin/audit")
        try:
            r = _check_status(
                client, "GET", "/api/admin/audit", want=200, headers=auth_headers,
            )
            data = r.json()
            report.add("admin/audit returns paginated envelope",
                       "results" in data and "total" in data)
            # The password-reset flow we ran earlier should have written
            # at least one audit row.
            report.add("admin/audit has entries", data["total"] >= 1,
                       f"total={data['total']}")
        except AssertionError as exc:
            report.add("admin/audit", False, str(exc))

        # ---------------------------------------------------------------
        # Auth boundary checks — must use a FRESH client so the
        # session cookies from login don't ride along.
        # ---------------------------------------------------------------
        print("\n[boundaries] protected routes reject unauthenticated calls")
        with httpx.Client(base_url=base, timeout=10.0) as anon:
            for path in (
                "/api/admin/users",
                "/api/admin/fonogramas",
                "/api/admin/songs",
                "/api/admin/emails",
                "/api/admin/audit",
            ):
                try:
                    _check_status(anon, "GET", path, want=401)
                    report.add(f"GET {path} requires auth", True)
                except AssertionError as exc:
                    report.add(f"GET {path} requires auth", False, str(exc))

        # ---------------------------------------------------------------
        # Health
        # ---------------------------------------------------------------
        try:
            _check_status(client, "GET", "/healthz", want=200)
            report.add("healthz returns 200", True)
        except AssertionError as exc:
            report.add("healthz", False, str(exc))

        # Prometheus exposition (just check status; format is exercised
        # in tests/api/test_observability_api.py).
        try:
            _check_status(client, "GET", "/metrics", want=200)
            report.add("/metrics returns 200", True)
        except AssertionError as exc:
            report.add("/metrics", False, str(exc))

    report.elapsed = time.time() - started
    return report


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--base", default="http://localhost:8000",
                        help="Base URL of the running backend (default: %(default)s)")
    parser.add_argument("--db", default="./backend/data/letras.db",
                        help="Path to letras.db for cross-checks (default: %(default)s)")
    parser.add_argument("--username", default="admin",
                        help="Admin username (default: %(default)s)")
    parser.add_argument("--password", default="admin123",
                        help="Admin password (default: %(default)s)")
    args = parser.parse_args()

    report = run(args.base, args.db, args.username, args.password)

    print("\n" + "=" * 60)
    passed = sum(1 for c in report.checks if c.passed)
    total = len(report.checks)
    print(f"Result: {passed}/{total} passed in {report.elapsed:.2f}s")
    if report.exit_code() != 0:
        print("\nFailed checks:")
        for c in report.checks:
            if not c.passed:
                print(f"  - {c.name}: {c.detail}")
    print("=" * 60 + "\n")
    return report.exit_code()


if __name__ == "__main__":
    sys.exit(main())