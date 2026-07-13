"""Database engine + session management.

Importing the submodule initialises the SQLAlchemy declarative base
once. ``app.db.session`` provides the engine lifecycle helpers.
"""
from app.db.base import Base, TimestampMixin
from app.db.session import (
    dispose_engine,
    get_sessionmaker,
    init_engine,
    init_in_memory_engine,
    session_scope,
)

__all__ = [
    "Base",
    "TimestampMixin",
    "dispose_engine",
    "get_sessionmaker",
    "init_engine",
    "init_in_memory_engine",
    "session_scope",
]
