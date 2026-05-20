# Export the versioned FastAPI OpenAPI schema for checked-in client type generation.

from __future__ import annotations

import json
import sys
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

app = cast(FastAPI, import_module("app.main").app)


def versioned_openapi_schema() -> dict[str, Any]:
    routes = [route for route in app.routes if getattr(route, "path", "").startswith("/api/v1")]
    return get_openapi(
        title=app.title,
        version=app.version,
        routes=routes,
    )


def default_output_path() -> Path:
    return Path(__file__).resolve().parents[3] / "docs" / "api" / "openapi-v1.json"


def main() -> None:
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_output_path()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(versioned_openapi_schema(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
