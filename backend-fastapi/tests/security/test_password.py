"""Hash + verify helpers + JWT mint helpers (unit-level, no DB)."""
import bcrypt
import pytest

from app.security import (
    hash_password,
    verify_legacy_password,
    verify_password,
    verify_password_policy,
)


def test_password_hash_and_verify_roundtrip():
    hashed = hash_password("CorrectHorseBatteryStaple42!")
    assert verify_password_policy("CorrectHorseBatteryStaple42!") is None
    assert hashed != "CorrectHorseBatteryStaple42!"
    assert hashed.startswith("$2")


@pytest.mark.parametrize(
    "pwd,reason",
    [
        ("", "at least 8"),
        ("abc", "at least 8"),
        ("a" * 129, "at most 128"),
        ("nodigitshere", "at least one digit"),
        ("NoDigitsHere!", "at least one digit"),  # no actual digit char
    ],
)
def test_password_policy_rejects_invalid(pwd, reason):
    err = verify_password_policy(pwd)
    assert err is not None
    assert reason in err


def test_verify_password_rejects_legacy_raw_bcrypt_hash():
    """A hash produced by ``bcrypt(plain)`` (Go style) must NOT match
    the SHA-256-pre-hashed FastAPI verifier. Otherwise the fallback
    in ``authenticate`` would never trigger."""
    plain = "CorrectHorseBatteryStaple42!"
    legacy_hash = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=4)).decode("ascii")
    assert verify_password(plain, legacy_hash) is False


def test_verify_legacy_password_accepts_raw_bcrypt_hash():
    plain = "CorrectHorseBatteryStaple42!"
    legacy_hash = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=4)).decode("ascii")
    assert verify_legacy_password(plain, legacy_hash) is True
    assert verify_legacy_password("WrongPassword1", legacy_hash) is False


def test_verify_legacy_password_rejects_new_format():
    """A SHA-256-pre-hashed FastAPI hash must NOT accidentally match
    the raw-bcrypt verifier (they use different inputs)."""
    plain = "CorrectHorseBatteryStaple42!"
    new_hash = hash_password(plain)
    assert verify_legacy_password(plain, new_hash) is False


def test_verify_legacy_password_handles_malformed_hash():
    """Garbage in the hash column must not raise; treat as a non-match."""
    assert verify_legacy_password("anything1", "not-a-bcrypt-hash") is False
    assert verify_legacy_password("anything1", "") is False
