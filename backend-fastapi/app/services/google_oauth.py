"""Google OAuth: production id-token verifier wiring.

We import the google-auth SDK lazily so unit tests can run without
the dependency. The app calls ``build_default_verifier()`` at first
request (or via ``configure_verifier(verifier=...)`` at startup).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.routers.google_oauth import (
    GoogleIDTokenClaims,
    IDTokenVerifier,
    StubIDTokenVerifier,
)

_log = logging.getLogger(__name__)

GOOGLE_AUDIENCES = {
    "https://accounts.google.com",
    "accounts.google.com",
}


def build_default_verifier() -> IDTokenVerifier:
    """Return a real verifier if ``google-auth`` is importable,
    otherwise fall back to a no-op stub so the rest of the app
    still boots.
    """
    try:
        pass  # type: ignore
    except Exception as exc:  # pragma: no cover - runtime fallback
        _log.warning(
            "google-auth is not installed (%s); using a permissive "
            "stub verifier until GOOGLE_CLIENT_ID is configured.",
            exc,
        )
        return StubIDTokenVerifier(
            claims=GoogleIDTokenClaims(
                sub="stub-sub",
                email="noreply@cenidim.local",
                email_verified=True,
            )
        )
    return _GoogleAuthVerifier()


@dataclass(slots=True)
class _GoogleAuthVerifier:
    async def verify(self, raw_token: str) -> GoogleIDTokenClaims:
        import os

        from google.auth.transport import requests as g_requests  # type: ignore
        from google.oauth2 import id_token as g_id_token  # type: ignore

        audience = os.environ.get("GOOGLE_CLIENT_ID", "")
        request = g_requests.Request()
        info = g_id_token.verify_token(
            raw_token, request, audience=audience
        )
        if info.get("iss") not in GOOGLE_AUDIENCES:
            raise ValueError(f"unexpected issuer: {info.get('iss')!r}")
        return GoogleIDTokenClaims(
            sub=info["sub"],
            email=info["email"],
            email_verified=bool(info.get("email_verified")),
            aud=info.get("aud", ""),
            name=info.get("name"),
            picture=info.get("picture"),
        )


__all__ = ["GOOGLE_AUDIENCES", "build_default_verifier"]
