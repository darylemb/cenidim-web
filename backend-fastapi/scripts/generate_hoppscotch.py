"""Generate the Hoppscotch collection from the FastAPI OpenAPI spec.

Output: backend-fastapi/scripts/hoppscotch-collection.json

Hoppscotch collection **v2** schema (the version the web UI
exports and imports). Key differences from v1:
  - ``headers`` is an OBJECT {key: value}, not an array
  - ``params`` is still an array of {key, value, active, ...}
  - ``v`` is the string ``"2"`` for collections, folders and requests
  - request names must be non-empty strings (the web UI shows
    "untitled" when v1 / missing-name fields slip through)

Spec reference: https://docs.hoppscotch.io/cli/rest-collection-spec

Usage:
    uv run python scripts/generate_hoppscotch.py
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.main import create_app
from app.config import Settings


def _param(p: dict[str, Any]) -> dict[str, Any]:
    """OpenAPI query parameter → Hoppscotch v2 param row."""
    schema = p.get("schema", {})
    return {
        "key": p["name"],
        "value": "" if schema.get("default") is None else str(schema["default"]),
        "active": False,
        "description": p.get("description", ""),
    }


def _body(content: dict[str, Any]) -> dict[str, Any]:
    """Render the request body in v2 shape."""
    json_content = content.get("application/json")
    if json_content is None:
        return {"contentType": None, "body": ""}
    example = json_content.get("example")
    return {
        "contentType": "application/json",
        "body": json.dumps(example) if example is not None else "",
    }


def _path_label(path: str, method: str, op: dict[str, Any]) -> str:
    summary = op.get("summary") or op.get("operationId")
    if summary:
        return f"{method.upper()} {summary}"
    return f"{method.upper()} {path}"


def _request(path: str, method: str, op: dict[str, Any]) -> dict[str, Any]:
    return {
        "v": "2",
        "name": _path_label(path, method, op),
        "method": method.upper(),
        "endpoint": f"{{{{BASE_URL}}}}{path}",
        "headers": {
            # Always-on defaults so the request works out of the box;
            # users can add more from the UI.
            "Accept": "application/json",
        },
        "params": [
            _param(p) for p in op.get("parameters", []) if p.get("in") == "query"
        ],
        "auth": {"active": False, "authType": "none"},
        "body": _body(op.get("requestBody", {}).get("content", {})),
    }


def _folder(name: str, requests: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "v": "2",
        "name": name,
        "folders": [],
        "requests": requests,
    }


def build_collection(base_url: str = "http://localhost:8000") -> dict[str, Any]:
    """Render the FastAPI OpenAPI spec as a Hoppscotch v2 collection."""
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
        label = bucket.replace("_", " ").title().replace("Api ", "API ")
        folders.append(_folder(label, requests))

    return {
        "v": "2",
        "name": "CENIDIM FastAPI",
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