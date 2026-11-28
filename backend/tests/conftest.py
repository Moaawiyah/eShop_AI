"""Shared fixtures: settings are isolated from the developer's `.env` and shell."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

import pytest

from app.core.settings import Settings, get_settings

SETTING_VARIABLES = ("APP_ENV", "APP_DEBUG", "BACKEND_HOST", "BACKEND_PORT",
                     "SHUTDOWN_TIMEOUT_SECONDS")


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
