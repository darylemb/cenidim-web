"""Hash + verify helpers + JWT mint helpers (unit-level, no DB)."""
import pytest

from app.security import hash_password, verify_password_policy


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
        ("1n0digit5", "at least one digit"),  # has 'n' digit but no actual digit char
    ],
)
def test_password_policy_rejects_invalid(pwd, reason):
    err = verify_password_policy(pwd)
    assert err is not None
    assert reason in err
