"""JWT helpers (issue + decode + refresh-rotation logic)."""
import pytest
from jose import JWTError

from app.security import issue_jwt


def test_jwt_roundtrip():
    token, exp = issue_jwt(
        subject=42,
        role="admin",
        ttl_seconds=60,
        secret="x" * 64,
        algorithm="HS256",
        token_type="access",
    )
    from jose import jwt
    payload = jwt.decode(token, "x" * 64, algorithms=["HS256"])
    assert payload["sub"] == 42
    assert payload["role"] == "admin"
    assert payload["type"] == "access"
    assert payload["exp"] > 0
    assert payload["iat"] > 0


def test_jwt_decode_rejects_wrong_secret():
    from jose import jwt
    token, _ = issue_jwt(
        subject=1,
        role="viewer",
        ttl_seconds=60,
        secret="a" * 64,
        algorithm="HS256",
        token_type="access",
    )
    with pytest.raises(JWTError):
        jwt.decode(token, "b" * 64, algorithms=["HS256"])


def test_jwt_extra_payload_merges_with_claims():
    token, _ = issue_jwt(
        subject=7,
        role="editor",
        ttl_seconds=30,
        secret="c" * 64,
        algorithm="HS256",
        token_type="refresh",
        extra={"family_id": 99},
    )
    from jose import jwt
    payload = jwt.decode(token, "c" * 64, algorithms=["HS256"])
    assert payload["family_id"] == 99
    assert payload["type"] == "refresh"


def test_jwt_emits_unique_jti_per_issue():
    seen = set()
    for _ in range(5):
        token, _ = issue_jwt(
            subject=1,
            role="viewer",
            ttl_seconds=60,
            secret="d" * 64,
            algorithm="HS256",
            token_type="access",
        )
        from jose import jwt
        claims = jwt.decode(token, "d" * 64, algorithms=["HS256"])
        seen.add(claims["jti"])
    assert len(seen) == 5
