"""Tests for app.db.session.session_scope_cm context manager."""
from __future__ import annotations

import pytest

from app import db as db_module
from app.db import init_in_memory_engine, session_scope_cm


@pytest.mark.asyncio
async def test_session_scope_cm_commits_on_clean_exit(db_session):
    from sqlalchemy import text as sa_text

    init_in_memory_engine()
    async with session_scope_cm() as session:
        await session.execute(sa_text("CREATE TABLE cm_t (x INTEGER)"))
        await session.execute(sa_text("INSERT INTO cm_t VALUES (1)"))
    # Verify the table is queryable in a new session
    sm = db_module.session.get_sessionmaker()
    async with sm() as session:
        result = (
            await session.execute(sa_text("SELECT x FROM cm_t"))
        ).scalar_one()
    assert result == 1
