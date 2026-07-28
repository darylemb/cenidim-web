"""Auth service unit tests: register / login / password reset."""
from __future__ import annotations

import pytest

from app import db as db_module
from app.services.auth import (
    AuthError,
    authenticate,
    consume_password_reset,
    issue_session,
    register_user,
    request_password_reset,
)


def _session():
    """Hand back a fresh AsyncSession on the in-memory engine."""
    return db_module.session.get_sessionmaker()()


@pytest.mark.asyncio
async def test_register_user_happy_path(db_session, settings):
    async with _session() as session:
        user = await register_user(
            session,
            username="alice",
            email="alice@cenidim.example",
            password="Strong1234",
            settings=settings,
        )
        assert user.id is not None
        assert user.username == "alice"
        assert user.role == "viewer"


@pytest.mark.asyncio
async def test_register_user_rejects_weak_password(db_session, settings):
    async with _session() as session:
        with pytest.raises(AuthError) as exc:
            await register_user(
                session,
                username="bob",
                email="bob@cenidim.example",
                password="nodigits",
                settings=settings,
            )
        assert exc.value.status_code == 400
        assert "digit" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_register_user_rejects_duplicate(db_session, settings):
    async with _session() as session:
        await register_user(
            session,
            username="carol",
            email="carol@cenidim.example",
            password="Strong1234",
            settings=settings,
        )
        with pytest.raises(AuthError) as exc:
            await register_user(
                session,
                username="carol",
                email="carol@cenidim.example",
                password="Different1",
                settings=settings,
            )
        assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_authenticate_round_trip(db_session, settings):
    async with _session() as session:
        await register_user(
            session,
            username="dave",
            email="dave@cenidim.example",
            password="Strong1234",
            settings=settings,
        )
        user = await authenticate(session, username="dave", password="Strong1234")
        assert user.username == "dave"


@pytest.mark.asyncio
async def test_authenticate_rejects_bad_password(db_session, settings):
    async with _session() as session:
        await register_user(
            session,
            username="eve",
            email="eve@cenidim.example",
            password="Strong1234",
            settings=settings,
        )
        with pytest.raises(AuthError) as exc:
            await authenticate(
                session, username="eve", password="WrongPass1"
            )
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_authenticate_accepts_legacy_go_bcrypt_hash_and_rehashes(
    db_session, settings
):
    """Users seeded by the Go db-init have raw ``bcrypt(plain)`` hashes.

    ``authenticate`` must accept them so the cut-over does not lock
    out the admin. On a legacy match the hash is upgraded to the
    FastAPI scheme so the next login uses the fast path.
    """
    import bcrypt as _bcrypt

    from app.models.user import User
    from app.security import hash_password, verify_password

    plain = "LegacyGoPass123"
    legacy_hash = _bcrypt.hashpw(
        plain.encode("utf-8"), _bcrypt.gensalt(rounds=4)
    ).decode("ascii")

    async with _session() as session:
        session.add(
            User(
                username="legacyuser",
                email="legacy@cenidim.example",
                password_hash=legacy_hash,
                role="viewer",
            )
        )
        await session.commit()

        user = await authenticate(
            session, username="legacyuser", password=plain
        )
        assert user.username == "legacyuser"

        # The legacy match must have triggered an opportunistic rehash.
        assert user.password_hash != legacy_hash
        assert user.password_hash.startswith("$2")
        assert verify_password(plain, user.password_hash) is True
        # And the upgrade must persist so the next login uses the fast path.
        await session.commit()
        await session.refresh(user)
        assert verify_password(plain, user.password_hash) is True

    async with _session() as session:
        # A second login must succeed via the new hash (no legacy
        # fallback needed).
        user = await authenticate(
            session, username="legacyuser", password=plain
        )
        assert user.username == "legacyuser"
        assert user.password_hash == hash_password(plain) or user.password_hash.startswith(
            "$2"
        )


