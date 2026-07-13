"""Application settings, loaded from environment variables via
``pydantic-settings``.

The single ``Settings`` instance is created at process start and
shared by routers, services and security helpers via ``get_settings()``.
Settings are intentionally explicit (no nested ``model_config`` magic)
so the configuration surface is easy to audit.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration in one place.

    Environment variables use the ``CENIDIM_`` prefix by default so they
    don't collide with system vars. See ``docker-compose.yml`` for the
    full mapping used in production.
    """

    model_config = SettingsConfigDict(
        env_prefix="CENIDIM_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- runtime ---
    env: Literal["dev", "prod"] = "dev"
    app_name: str = "CENIDIM API"
    debug: bool = False

    # --- database ---
    db_path: Path = Path("letras.db")
    db_echo: bool = False
    db_pool_size: int = 5

    # --- JWT / CSRF ---
    jwt_secret: SecretStr = SecretStr("change-me-in-production-please-32-chars")
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_seconds: int = 60 * 60 * 24          # 24 h
    jwt_refresh_ttl_seconds: int = 60 * 60 * 24 * 7     # 7 d

    # --- CORS ---
    cors_origin_env: str = ""  # populated from CORS_ALLOWED_ORIGINS by main
    cors_allow_credentials: bool = True

    # --- email ---
    email_provider: Literal["resend", "outbox"] = "outbox"
    resend_api_key: SecretStr = SecretStr("")
    email_from: str = "no-reply@cenidim.local"
    email_demo_print_body: bool = False
    frontend_base_url: str = "http://localhost:3000"

    # --- rate limiting ---
    rate_limit_default: str = "60/minute"
    rate_limit_login: str = "5/minute"
    rate_limit_forgot: str = "3/minute"

    # --- audit log retention (days) ---
    audit_log_retention_days: int = 30

    # --- admin bootstrap (creates first superuser on startup) ---
    admin_bootstrap_username: str = "admin"
    admin_bootstrap_email: str = "admin@cenidim.local"
    admin_bootstrap_password: str = "ChangeMe!23"

    # --- derived properties -------------------------------------------------

    @property
    def is_dev(self) -> bool:
        return self.env == "dev"

    @property
    def is_prod(self) -> bool:
        return self.env == "prod"

    @property
    def db_url(self) -> str:
        """SQLAlchemy async URL for the configured sqlite file."""
        return f"sqlite+aiosqlite:///{self.db_path}"

    @property
    def cors_origin_list(self) -> list[str]:
        """Allow-list of origins, sourced from the ``CORS_ALLOWED_ORIGINS``
        environment variable (comma-separated). Falls back to the local
        trio used by the Go backend in dev.
        """
        # Allow non-prefixed var to play nicely with the Go backend's
        # CORS config without forcing every operator to re-export.
        raw = os.environ.get(
            "CORS_ALLOWED_ORIGINS",
            self.cors_origin_env,
            # The ``or`` keeps an empty string from leaking through as
            # a single empty origin, which Starlette treats as "same
            # origin" and refuses.
        )
        if isinstance(raw, str) and raw.strip():
            return [o.strip() for o in raw.split(",") if o.strip()]
        return [
            "http://localhost",
            "http://localhost:3000",
            "http://localhost:8000",
        ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached factory so we instantiate the model exactly once."""
    return Settings()


__all__ = ["Settings", "get_settings"]
