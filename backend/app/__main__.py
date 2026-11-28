"""Run the backend with Uvicorn: `uv run python -m app` (from backend/).

Host, port and the graceful-shutdown timeout come from the settings
(NFR-REL-008). For auto-reload during development, see docs/DEVELOPMENT.md.
"""

from __future__ import annotations

import uvicorn

from app.core.settings import Settings, get_settings


def server_config(settings: Settings) -> uvicorn.Config:
    """Uvicorn configuration derived from the settings."""
    return uvicorn.Config(
        "app.main:create_app",
        factory=True,
        host=settings.backend_host,
        port=settings.backend_port,
        timeout_graceful_shutdown=settings.shutdown_timeout_seconds,
        log_config=None,  # logging is configured by create_app (app.core.logging)
        server_header=False,  # do not advertise the server software
        access_log=False,  # the request middleware writes the access log
    )


def main() -> None:
    uvicorn.Server(server_config(get_settings())).run()


if __name__ == "__main__":
    main()
