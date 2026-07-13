"""Factory-boy factories + a few helpers for HTTP tests."""
from __future__ import annotations

import secrets

import factory

from app.models.user import User


class UserFactory(factory.Factory):
    """Build a User row in memory (no DB write)."""

    class Meta:
        model = User

    id = factory.Sequence(lambda n: n)
    username = factory.LazyAttribute(lambda o: f"user{o.id}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@cenidim.test")
    password_hash = factory.LazyAttribute(lambda o: f"hash:{secrets.token_hex(16)}")
    role = "viewer"
    version = 0
