"""Uvicorn configuration: host, port and graceful-shutdown timeout (NFR-REL-008)."""

from __future__ import annotations

from collections.abc import Callable

from app.__main__ import server_config
from app.core.settings import Settings


def test_server_uses_settings(make_settings: Callable[..., Settings]) -> None:
    config = server_config(make_settings(backend_port=8123, shutdown_timeout_seconds=7))
    assert config.app == "app.main:create_app"
    assert config.factory is True
    assert (config.host, config.port) == ("127.0.0.1", 8123)
    assert config.timeout_graceful_shutdown == 7


def test_server_leaves_logging_to_the_application(
    make_settings: Callable[..., Settings],
) -> None:
    config = server_config(make_settings())
    assert config.log_config is None
    assert config.access_log is False


def test_server_does_not_advertise_the_server_software(
    make_settings: Callable[..., Settings],
) -> None:
    assert server_config(make_settings()).server_header is False
