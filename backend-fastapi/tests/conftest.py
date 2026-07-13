"""Shared pytest fixtures.

Engine lifecycle: each test gets a single in-memory sqlite that is
shared between the FastAPI app (mounted under ``app_client``) and any
``make_user`` / ``make_admin`` call in the test body. The shared
``StaticPool`` connection is the simplest way to make sure a row
inserted during test setup is visible to the API call that follows.

We deliberately grab the engine via ``app.db.session._engine`` rather
than ``from app.db.session import _engine`` because Python rebinds the
global inside ``init_in_memory_engine`` / ``init_engine``; the
import-style binding would cache the original ``None``.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app import db as db_module
from app.config import Settings
from app.main import create_app
from app.models import Base, EmailOutbox, User, UserIdentity
from app.security import hash_password
from app.services.email import EmailService


@pytest_asyncio.fixture
async def settings(tmp_path: Path) -> Settings:
    """Settings pointing at a fresh tmp sqlite + deterministic secrets."""
    return Settings(
        env="dev",
        db_path=tmp_path / "test.db",
        jwt_secret="test-secret-must-be-at-least-32-chars-long-xx",
        admin_bootstrap_username="admin",
        admin_bootstrap_email="admin@cenidim.test",
        admin_bootstrap_password="admin1234",
    )


@pytest_asyncio.fixture
async def db_session(settings: Settings) -> AsyncIterator[None]:
    """Per-test in-memory sqlite + ORM schema bootstrap.

    Yields ``None``: callers do their ORM work via the helpers
    below or by grabbing ``app.db.session.get_sessionmaker()()``
    directly. The schema is created on yield so any subsequent
    ``make_user`` / API call sees the tables.
    """
    db_module.init_in_memory_engine()
    EmailService.configure(settings)
    engine = db_module.session._engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield None


@pytest_asyncio.fixture
async def app_client(db_session, settings: Settings) -> AsyncIterator[AsyncClient]:
    """Per-test FastAPI app + httpx AsyncClient (no cookie sharing)."""
    app = create_app(settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def make_user(
    *,
    username: str,
    email: str,
    password: str = "Strong1234",  # noqa: S107  - test fixture password
    role: str = "viewer",
) -> User:
    """Persist a user row directly via its own short-lived session."""
    from datetime import UTC, datetime

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=role,
        created_at=datetime.now(UTC),
    )
    sm = db_module.session.get_sessionmaker()
    async with sm() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def make_admin() -> None:
    """Convenience: seed the bootstrap admin row used by most tests."""
    await make_user(
        username="admin",
        email="admin@cenidim.example",
        password="admin1234",
        role="admin",
    )


async def make_identity(
    *, user_id: int, provider: str = "google", subject: str = "google-subject"
) -> UserIdentity:
    """Persist a ``user_identities`` row directly."""
    identity = UserIdentity(
        user_id=user_id,
        provider=provider,
        subject=subject,
        email_at_link="admin@cenidim.example",
    )
    sm = db_module.session.get_sessionmaker()
    async with sm() as session:
        session.add(identity)
        await session.commit()
        await session.refresh(identity)
    return identity


async def make_email_outbox(
    *,
    to_addr: str = "bob@cenidim.example",
    subject: str = "Reset",
    kind: str = "password_reset",
    body_text: str = "click here",
    body_html: str | None = "<p>click here</p>",
) -> EmailOutbox:
    """Persist an ``email_outbox`` row directly."""
    from datetime import UTC, datetime

    row = EmailOutbox(
        to_addr=to_addr,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        kind=kind,
        sent_at=datetime.now(UTC),
    )
    sm = db_module.session.get_sessionmaker()
    async with sm() as session:
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return row


async def login_as(
    client: AsyncClient,
    username: str,
    password: str = "Strong1234",  # noqa: S107  - test fixture password
) -> None:
    """Log a user in via /api/auth/login and propagate the cookies
    (cenidim_session + cenidim_csrf) back onto the test client.

    The FastAPI app's CSRF middleware sets ``cenidim_csrf`` AND the
    login route itself calls ``response.set_cookie("cenidim_csrf", ...)``
    with a different value, so multiple Set-Cookie headers with the
    same name arrive in the same response. We therefore read the
    raw header list manually and keep only the most recent value per
    name, sidestepping httpx's CookieJar "two cookies with the same
    name" guard.
    """
    response = await client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    if response.status_code != 200:
        raise AssertionError(
            f"login_as failed: {response.status_code} {response.text}"
        )
    cookies: dict[str, str] = {}
    for raw in response.headers.raw:
        if raw[0].lower() != b"set-cookie":
            continue
        cookie_str = (
            raw[1].decode("latin-1") if isinstance(raw[1], bytes) else raw[1]
        )
        head = cookie_str.split(";", 1)[0]
        if "=" not in head:
            continue
        name, value = head.split("=", 1)
        cookies[name.strip()] = value.strip()
    # Wipe the jar first so we don't conflict with httpx's own jar state.
    client.cookies.clear()
    for name, value in cookies.items():
        client.cookies.set(name, value)


__all__ = [
    "app_client",
    "db_session",
    "login_as",
    "make_admin",
    "make_email_outbox",
    "make_identity",
    "make_user",
    "settings",
]