@pytest.mark.asyncio
async def test_authenticate_legacy_fallback_rejects_wrong_password(
    db_session, settings
):
    """The legacy fallback must NOT widen the false-positive window.

    A wrong password against a legacy hash still fails 401, even
    though the verifier path differs.
    """
    import bcrypt as _bcrypt

    from app.models.user import User

    legacy_hash = _bcrypt.hashpw(
        b"CorrectPassword1", _bcrypt.gensalt(rounds=4)
    ).decode("ascii")

    async with _session() as session:
        session.add(
            User(
                username="legacyguard",
                email="legacyguard@cenidim.example",
                password_hash=legacy_hash,
                role="viewer",
            )
        )
        await session.commit()

        with pytest.raises(AuthError) as exc:
            await authenticate(
                session, username="legacyguard", password="WrongPassword1"
            )
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_issue_session_mints_both_tokens(db_session, settings):
    async with _session() as session:
        user = await register_user(
            session,
            username="frank",
            email="frank@cenidim.example",
            password="Strong1234",
            settings=settings,
        )
        await session.commit()
        await session.refresh(user)

    tokens = issue_session(user, settings)
    assert set(tokens) == {"access", "refresh"}
    access_token, _ = tokens["access"]
    refresh_token, _ = tokens["refresh"]
    from jose import jwt

    a = jwt.decode(
        access_token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )
    assert a["type"] == "access"
    assert int(a["sub"]) == user.id
    r = jwt.decode(
        refresh_token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )
    assert r["type"] == "refresh"


@pytest.mark.asyncio
async def test_request_password_reset_returns_no_link_when_demo_disabled(
    db_session, settings
):
    settings.email_demo_print_body = False
    async with _session() as session:
        await register_user(
            session,
            username="i",
            email="i@cenidim.example",
            password="Strong1234",
            settings=settings,
        )
        await session.commit()
    async with _session() as session:
        dev_link, err = await request_password_reset(
            session,
            email="i@cenidim.example",
            settings=settings,
        )
    assert dev_link is None
    assert err is None


@pytest.mark.asyncio
async def test_consume_password_reset_rejects_bad_token(db_session, settings):
    async with _session() as session:
        with pytest.raises(AuthError) as exc:
            await consume_password_reset(
                session,
                token="never-issued-token",
                new_password="NewSecret123",
            )
        assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_consume_password_reset_rejects_weak_password(db_session, settings):
    settings.email_demo_print_body = True
    async with _session() as session:
        await register_user(
            session,
            username="g",
            email="g@cenidim.example",
            password="Strong1234",
            settings=settings,
        )
        dev_link, _ = await request_password_reset(
            session,
            email="g@cenidim.example",
            settings=settings,
        )
        token = dev_link.split("token=")[1]
    async with _session() as session:
        with pytest.raises(AuthError) as exc:
            await consume_password_reset(
                session,
                token=token,
                new_password="nodigits",
            )
        assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_consume_password_reset_rejects_double_use(db_session, settings):
    settings.email_demo_print_body = True
    async with _session() as session:
        await register_user(
            session,
            username="h",
            email="h@cenidim.example",
            password="Strong1234",
            settings=settings,
        )
        await session.commit()
    async with _session() as session:
        dev_link, _ = await request_password_reset(
            session,
            email="h@cenidim.example",
            settings=settings,
        )
        await session.commit()
    token = dev_link.split("token=")[1]
    async with _session() as session:
        await consume_password_reset(
            session, token=token, new_password="BrandNew1234"
        )
        await session.commit()

    from app.db import session_scope_cm

    raised: AuthError | None = None
    async with session_scope_cm() as session:
        try:
            await consume_password_reset(
                session, token=token, new_password="BrandNew1234"
            )
        except AuthError as exc:
            raised = exc
    assert raised is not None
    assert raised.status_code == 401


def test_verify_bcrypt_safe_rejects_malformed_hash():
    """Garbage in the DB (e.g. legacy 'GOOGLE_LINKED' row) must
    fail closed instead of raising.
    """
    from app.services.auth import _verify_bcrypt_safe

    assert _verify_bcrypt_safe("any-token", "not-a-bcrypt-hash") is False


def test_verify_bcrypt_safe_accepts_matching_token():
    from app.security import generate_reset_token
    from app.services.auth import _verify_bcrypt_safe

    plain, hashed = generate_reset_token()
    assert _verify_bcrypt_safe(plain, hashed) is True


def test_verify_bcrypt_safe_rejects_wrong_token():
    from app.security import generate_reset_token
    from app.services.auth import _verify_bcrypt_safe

    _, hashed = generate_reset_token()
    assert _verify_bcrypt_safe("nope", hashed) is False
