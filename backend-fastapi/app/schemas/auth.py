"""Auth request / response DTOs."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import User


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=128)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    role: str
    created_at: datetime


class AuthResponse(BaseModel):
    user: UserOut


class ForgotPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class ForgotPasswordResponse(BaseModel):
    ok: bool = True
    dev_link: str | None = None


class LinkGoogleIdentityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: int
    subject: str
    email_at_link: EmailStr


def user_to_out(user: User) -> UserOut:
    return UserOut.model_validate(user)


__all__ = [
    "AuthResponse",
    "ForgotPasswordRequest",
    "ForgotPasswordResponse",
    "LinkGoogleIdentityRequest",
    "LoginRequest",
    "RegisterRequest",
    "ResetPasswordRequest",
    "UserOut",
    "user_to_out",
]
