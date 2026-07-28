"""Generate the Hoppscotch collection from the FastAPI OpenAPI spec.

Output: backend-fastapi/scripts/hoppscotch-collection.json

Hoppscotch collection v1 schema:
https://docs.hoppscotch.io/cli/rest-collection-spec

Usage:
    uv run python scripts/generate_hoppscotch.py

    # then point Hoppscotch at the file via File > Open or the CLI:
    hpc import scripts/hoppscotch-collection.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.main import create_app
from app.config import Settings


def _param_to_hoppscotch(p: dict[str, Any]) -> dict[str, Any]:
    """Convert an OpenAPI parameter to a Hoppscotch param row."""
    schema = p.get("schema", {})
    return {
        "key": p["name"],
        "value": str(schema.get("default", "")),
        "active": False,
        "description": p.get("description", ""),
    }


def _header_to_hoppscotch(h: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": h["name"],
        "value": "",
        "active": h["name"].lower() in {"accept", "content-type"},
        "description": h.get("description", ""),
    }


def _body_to_hoppscotch(content: dict[str, Any]) -> dict[str, Any] | None:
    """Pick the JSON body (if any) and return the Hoppscotch body shape."""
    json_content = content.get("application/json")
    if json_content is None:
        return None
    schema = json_content.get("schema", {})
    # Use the example if present; otherwise an empty object so the user
    # can fill it in.
    example = json_content.get("example")
    return {
        "contentType": "application/json",
        "body": example if example is not None else "",
    }


def _request(name: str, path: str, method: str, op: dict[str, Any]) -> dict[str, Any]:
    """Build a single Hoppscotch request entry."""
    params = [
        _param_to_hoppscotch(p)
        for p in op.get("parameters", [])
        if p.get("in") == "query"
    ]
    headers = [_header_to_hoppscotch(h) for h in op.get("parameters", []) if p_in_path(h)] \
              or [
                  {"key": "Accept", "value": "application/json", "active": True},
                  {"key": "Content-Type", "value": "application/json", "active": False},
              ]
    return {
        "v": "1",
        "name": name,
        "method": method.upper(),
        "endpoint": f"{{{{BASE_URL}}}}{path}",
        "headers": headers,
        "params": params,
        "auth": {"active": False, "authType": "none"},
        "body": _body_to_hoppscotch(op.get("requestBody", {}).get("content", {})) or {
            "contentType": "application/json",
            "body": "",
        },
    }


def p_in_path(h: dict[str, Any]) -> bool:
    return h.get("in") == "header"


def _path_label(path: str, op: dict[str, Any]) -> str:
    summary = op.get("summary") or op.get("operationId") or path
    return summary


def build_collection(base_url: str = "http://localhost:8000") -> dict[str, Any]:
    """Render the FastAPI OpenAPI spec as a Hoppscotch v1 collection."""
    settings = Settings(
        env="dev",
        db_path=":memory:",
        jwt_secret="x" * 64,
    )
    app = create_app(settings)
    spec = app.openapi()

    folders: list[dict[str, Any]] = []

    # Bucket each path by its first segment so the collection reads as
    # /api/auth/*, /api/admin/*, /api/search, etc.
    by_prefix: dict[str, list[dict[str, Any]]] = {}
    for path, methods in sorted(spec["paths"].items()):
        for method, op in methods.items():
            if method.upper() not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                continue
            request = _request(
                _path_label(path, op),
                path,
                method,
                op,
            )
            parts = [p for p in path.split("/") if p and not p.startswith("{")]
            bucket = "/".join(parts[:2]) if parts else "_root"
            by_prefix.setdefault(bucket, []).append(request)

    for bucket, requests in by_prefix.items():
        label = bucket.replace("_", " ").title()
        folders.append(
            {
                "v": 1,
                "name": label,
                "folders": [],
                "requests": requests,
            }
        )

    return {
        "v": 1,
        "name": "CENIDIM FastAPI",
        "description": (
            "Auto-generated from backend-fastapi/openapi.json. "
            "Set the BASE_URL env variable in Hoppscotch to "
            f"`{base_url}`. For protected endpoints, attach the JWT "
            "from POST /api/auth/login as a Bearer token."
        ),
        "folders": folders,
        "requests": [],
        "auth": {"active": False, "authType": "none"},
    }


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    out = repo / "scripts" / "hoppscotch-collection.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(build_collection(), indent=2, ensure_ascii=False))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()