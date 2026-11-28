"""Export the FastAPI OpenAPI document as deterministic JSON (ARCHITECTURE 4.3).

Usage: `uv run python scripts/export_openapi.py [OUTPUT]` from `backend/`.
The default output is the committed copy used by the frontend type generator.
The document is built from fixed settings, so it never depends on the
developer's `.env` or environment.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = BACKEND_ROOT.parent / "frontend" / "src" / "lib" / "api" / "openapi.json"


def render_openapi() -> str:
    """Return the OpenAPI document as stable, indented JSON with a trailing newline."""
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))
    from app.core.settings import Settings
    from app.main import create_app

    # The application logs its start-up configuration; keep the console quiet.
    logging.disable(logging.CRITICAL)
    try:
        app = create_app(Settings(_env_file=None, app_env="development"))
    finally:
        logging.disable(logging.NOTSET)
    return json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"


def export_openapi(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_openapi(), encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) > 2:
        sys.stderr.write("usage: export_openapi.py [OUTPUT]\n")
        return 2
    export_openapi(Path(argv[1]).resolve() if len(argv) == 2 else DEFAULT_OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
