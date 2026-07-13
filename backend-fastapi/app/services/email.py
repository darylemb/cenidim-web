"""Email service: Resend + dev fallback.

Phase 1 uses ``resend`` for production sends and a stdout + email_outbox
fallback for development. The outbox table is exposed to admins via
``GET /api/admin/emails`` so operators can inspect sends when the
demo SMTP is "log to stdout".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.config import Settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class EmailMessage:
    to: str
    subject: str
    body_text: str
    body_html: str
    kind: str
    related_user_id: int | None


def render_password_reset_email(username: str, reset_url: str) -> tuple[str, str]:
    text = (
        f"Hola {username},\n\n"
        f"Recibimos una solicitud para restablecer la contraseña de tu "
        f"cuenta en el CENIDIM.\n\n"
        f"Para continuar, abrí este enlace en tu navegador (caduca en 1 hora, "
        f"un solo uso):\n{reset_url}\n\n"
        f"Si no solicitaste este cambio, podés ignorar este mensaje.\n\n"
        f"— CENIDIM Archivo Musical\n"
    )
    html = (
        f'<!doctype html><html><body style="font-family: system-ui, sans-serif; max-width: 560px; '
        f'margin: 2em auto; color: #1a1612;">'
        f"<h1 style=\"font-size: 1.4em;\">Hola {username},</h1>"
        f"<p>Recibimos una solicitud para restablecer la contraseña de tu cuenta en el CENIDIM.</p>"
        f'<p style="margin: 2em 0;"><a href="{reset_url}" '
        f'style="background: #751428; color: #faf7f0; padding: 0.75em 1.5em; '
        f'text-decoration: none; border-radius: 2px;">Restablecer contraseña</a></p>'
        f'<p style="color: #666; font-size: 0.9em;">El enlace caduca en 1 hora y es de un solo uso. '
        f'Si no solicitaste este cambio, podés ignorar este mensaje.</p>'
        f'<p style="color: #999; font-size: 0.8em;">— CENIDIM Archivo Musical</p>'
        f"</body></html>"
    )
    return text, html


class EmailService:
    """Send wrapper around the Resend SDK + email_outbox fallback."""

    _settings: Settings | None = None

    @classmethod
    def configure(cls, settings: Settings) -> None:
        cls._settings = settings

    @classmethod
    def settings(cls) -> Settings:
        if cls._settings is None:
            from app.config import get_settings
            cls._settings = get_settings()
        return cls._settings  # type: ignore[return-value]

    @classmethod
    async def enqueue(
        cls,
        *,
        to: str,
        subject: str,
        body: tuple[str, str] | str,
        kind: str,
        related_user_id: int | None,
        db: AsyncSession | None = None,
    ) -> int | None:
        """Persist the email to email_outbox; send via Resend if configured.

        Returns the email_outbox row id (so callers / admin UI can
        reference the message), or None if the outbox write failed.

        If ``db`` is provided (caller already has a session, e.g.
        inside a FastAPI dep) we reuse it; otherwise we open our
        own via ``session_scope()``.
        """
        if isinstance(body, str):
            text, html = body, body
        else:
            text, html = body
        settings = cls.settings()
        # Phase 1: persist to email_outbox. The model lives in the
        # admin audit/emails module; we inline the SQL here to keep
        # the email service free of circular imports with models.
        from sqlalchemy import text as sa_text

        async def _insert(session: AsyncSession) -> int | None:
            result = await session.execute(
                sa_text(
                    "INSERT INTO email_outbox "
                    "(to_addr, subject, body_text, body_html, kind, related_user_id) "
                    "VALUES (:to, :subj, :text, :html, :kind, :uid)"
                ),
                {
                    "to": to,
                    "subj": subject,
                    "text": text,
                    "html": html,
                    "kind": kind,
                    "uid": related_user_id,
                },
            )
            return result.lastrowid

        row_id: int | None = None
        try:
            if db is not None:
                row_id = await _insert(db)
            else:
                from app.db import session_scope_cm

                async with session_scope_cm() as scoped:
                    row_id = await _insert(scoped)
        except Exception as exc:  # noqa: BLE001 - never break the caller; just log
            import logging

            logging.getLogger(__name__).warning(
                "email_outbox insert failed for kind=%s to=%s: %s", kind, to, exc,
            )
            row_id = None
        # Phase 1: only attempt Resend when API key + non-dev provider.
        if (
            settings.email_provider == "resend"
            and settings.resend_api_key
            and settings.resend_api_key.get_secret_value()
        ):
            cls._send_resend(
                to=to,
                subject=subject,
                text=text,
                html=html,
                api_key=settings.resend_api_key.get_secret_value(),
                from_addr=settings.email_from,
            )
        elif settings.email_demo_print_body or settings.env == "dev":
            import logging
            logging.getLogger(__name__).info(
                "[DEV EMAIL OUTBOX id=%s kind=%s] to=%s subject=%r link/body available in email_outbox row",
                row_id, kind, to, subject,
            )
        return row_id

    @staticmethod
    def _send_resend(*, to: str, subject: str, text: str, html: str,
                      api_key: str, from_addr: str) -> None:
        """Send via the official Resend SDK. Network errors are logged."""
        try:
            import resend  # type: ignore
            resend.api_key = api_key
            resend.Emails.send(
                {
                    "from": from_addr,
                    "to": to,
                    "subject": subject,
                    "text": text,
                    "html": html,
                }
            )
        except Exception as exc:  # noqa: BLE001
            import logging
            logging.getLogger(__name__).warning("Resend send failed for to=%s: %s", to, exc)

    @classmethod
    def build_reset_body(cls, username: str, reset_url: str) -> tuple[str, str]:
        return render_password_reset_email(username, reset_url)


__all__ = ["EmailService", "EmailMessage", "render_password_reset_email"]
