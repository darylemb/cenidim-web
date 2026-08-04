"""Admin CRUD: fonogramas, songs, users, identities, audit log, email outbox.

Role tiers (from the Go ``RequireRole`` middleware):
  viewer  - can read everything under /api/admin/*
  editor  - can create/update fonogramas + songs
  admin   - can delete fonogramas + songs and full user CRUD

The router deliberately mirrors the Go ``handlers/admin.go`` surface
so the FastAPI cutover (Phase 7 in the master plan) is a clean swap.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import DbDep, require_role
from app.models.audit_log import AuditLog
from app.models.email_outbox import EmailOutbox
from app.models.fonograma import Fonograma
from app.models.song import Song
from app.models.user import User
from app.schemas.song import (
    FonogramaOut,
    SongCreateIn,
    SongOut,
    SongUpdateIn,
    fonograma_to_out,
    song_to_out,
)
from app.schemas.stats import PaginatedResponse
from app.schemas.user import (
    UserCreatedResponse,
    UserCreateIn,
    UserCreateOut,
    UserOut,
    UserUpdateIn,
    user_to_out,
)
from app.security import hash_password, verify_password_policy

router = APIRouter(prefix="/api/admin", tags=["admin"])
_log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _record_audit(
    db: AsyncSession,
    *,
    actor_id: int | None,
    action: str,
    target_type: str | None = None,
    target_id: int | None = None,
    detail: str | None = None,
) -> None:
    """Append an audit_log row. Failures are logged but never raised."""
    try:
        db.add(
            AuditLog(
                actor_id=actor_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                detail=detail,
                occurred_at=datetime.now(UTC),
            )
        )
        await db.flush()
    except Exception as exc:  # noqa: BLE001  - audit must never break the request
        _log.warning("AuditLog insert failed for action=%s: %s", action, exc)


def _clave_fonograma_param(
    id: int = Path(ge=1, description="clave_fonograma"),
) -> int:
    return id


def _song_id_param(id: int = Path(ge=1, description="song id")) -> int:
    return id


def _user_id_param(id: int = Path(ge=1, description="user id")) -> int:
    return id


# ---------------------------------------------------------------------------
# Fonogramas
# ---------------------------------------------------------------------------


@router.get("/fonogramas", response_model=PaginatedResponse)
async def admin_list_fonogramas(
    db: DbDep,
    _: User = Depends(require_role("viewer")),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=200),
) -> dict[str, Any]:
    total = (await db.execute(select(func.count()).select_from(Fonograma))).scalar_one()
    rows = (
        await db.execute(
            select(Fonograma)
            .order_by(Fonograma.clave_fonograma)
            .offset((page - 1) * limit)
            .limit(limit)
        )
    ).scalars().all()
    return {
        "results": [fonograma_to_out(f).model_dump() for f in rows],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/fonogramas/{id}", response_model=FonogramaOut)
async def admin_get_fonograma(
    db: DbDep,
    id: Annotated[int, _clave_fonograma_param],
    _: User = Depends(require_role("viewer")),
) -> Fonograma:
    row = (
        await db.execute(
            select(Fonograma).where(Fonograma.clave_fonograma == id)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Fonograma not found")
    return row


@router.post(
    "/fonogramas", response_model=FonogramaOut, status_code=status.HTTP_201_CREATED
)
async def admin_create_fonograma(
    db: DbDep,
    body: FonogramaOut,
    actor: User = Depends(require_role("editor")),
) -> Fonograma:
    row = Fonograma(
        clave_fonograma=body.clave_fonograma,
        titulo=body.titulo,
        subtitulo=body.subtitulo,
        interprete_principal=body.interprete_principal,
        interpretes_invitados=body.interpretes_invitados,
        interprete_participante=body.interprete_participante,
        soporte_fisico=body.soporte_fisico,
        editora=body.editora,
        numero_catalogo=body.numero_catalogo,
        ciudad_edicion=body.ciudad_edicion,
        pais_edicion=body.pais_edicion,
        anio=body.anio,
        pistas=body.pistas,
        observaciones=body.observaciones,
    )
    db.add(row)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ClaveFonograma already exists or invalid data",
        ) from exc
    await _record_audit(
        db,
        actor_id=actor.id,
        action="fonograma.create",
        target_type="fonograma",
        target_id=row.clave_fonograma,
        detail=f"titulo={row.titulo!r}",
    )
    return row


@router.put("/fonogramas/{id}", response_model=FonogramaOut)
async def admin_update_fonograma(
    db: DbDep,
    body: FonogramaOut,
    id: Annotated[int, _clave_fonograma_param],
    actor: User = Depends(require_role("editor")),
) -> Fonograma:
    existing = (
        await db.execute(
            select(Fonograma).where(Fonograma.clave_fonograma == id)
        )
    ).scalar_one_or_none()
    if existing is None:
        raise HTTPException(status_code=404, detail="Fonograma not found")
    # The Go handler ignores the body's ``clave_fonograma`` and uses
    # only the path parameter. We mirror that to keep callers happy.
    existing.titulo = body.titulo
    existing.subtitulo = body.subtitulo
    existing.interprete_principal = body.interprete_principal
    existing.interpretes_invitados = body.interpretes_invitados
    existing.interprete_participante = body.interprete_participante
    existing.soporte_fisico = body.soporte_fisico
    existing.editora = body.editora
    existing.numero_catalogo = body.numero_catalogo
    existing.ciudad_edicion = body.ciudad_edicion
    existing.pais_edicion = body.pais_edicion
    existing.anio = body.anio
    existing.pistas = body.pistas
    existing.observaciones = body.observaciones
    existing.version = (existing.version or 0) + 1
    await db.flush()
    await _record_audit(
        db,
        actor_id=actor.id,
        action="fonograma.update",
        target_type="fonograma",
        target_id=existing.clave_fonograma,
    )
    return existing


@router.delete("/fonogramas/{id}", response_model=UserCreatedResponse)
async def admin_delete_fonograma(
    db: DbDep,
    id: Annotated[int, _clave_fonograma_param],
    actor: User = Depends(require_role("admin")),
) -> UserCreatedResponse:
    # Manual cascade: drop songs first so SQLAlchemy doesn't fight
    # the FK ON DELETE CASCADE that the Go migration creates.
    await db.execute(delete(Song).where(Song.fonograma_id == id))
    result = await db.execute(
        delete(Fonograma).where(Fonograma.clave_fonograma == id)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Fonograma not found")
    await _record_audit(
        db,
        actor_id=actor.id,
        action="fonograma.delete",
        target_type="fonograma",
        target_id=id,
    )
    return UserCreatedResponse(message="Fonograma deleted")


# ---------------------------------------------------------------------------
# Songs
# ---------------------------------------------------------------------------


@router.get("/songs", response_model=PaginatedResponse)
async def admin_list_songs(
    db: DbDep,
    _: User = Depends(require_role("viewer")),
    fonograma_id: int | None = Query(default=None, ge=1),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
) -> dict[str, Any]:
    base = (
        select(Song, Fonograma)
        .join(Fonograma, Song.fonograma_id == Fonograma.clave_fonograma)
    )
    count_q = select(func.count()).select_from(Song)
    if fonograma_id is not None:
        base = base.where(Song.fonograma_id == fonograma_id)
        count_q = count_q.where(Song.fonograma_id == fonograma_id)
    total = (await db.execute(count_q)).scalar_one()
    rows = (
        await db.execute(
            base.order_by(Song.id)
            .offset((page - 1) * limit)
            .limit(limit)
        )
    ).all()
    results = [song_to_out(song, fonograma).model_dump() for song, fonograma in rows]
    return {
        "results": results,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post(
    "/songs",
    response_model=SongOut,
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_song(
    db: DbDep,
    body: SongCreateIn,
    actor: User = Depends(require_role("editor")),
) -> Song:
    row = Song(
        fonograma_id=body.fonograma_id,
        title=body.title,
        lyrics=body.lyrics,
    )
    db.add(row)
    await db.flush()
    await _record_audit(
        db,
        actor_id=actor.id,
        action="song.create",
        target_type="song",
        target_id=row.id,
        detail=f"title={row.title!r}",
    )
    return row


@router.put("/songs/{id}", response_model=UserCreatedResponse)
async def admin_update_song(
    db: DbDep,
    body: SongUpdateIn,
    id: Annotated[int, _song_id_param],
    actor: User = Depends(require_role("editor")),
) -> UserCreatedResponse:
    existing = (
        await db.execute(select(Song).where(Song.id == id))
    ).scalar_one_or_none()
    if existing is None:
        raise HTTPException(status_code=404, detail="Song not found")
    if body.title is not None and body.title.strip():
        existing.title = body.title
    if body.lyrics is not None:
        existing.lyrics = body.lyrics
    existing.version = (existing.version or 0) + 1
    await db.flush()
    await _record_audit(
        db,
        actor_id=actor.id,
        action="song.update",
        target_type="song",
        target_id=existing.id,
    )
    return UserCreatedResponse(message="Song updated")


@router.delete("/songs/{id}", response_model=UserCreatedResponse)
async def admin_delete_song(
    db: DbDep,
    id: Annotated[int, _song_id_param],
    actor: User = Depends(require_role("admin")),
) -> UserCreatedResponse:
    result = await db.execute(delete(Song).where(Song.id == id))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Song not found")
    await _record_audit(
        db,
        actor_id=actor.id,
        action="song.delete",
        target_type="song",
        target_id=id,
    )
    return UserCreatedResponse(message="Song deleted")


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@router.get("/users", response_model=list[UserOut])
async def admin_list_users(
    db: DbDep,
    _: User = Depends(require_role("admin")),
) -> list[User]:
    rows = (await db.execute(select(User).order_by(User.id))).scalars().all()
    return list(rows)


@router.post(
    "/users", response_model=UserCreateOut, status_code=status.HTTP_201_CREATED
)
async def admin_create_user(
    db: DbDep,
    body: UserCreateIn,
    actor: User = Depends(require_role("admin")),
) -> UserCreateOut:
    # Belt-and-braces: middleware already enforces admin; the in-handler
    # check matches the Go admin handler.
    if actor.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create users")
    err = verify_password_policy(body.password)
    if err is not None:
        raise HTTPException(status_code=400, detail=err)
    role_value = body.role or "viewer"
    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        role=role_value,
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Username or email already exists") from exc
    await _record_audit(
        db,
        actor_id=actor.id,
        action="user.create",
        target_type="user",
        target_id=user.id,
        detail=f"username={user.username!r} role={user.role}",
    )
    return UserCreateOut(user=user_to_out(user))


@router.put("/users/{id}", response_model=UserCreatedResponse)
async def admin_update_user(
    db: DbDep,
    body: UserUpdateIn,
    id: Annotated[int, _user_id_param],
    actor: User = Depends(require_role("admin")),
) -> UserCreatedResponse:
    existing = (
        await db.execute(select(User).where(User.id == id))
    ).scalar_one_or_none()
    if existing is None:
        raise HTTPException(status_code=404, detail="User not found")

    updates: list[str] = []
    if body.password is not None and body.password:
        err = verify_password_policy(body.password)
        if err is not None:
            raise HTTPException(status_code=400, detail=err)
        existing.password_hash = hash_password(body.password)
        updates.append("password")
    if body.username is not None and body.username:
        existing.username = body.username
        updates.append("username")
    if body.email is not None and body.email:
        existing.email = body.email
        updates.append("email")
    if body.role is not None and body.role:
        existing.role = body.role
        updates.append("role")
    existing.version = (existing.version or 0) + 1
    await db.flush()
    if updates:
        await _record_audit(
            db,
            actor_id=actor.id,
            action="user.update",
            target_type="user",
            target_id=existing.id,
            detail=",".join(updates),
        )
    return UserCreatedResponse(message="User updated")


@router.delete("/users/{id}", response_model=UserCreatedResponse)
async def admin_delete_user(
    db: DbDep,
    id: Annotated[int, _user_id_param],
    actor: User = Depends(require_role("admin")),
) -> UserCreatedResponse:
    existing = (
        await db.execute(select(User).where(User.id == id))
    ).scalar_one_or_none()
    if existing is None:
        raise HTTPException(status_code=404, detail="User not found")
    if existing.role == "admin":
        admin_count = (
            await db.execute(
                select(func.count()).select_from(User).where(User.role == "admin")
            )
        ).scalar_one()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400, detail="Cannot delete the last admin"
            )
    await db.execute(delete(User).where(User.id == id))
    await _record_audit(
        db,
        actor_id=actor.id,
        action="user.delete",
        target_type="user",
        target_id=id,
        detail=f"deleted_username={existing.username!r}",
    )
    return UserCreatedResponse(message="User deleted")


# ---------------------------------------------------------------------------
# Email outbox + audit log
# ---------------------------------------------------------------------------


@router.get("/emails", response_model=PaginatedResponse)
async def admin_list_emails(
    db: DbDep,
    _: User = Depends(require_role("admin")),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    only_failures: bool = Query(default=False),
) -> dict[str, Any]:
    base = select(EmailOutbox)
    count_q = select(func.count()).select_from(EmailOutbox)
    if only_failures:
        base = base.where(EmailOutbox.failed_at.is_not(None))
        count_q = count_q.where(EmailOutbox.failed_at.is_not(None))
    total = (await db.execute(count_q)).scalar_one()
    rows = (
        await db.execute(
            base.order_by(EmailOutbox.sent_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
    ).scalars().all()
    results = [
        {
            "id": row.id,
            "to_addr": row.to_addr,
            "subject": row.subject,
            "kind": row.kind,
            "related_user_id": row.related_user_id,
            "delivered_at": row.delivered_at.isoformat() if row.delivered_at else None,
            "failed_at": row.failed_at.isoformat() if row.failed_at else None,
            "failure_reason": row.failure_reason,
            "sent_at": row.sent_at.isoformat() if row.sent_at else None,
            # Exclude the body to keep payloads small for the admin UI.
            "body_preview": (row.body_text or "")[:200],
        }
        for row in rows
    ]
    return {
        "results": results,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/audit", response_model=PaginatedResponse)
async def admin_list_audit_log(
    db: DbDep,
    _: User = Depends(require_role("admin")),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    actor_id: int | None = Query(default=None, ge=1),
    action: str | None = Query(default=None, max_length=64),
) -> dict[str, Any]:
    base = select(AuditLog)
    count_q = select(func.count()).select_from(AuditLog)
    if actor_id is not None:
        base = base.where(AuditLog.actor_id == actor_id)
        count_q = count_q.where(AuditLog.actor_id == actor_id)
    if action:
        base = base.where(AuditLog.action == action)
        count_q = count_q.where(AuditLog.action == action)
    total = (await db.execute(count_q)).scalar_one()
    rows = (
        await db.execute(
            base.order_by(AuditLog.occurred_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
    ).scalars().all()
    results = [
        {
            "id": row.id,
            "actor_id": row.actor_id,
            "action": row.action,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "detail": row.detail,
            "ip": row.ip,
            "occurred_at": row.occurred_at.isoformat() if row.occurred_at else None,
        }
        for row in rows
    ]
    return {
        "results": results,
        "total": total,
        "page": page,
        "limit": limit,
    }


__all__ = ["router"]
