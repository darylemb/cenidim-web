"""Common dependencies + CORS + security middleware."""
from __future__ import annotations

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import Settings, get_settings
from app.db import dispose_engine, init_engine
from app.security import issue_csrf_token
from app.services.email import EmailService


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory. Phase 1 keeps a single backend with a
    deliberately small router surface; sub-routers are mounted in
    their own files.
    """
    settings = settings or get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url="/docs" if not settings.is_prod else None,
        redoc_url=None,
    )
    init_engine(settings)
    EmailService.configure(settings)

    # CORS — strict allowlist. Wildcard is intentionally disabled.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
        max_age=600,
    )

    # Rate limit middleware. Per-route limits are applied inside each
    # router via @limiter.limit("X/period").
    limiter = Limiter(key_func=_ip_key, default_limits=[])
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

    # CSRF seed cookie. The client reads this and echoes it as
    # X-CSRF-Token on every mutating request.
    @app.middleware("http")
    async def _csrf_seed(request: Request, call_next):
        # Refresh the seed whenever the page is loaded.
        existing = request.cookies.get("cenidim_csrf")
        if not existing:
            token = issue_csrf_token()
            request.state.csrf_seed = token
        else:
            request.state.csrf_seed = existing
        response: object = await call_next(request)
        if isinstance(response, JSONResponse) and not request.cookies.get(
            "cenidim_csrf"
        ):
            response.set_cookie(
                "cenidim_csrf",
                getattr(request.state, "csrf_seed", ""),
                httponly=False,  # JS must read it
                secure=settings.is_prod,
                samesite="strict",
                path="/",
            )
        return response

    # Healthcheck endpoint used by Docker / Coolify.
    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    # Tear down the DB engine on shutdown so connections close cleanly.
    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await dispose_engine()

    return app


def _ip_key(request: Request) -> str:
    """IP key for the rate limiter; respects X-Forwarded-For when set."""
    return request.headers.get("x-forwarded-for", request.client.host if request.client else "anonymous")


async def _rate_limit_handler(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests", "detail": str(exc)},
    )


__all__ = ["create_app"]
