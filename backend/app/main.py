"""Common dependencies + CORS + security middleware."""
from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import Settings, get_settings
from app.db import dispose_engine, init_engine
from app.logging_config import configure_logging
from app.observability import (
    HTTP_4XX,
    HTTP_5XX,
    HTTP_LATENCY,
    HTTP_REQUESTS,
    REGISTRY,
    timed,
)
from app.routers import admin as admin_router
from app.routers import auth as auth_router
from app.routers import public as public_router
from app.security import issue_csrf_token
from app.services.email import EmailService


def create_app(settings: Settings | None = None) -> FastAPI:
    """Application factory. Phase 1 keeps a single backend with a
    deliberately small router surface; sub-routers are mounted in
    their own files.
    """
    settings = settings or get_settings()
    configure_logging(level="DEBUG" if settings.is_dev else "INFO")
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        docs_url="/docs" if not settings.is_prod else None,
        redoc_url=None,
    )
    # Only initialise the engine if one isn't already configured.
    # Tests set up an in-memory engine before calling ``create_app``
    # so they can share the same DB across the API client and direct
    # ORM access in the same test (see tests/conftest.py).
    from app.db.session import _engine

    if _engine is None:
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

    # Prometheus metrics endpoint. Served in the standard text
    # exposition format so any Prometheus-compatible scraper can
    # ingest it.
    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(
            content=REGISTRY.render(),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    # HTTP metrics middleware. Records latency + response code
    # counters labelled by method + path + status.
    @app.middleware("http")
    async def _record_metrics(request: Request, call_next):  # type: ignore[no-untyped-def]
        start = timed()
        response = await call_next(request)
        elapsed = timed() - start
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        HTTP_LATENCY.observe(elapsed)
        HTTP_REQUESTS.inc(
            method=request.method,
            path=path,
            status=str(response.status_code),
        )
        if response.status_code >= 500:
            HTTP_5XX.inc(method=request.method, path=path)
        elif response.status_code >= 400:
            HTTP_4XX.inc(method=request.method, path=path)
        return response

    # Sub-routers.
    app.include_router(auth_router.router)
    app.include_router(public_router.router)
    app.include_router(admin_router.router)

    # Tear down the DB engine on shutdown so connections close cleanly.
    @app.on_event("shutdown")
    async def _shutdown() -> None:
        await dispose_engine()

    # Schema bootstrap. In production the docker-compose db-init
    # container runs ``alembic upgrade head`` before the API starts;
    # in dev / standalone ``uvicorn`` runs we either:
    #   - apply pending migrations (when the DB exists but is stale),
    #   - or fall back to ``metadata.create_all`` for an empty DB so
    #     unit tests + integration tests don't need a migration step.
    if settings.is_dev:
        @app.on_event("startup")
        async def _bootstrap_schema() -> None:
            from sqlalchemy import inspect

            from app.db import init_engine

            engine = init_engine(settings)
            async with engine.begin() as conn:
                inspector = await conn.run_sync(inspect)
                tables = await conn.run_sync(
                    lambda sync_conn: set(inspector.get_table_names())
                )
            if tables:
                # Schema already exists; rely on alembic for changes.
                return
            from app.models import Base

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

    return app


def _ip_key(request: Request) -> str:
    """IP key for the rate limiter; respects X-Forwarded-For when set."""
    return request.headers.get("x-forwarded-for", request.client.host if request.client else "anonymous")


async def _rate_limit_handler(_request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests", "detail": str(exc)},
    )


# Module-level ASGI app so `uvicorn app.main:app` works without
# the --factory flag. Tests still build their own instances via
# ``create_app(settings)`` so per-test Settings isolation is preserved.
app = create_app()


__all__ = ["app", "create_app"]
