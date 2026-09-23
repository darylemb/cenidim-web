"""Tests for the EmailService: Resend SDK + outbox + dev-fallback."""
from __future__ import annotations

import pytest
from sqlalchemy import select

from app import db as db_module
from app.models.email_outbox import EmailOutbox
from app.services.email import EmailService


@pytest.mark.asyncio
async def test_enqueue_inserts_into_outbox(db_session, settings):
    EmailService.configure(settings)
    row_id = await EmailService.enqueue(
        to="alice@cenidim.example",
        subject="hi",
        body="hello",
        kind="welcome",
        related_user_id=None,
    )
    assert row_id is not None
    sm = db_module.session.get_sessionmaker()
    async with sm() as session:
        out = (
            await session.execute(select(EmailOutbox).where(EmailOutbox.id == row_id))
        ).scalar_one_or_none()
        assert out is not None
        assert out.subject == "hi"
        assert out.kind == "welcome"


@pytest.mark.asyncio
async def test_enqueue_accepts_text_html_pair(db_session, settings):
    EmailService.configure(settings)
    row_id = await EmailService.enqueue(
        to="bob@cenidim.example",
        subject="pair",
        body=("plain", "<p>html</p>"),
        kind="welcome",
        related_user_id=None,
    )
    assert row_id is not None


@pytest.mark.asyncio
async def test_enqueue_returns_none_when_outbox_write_fails(
    db_session, settings, monkeypatch
):
    EmailService.configure(settings)

    def _raise_cm():
        raise RuntimeError("kaboom")

    # The email service looks up ``session_scope_cm`` lazily; we
    # monkey-patch the function imported in its closure via the
    # ``app.db`` namespace (the canonical export).
    from app import db as db_module_pkg

    monkeypatch.setattr(db_module_pkg, "session_scope_cm", _raise_cm)
    # Force the email module to re-import on its next call.
    import app.services.email as email_pkg

    monkeypatch.setattr(email_pkg, "session_scope_cm", _raise_cm, raising=False)
    row_id = await EmailService.enqueue(
        to="x@cenidim.example",
        subject="x",
        body="x",
        kind="x",
        related_user_id=None,
    )
    assert row_id is None


@pytest.mark.asyncio
async def test_enqueue_respects_provider_off_and_dev_print(settings, caplog):
    EmailService.configure(settings)
    settings.email_provider = "outbox"
    settings.email_demo_print_body = False
    settings.env = "dev"
    import logging

    caplog.set_level(logging.INFO, logger="app.services.email")
    await EmailService.enqueue(
        to="info@cenidim.example",
        subject="dev-outbox",
        body="hello",
        kind="dev",
        related_user_id=None,
    )
    # The dev-fallback branch logs once with subject + kind
    info_records = [r for r in caplog.records if "DEV EMAIL OUTBOX" in r.message]
    assert info_records


@pytest.mark.asyncio
async def test_build_reset_body_returns_text_and_html():
    text, html = EmailService.build_reset_body(
        "alice",
        "http://localhost:3000/reset?token=abc",
    )
    assert "alice" in text
    assert "http://localhost:3000/reset?token=abc" in text
    assert "alice" in html
    assert "Restablecer" in html


@pytest.mark.asyncio
async def test_render_password_reset_email_top_level():
    from app.services.email import render_password_reset_email

    text, html = render_password_reset_email(
        "alice", "http://localhost:3000/reset?token=abc"
    )
    assert "alice" in text
    assert "http://localhost:3000/reset?token=abc" in text
    assert "<" in html


def test_send_resend_handles_missing_sdk(monkeypatch):
    """The Resend SDK is an optional import; failure is logged."""
    import builtins

    from app.services.email import EmailService

    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "resend":
            raise ImportError("forced missing")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    # Should log a warning rather than raise
    import logging

    logging.getLogger("app.services.email").info("smoke")
    # Direct invoke path: just confirm the call doesn't raise ImportError
    # because the SDK call lives behind the try/except in EmailService._send_resend.
    EmailService._send_resend(
        to="a@x.example",
        subject="x",
        text="x",
        html="x",
        api_key="dummy",
        from_addr="noreply@example.com",
    )
