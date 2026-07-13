"""HTTP routers for /api/auth/*."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from app.config import Settings, get_settings
from app.deps import DbDep, issue_access_token
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    user_to_out,
)
from app.security import (
    issue_csrf_token,
    issue_jwt,
)
from app.services.auth import AuthError, authenticate, register_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: DbDep,
    settings: Settings = Depends(get_settings),
) -> AuthResponse:
    try:
        user = await authenticate(db, username=body.username, password=body.password)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    _set_session_cookies(response, user, settings)
    user.last_sign_in_method = "password"
    await db.flush()
    return AuthResponse(user=user_to_out(user))


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    body: RegisterRequest,
    response: Response,
    db: DbDep,
    settings: Settings = Depends(get_settings),
) -> AuthResponse:
    try:
        user = await register_user(
            db,
            username=body.username,
            email=str(body.email),
            password=body.password,
            settings=settings,
        )
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    _set_session_cookies(response, user, settings)
    return AuthResponse(user=user_to_out(user))


@router.post("/forgot", response_model=ForgotPasswordResponse)
async def forgot(
    body: ForgotPasswordRequest,
    db: DbDep,
    settings: Settings = Depends(get_settings),
) -> ForgotPasswordResponse:
    # Always 200; the email-existence check happens server-side and
    # is silent. The dev-mode flag returns the link in the body.
    from app.services.auth import request_password_reset

    try:
        dev_link, _err = await request_password_reset(
            db, email=str(body.email), settings=settings
        )
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return ForgotPasswordResponse(ok=True, dev_link=dev_link)


@router.post("/reset")
async def reset(
    body: ResetPasswordRequest,
    db: DbDep,
) -> dict[str, bool]:
    from app.services.auth import consume_password_reset

    try:
        await consume_password_reset(
            db, token=body.token, new_password=body.new_password
        )
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail)
    return {"ok": True}


@router.post("/logout")
async def logout(response: Response) -> dict[str, bool]:
    _clear_session_cookies(response)
    return {"ok": True}


def _set_session_cookies(response: Response, user: User, settings: Settings) -> None:
    """Attach the HttpOnly access + refresh cookies + the CSRF seed."""
    access, access_exp = issue_access_token(user, settings)
    refresh, refresh_exp = issue_jwt(
        subject=user.id,
        role=user.role,
        ttl_seconds=settings.jwt_refresh_ttl_seconds,
        secret=settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
        token_type="refresh",  # noqa: S106
    )
    response.set_cookie(
        "cenidim_session",
        access,
        max_age=settings.jwt_access_ttl_seconds,
        httponly=True,
        secure=settings.is_prod,
        samesite="strict",
        path="/",
    )
    response.set_cookie(
        "cenidim_refresh",
        refresh,
        max_age=settings.jwt_refresh_ttl_seconds,
        httponly=True,
        secure=settings.is_prod,
        samesite="strict",
        path="/api/auth/refresh",
    )
    response.set_cookie(
        "cenidim_csrf",
        issue_csrf_token(),
        max_age=60 * 60 * 24,
        httponly=False,
        secure=settings.is_prod,
        samesite="strict",
        path="/",
    )


def _clear_session_cookies(response: Response) -> None:
    response.delete_cookie("cenidim_session")
    response.delete_cookie("cenidim_refresh", path="/api/auth/refresh")
    response.delete_cookie("cenidim_csrf", path="/")


__all__ = ["router"]
