"""HTTP routers for /api/auth/*."""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from jose import JWTError, jwt
from sqlalchemy import select

from app.config import Settings, get_settings
from app.deps import DbDep, issue_access_token
from app.models.refresh_revocation import RefreshTokenRevocation
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
async def logout(
    request: Request,
    response: Response,
    db: DbDep,
    settings: Settings = Depends(get_settings),
) -> dict[str, bool]:
    """Revoke the current refresh token (if any) and clear cookies."""
    refresh = request.cookies.get("cenidim_refresh")
    if refresh:
        try:
            claims = jwt.decode(
                refresh,
                settings.jwt_secret.get_secret_value(),
                algorithms=[settings.jwt_algorithm],
            )
        except JWTError:
            claims = None
        if claims:
            sub = claims.get("sub")
            jti = claims.get("jti")
            exp_ts = claims.get("exp")
            try:
                sub_int = int(sub) if sub is not None else None
            except (TypeError, ValueError):
                sub_int = None
            if (
                isinstance(sub_int, int)
                and isinstance(jti, str)
                and isinstance(exp_ts, int)
            ):
                db.add(
                    RefreshTokenRevocation(
                        jti=jti,
                        user_id=sub_int,
                        reason="logout",
                        expires_at=datetime.fromtimestamp(exp_ts, UTC),
                    )
                )
                await db.flush()
    _clear_session_cookies(response)
    return {"ok": True}


@router.post("/refresh", response_model=AuthResponse)
async def refresh(
    request: Request,
    response: Response,
    db: DbDep,
    settings: Settings = Depends(get_settings),
) -> AuthResponse:
    """Rotate the refresh token. Old ``jti`` is recorded as
    revoked so any future reuse returns 401.
    """
    refresh_cookie = request.cookies.get("cenidim_refresh")
    if not refresh_cookie:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    try:
        claims = jwt.decode(
            refresh_cookie,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")
    if claims.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Wrong token type")
    sub = claims.get("sub")
    jti = claims.get("jti")
    exp_ts = claims.get("exp")
    # python-jose returns ``sub`` as str; the rest come back as their
    # original types. We coerce ``sub`` to int and require ``jti`` /
    # ``exp`` to be present and of the expected types.
    try:
        sub_int = int(sub) if sub is not None else None
    except (TypeError, ValueError):
        sub_int = None
    if not (
        isinstance(sub_int, int)
        and isinstance(jti, str)
        and isinstance(exp_ts, int)
    ):
        raise HTTPException(status_code=401, detail="Malformed refresh claims")

    # Reject if the jti has been revoked (e.g. by a previous /refresh).
    revoked = (
        await db.execute(
            select(RefreshTokenRevocation).where(RefreshTokenRevocation.jti == jti)
        )
    ).scalar_one_or_none()
    if revoked is not None:
        raise HTTPException(status_code=401, detail="Refresh revoked")

    user = (
        await db.execute(select(User).where(User.id == sub_int))
    ).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User no longer exists")

    # Record the old jti and issue a fresh pair.
    db.add(
        RefreshTokenRevocation(
            jti=jti,
            user_id=sub_int,
            reason="rotated",
            expires_at=datetime.fromtimestamp(exp_ts, UTC),
        )
    )
    _set_session_cookies(response, user, settings)
    return AuthResponse(user=user_to_out(user))


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
