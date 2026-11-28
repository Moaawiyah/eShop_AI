"""Shared fixtures: settings are isolated from the developer's `.env` and shell."""

from __future__ import annotations

import io
import json
import logging
from collections.abc import Callable, Iterator
from typing import Any

import pytest

from app.core.logging import JsonFormatter
from app.core.settings import Settings, get_settings

SETTING_VARIABLES = (
    "APP_ENV",
    "APP_DEBUG",
    "BACKEND_HOST",
    "BACKEND_PORT",
    "SHUTDOWN_TIMEOUT_SECONDS",
    "LOG_LEVEL",
    "LOG_FORMAT",
)


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Ignore the real `.env`, remove backend variables and reset the settings cache."""
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    for name in SETTING_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def make_settings() -> Callable[..., Settings]:
    """Build settings without reading any `.env` file."""

    def build(**values: Any) -> Settings:
        return Settings(_env_file=None, **values)

    return build


class LogCapture:
    """JSON log lines written through an extra handler using the app formatter."""

    def __init__(self) -> None:
        self.stream = io.StringIO()

    @property
    def text(self) -> str:
        return self.stream.getvalue()

    @property
    def records(self) -> list[dict[str, Any]]:
        return [json.loads(line) for line in self.text.splitlines() if line]


@pytest.fixture(autouse=True)
def restore_logging() -> Iterator[None]:
    """Undo global logging changes made by configure_logging or create_app."""
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    names = ("uvicorn", "uvicorn.error", "uvicorn.access")
    saved = {n: (logging.getLogger(n).propagate, logging.getLogger(n).disabled) for n in names}
    yield
    root.handlers[:] = handlers
    root.setLevel(level)
    for name, (propagate, disabled) in saved.items():
        logging.getLogger(name).propagate = propagate
        logging.getLogger(name).disabled = disabled


@pytest.fixture
def log_capture() -> Iterator[LogCapture]:
    """Capture all root log output as JSON (after the app has configured logging)."""
    capture = LogCapture()
    handler = logging.StreamHandler(capture.stream)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(lambda record: record.name.startswith("app"))  # skip client library logs
    logging.getLogger().addHandler(handler)
    yield capture
    logging.getLogger().removeHandler(handler)
