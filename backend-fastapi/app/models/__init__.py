"""SQLAlchemy ORM models mirroring the Go (cmd/build-db) schema.

Column names use snake_case to match the existing ``letras.db`` exactly
so the FastAPI backend can run against the Go-produced database
without a migration. Default values mirror the Go CREATE TABLEs.
"""
from app.db.base import Base, TimestampMixin
from app.models.audit_log import AuditLog
from app.models.email_outbox import EmailOutbox
from app.models.fonograma import Fonograma
from app.models.password_reset_token import PasswordResetToken
from app.models.refresh_revocation import RefreshTokenRevocation
from app.models.song import Song
from app.models.song_stats import SongStats
from app.models.user import User

__all__ = [
    "AuditLog",
    "Base",
    "EmailOutbox",
    "Fonograma",
    "PasswordResetToken",
    "RefreshTokenRevocation",
    "Song",
    "SongStats",
    "TimestampMixin",
    "User",
]
