"""Generate docs/openapi.json from the live FastAPI app.

Run this script after any router/schema change to keep the
checked-in OpenAPI spec in sync:

    uv run python scripts/generate_openapi.py

The committed `openapi.json` is what the frontend type generator
and the coolify-deploy hook consume; CI regenerates it on every
build to catch drift.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Make the project importable when the script is invoked directly.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


def main() -> None:
    settings = Settings(env="dev", jwt_secret="x" * 64, db_path="/tmp/x.db")
    app = create_app(settings)
    spec = app.openapi()
    out = ROOT / "openapi.json"
    out.write_text(json.dumps(spec, indent=2, default=str))
    print(
        f"Wrote {out} "
        f"({len(spec.get('paths', {}))} paths, "
        f"{len(spec.get('components', {}).get('schemas', {}))} schemas)"
    )


if __name__ == "__main__":
    main()
