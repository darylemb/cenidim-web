"""User management DTOs for the admin router."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints

from app.models.user import User

RoleLiteral = Literal["viewer", "editor", "admin"]

UsernameStr = Annotated[
    str, StringConstraints(min_length=3, max_length=32, strip_whitespace=True)
]
PlainPassword = Annotated[
    str, StringConstraints(min_length=8, max_length=128, strip_whitespace=False)
]


class UserOut(BaseModel):
    """Response shape for ``GET /api/admin/users`` and friends."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    role: str
    version: int = 0
    created_at: datetime
    last_sign_in_method: str | None = None
    last_sign_in_at: datetime | None = None


class UserCreateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: UsernameStr
    email: EmailStr
    password: PlainPassword
    role: RoleLiteral | None = None


class UserUpdateIn(BaseModel):
    """PATCH-style update. All fields are optional; only non-empty
    ones are written (matches the Go PUT behaviour).
    """
    model_config = ConfigDict(extra="forbid")

    username: UsernameStr | None = None
    email: EmailStr | None = None
    password: PlainPassword | None = None
    role: RoleLiteral | None = None


class UserCreateOut(BaseModel):
    """The ``POST /api/admin/users`` response envelope."""
    user: UserOut


class UserCreatedResponse(BaseModel):
    """Generic 200/201 envelope used by PUT / DELETE."""
    message: str


def user_to_out(user: User) -> UserOut:
    return UserOut.model_validate(user)


__all__ = [
    "PlainPassword",
    "RoleLiteral",
    "UserCreateIn",
    "UserCreateOut",
    "UserCreatedResponse",
    "UserOut",
    "UserUpdateIn",
    "UsernameStr",
    "user_to_out",
]
