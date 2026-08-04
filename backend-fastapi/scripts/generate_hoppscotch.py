"""Generate the Hoppscotch collection from the FastAPI OpenAPI spec.

Output: backend-fastapi/scripts/hoppscotch-collection.json

Hoppscotch collection v2 schema (per hoppscotch-data/src/rest/v/1.ts,
collection/v/2.ts, rest/v/5.ts). The web UI's import path validates
each request against the latest ``HoppRESTRequest`` schema and then
walks it through every version migration. The v2 collection itself
needs:
  - ``v: 2`` (literal number)
  - ``name: string``
  - ``requests: []``  (can be empty when folders carry the requests)
  - ``folders: []``  (can be empty)
  - ``headers: []``  (REQUIRED, collection-level default headers)
  - ``auth: { authType: "none", authActive: true }`` (REQUIRED)

Each request needs v >= "1" with the HoppRESTAuth union
(``authType`` + ``authActive: bool``, NOT ``active``) and an array
of ``HoppRESTHeaders`` (NOT an object). The script targets v1
because that's the earliest complete shape that the version walker
can promote all the way to v17 without further input from us.

Variable interpolation: Hoppscotch uses ``<<var>>`` (double angle
brackets), NOT ``{{var}}`` — the latter is the Postman syntax.
See https://docs.hoppscotch.io/documentation/features/environments

Spec reference: https://docs.hoppscotch.io/cli/rest-collection-spec

Usage:

    # from anywhere in the repo
    uv run --project backend-fastapi python backend-fastapi/scripts/generate_hoppscotch.py

    # or from backend-fastapi/
    cd backend-fastapi
    uv run python scripts/generate_hoppscotch.py
"""
from __future__ import annotations

import json
import sys
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


# Hoppscotch auth/header shape expected by every version from v1+.
NO_AUTH = {"authType": "none", "authActive": True}


def _param(p: dict[str, Any]) -> dict[str, Any]:
    """OpenAPI query parameter → Hoppscotch v1+ param row."""
    schema = p.get("schema", {})
    return {
        "key": p["name"],
        "value": "" if schema.get("default") is None else str(schema["default"]),
        "active": False,
        "description": p.get("description", ""),
    }


def _body(content: dict[str, Any]) -> dict[str, Any]:
    """Render the request body in HoppRESTReqBody shape."""
    json_content = content.get("application/json")
    if json_content is None:
        # ``contentType: null, body: null`` is the GET / no-body branch.
        return {"contentType": None, "body": None}
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
        "v": "1",
        "name": _path_label(path, method, op),
        "method": method.upper(),
        # Hoppscotch uses ``<<var>>`` for variable interpolation;
        # ``{{var}}`` is the Postman syntax and Hoppscotch treats
        # the braces as literal characters.
        "endpoint": f"<<BASE_URL>>{path}",
        "params": [
            _param(p) for p in op.get("parameters", []) if p.get("in") == "query"
        ],
        # Headers is an ARRAY of {key, value, active} per HoppRESTHeaders
        # schema. Pre-populating Accept means requests work out of the
        # box; users can add more from the UI.
        "headers": [
            {"key": "Accept", "value": "application/json", "active": True},
        ],
        "preRequestScript": "",
        "testScript": "",
        # ``authActive: bool`` (not ``active``) — that's the bit that
        # was making the UI show "untitled" in older exports.
        "auth": {"authType": "none", "authActive": False},
        "body": _body(op.get("requestBody", {}).get("content", {})),
    }


def _folder(name: str, requests: list[dict[str, Any]]) -> dict[str, Any]:
    # Folders are themselves HoppCollection-shaped v2 records.
    # NOTE: collection/folder ``v`` is the *number* 2; request ``v``
    # is the *string* "1"+"17". Hoppscotch's getVersion() reads
    # ``data.v`` as a number for collections and walks requests
    # through verzod's entityRefUptoVersion.
    return {
        "v": 2,
        "name": name,
        "folders": [],
        "requests": requests,
        "headers": [],
        "auth": dict(NO_AUTH),
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
        # Folder names with "/" trip Hoppscotch's name rendering.
        # Drop the "api/" prefix and title-case the rest:
        #   api/admin       -> Admin
        #   api/word-cloud  -> Word-Cloud
        #   healthz         -> Healthz
        parts = bucket.split("/")
        resource = parts[1] if parts[0] == "api" else parts[0]
        label = resource.replace("-", " ").title().replace(" ", "-")
        folders.append(_folder(label, requests))

    return {
        "v": 2,
        "name": "CENIDIM FastAPI",
        "folders": folders,
        "requests": [],
        # Collection-level default headers + auth (applied to every
        # request that uses ``authType: "inherit"``).
        "headers": [],
        "auth": dict(NO_AUTH),
    }


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    out = repo / "scripts" / "hoppscotch-collection.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    collection = build_collection()
    out.write_text(json.dumps(collection, indent=2, ensure_ascii=False))
    print(f"Wrote {out}")

    # Print a summary that doubles as a structural sanity check.
    total = sum(len(f["requests"]) for f in collection["folders"])
    print(
        f"  {len(collection['folders'])} folders, {total} requests, "
        f"collection v={collection['v']}, folder v={collection['folders'][0]['v']}, "
        f"request v={collection['folders'][0]['requests'][0]['v']!r}"
    )
    print(
        "  Verify with: "
        "cd scripts/hoppscotch-validator && node validate.mjs ../hoppscotch-collection.json"
    )


if __name__ == "__main__":
    main()