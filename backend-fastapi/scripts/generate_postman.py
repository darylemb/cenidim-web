"""Generate a Postman v2.1 collection from the FastAPI OpenAPI spec.

Output: backend-fastapi/scripts/postman-collection.json

Postman v2.1 schema (https://schema.getpostman.com/json/collection/v2.1.0/collection.json):
  - info { _postman_id, name, description, schema }
  - item  — recursive: each is either a folder (with nested item[])
                     or a request (with request{}, response[])
  - variable[ {key, value} ] — collection-level variables; we
                                 expose ``baseUrl`` so Postman users can
                                 import + tweak in one click.

Variables use ``{{baseUrl}}`` (the Postman / curl convention) — NOT
``<<baseUrl>>`` (Hoppscotch). Postman resolves them automatically.

Usage:

    # from anywhere in the repo
    uv run --project backend-fastapi python backend-fastapi/scripts/generate_postman.py

    # or from backend-fastapi/
    cd backend-fastapi
    uv run python scripts/generate_postman.py
"""
from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path
from typing import Any

# Make the FastAPI app importable regardless of where the script is
# invoked from. backend-fastapi/scripts/ -> backend-fastapi/ is one
# level up.
_SCRIPT_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _SCRIPT_DIR.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.main import create_app  # noqa: E402
from app.config import Settings  # noqa: E402


def _query(p: dict[str, Any]) -> dict[str, Any]:
    schema = p.get("schema", {})
    return {
        "key": p["name"],
        "value": "" if schema.get("default") is None else str(schema["default"]),
        "disabled": True,
        "description": p.get("description", ""),
    }


def _request(path: str, method: str, op: dict[str, Any]) -> dict[str, Any]:
    path_params = [
        {"key": m.group(1), "value": "", "description": ""}
        for m in re.finditer(r"\{([^}]+)\}", path)
    ]
    return {
        "name": op.get("summary") or op.get("operationId") or f"{method.upper()} {path}",
        "request": {
            "method": method.upper(),
            "description": op.get("description", ""),
            "header": [
                {"key": "Accept", "value": "application/json", "type": "text"},
            ],
            "url": {
                "raw": f"{{{{baseUrl}}}}{path}",
                "host": ["{{baseUrl}}"],
                "path": [p for p in path.split("/") if p and not p.startswith("{")],
                "variable": path_params,
                "query": [
                    _query(p)
                    for p in op.get("parameters", [])
                    if p.get("in") == "query"
                ],
            },
            # Body only when there's an OpenAPI requestBody — otherwise
            # omit the field so Postman doesn't render an empty editor.
            **({"body": _body(op["requestBody"])} if "requestBody" in op else {}),
        },
        "response": [],
    }


def _body(rb: dict[str, Any]) -> dict[str, Any]:
    content = rb.get("content", {})
    json_content = content.get("application/json")
    example = json_content.get("example") if json_content else None
    return {
        "mode": "raw",
        "raw": json.dumps(example) if example is not None else "",
        "options": {"raw": {"language": "json"}},
    }


def _folder(name: str, children: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "name": name,
        "item": children,
    }


def build_collection(base_url: str = "http://localhost:8000") -> dict[str, Any]:
    """Render the FastAPI OpenAPI spec as a Postman v2.1 collection."""
    settings = Settings(
        env="dev",
        db_path=":memory:",
        jwt_secret="x" * 64,
    )
    app = create_app(settings)
    spec = app.openapi()

    by_prefix: dict[str, list[dict[str, Any]]] = {}
    for path, methods in sorted(spec["paths"].items()):
        for method, op in methods.items():
            if method.upper() not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                continue
            request = _request(path, method, op)
            parts = [p for p in path.split("/") if p and not p.startswith("{")]
            bucket = "/".join(parts[:2]) if parts else "_root"
            by_prefix.setdefault(bucket, []).append(request)

    folders = []
    for bucket, requests in by_prefix.items():
        # Postman renders "/" as a folder separator, so strip the
        # ``api/`` prefix and title-case the rest:
        #   api/admin       -> Admin
        #   api/word-cloud  -> Word-Cloud
        #   healthz         -> Healthz
        parts = bucket.split("/")
        resource = parts[1] if parts[0] == "api" else parts[0]
        label = resource.replace("-", " ").title().replace(" ", "-")
        folders.append(_folder(label, requests))

    return {
        "info": {
            "_postman_id": str(uuid.uuid4()),
            "name": "CENIDIM FastAPI",
            "description": (
                "Auto-generated from backend-fastapi/openapi.json. "
                f"Set the `baseUrl` variable to {base_url!r} (or "
                "http://localhost if you go through the nginx proxy "
                "on :80). Auth-protected endpoints expect a Bearer "
                "token from POST /api/auth/login."
            ),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": folders,
        "variable": [
            {
                "key": "baseUrl",
                "value": base_url,
                "type": "string",
            }
        ],
    }


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    out = repo / "scripts" / "postman-collection.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    collection = build_collection()
    out.write_text(json.dumps(collection, indent=2, ensure_ascii=False))
    print(f"Wrote {out}")
    total = sum(len(f["item"]) for f in collection["item"])
    print(f"  {len(collection['item'])} folders, {total} requests")
    print(
        "  Import via: Postman → Import → File → select the JSON,"
        " OR Postman → Import → Link → "
        "http://localhost:8000/openapi.json (live)"
    )


if __name__ == "__main__":
    main()