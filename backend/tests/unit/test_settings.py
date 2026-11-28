"""Settings: safe defaults, environment overrides and rejected values."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.settings import REPOSITORY_ENV_FILE, Settings

MakeSettings = Callable[..., Settings]


def test_defaults_are_safe_for_local_development(make_settings: MakeSettings) -> None:
    settings = make_settings()
    assert settings.app_env == "development"
    assert settings.app_debug is False
    assert settings.backend_host == "127.0.0.1"  # not reachable from other machines
    assert settings.backend_port == 8000
    assert settings.shutdown_timeout_seconds == 20


def test_environment_variables_override_defaults(
    make_settings: MakeSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("BACKEND_PORT", "8100")
    monkeypatch.setenv("SHUTDOWN_TIMEOUT_SECONDS", "5")
    settings = make_settings()
    assert (settings.app_env, settings.backend_port, settings.shutdown_timeout_seconds) == (
        "test",
        8100,
        5,
    )


def test_env_file_is_read_and_environment_wins(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("APP_ENV=test\nBACKEND_PORT=8200\nFRONTEND_ONLY_KEY=x\n", encoding="utf-8")
    monkeypatch.setenv("BACKEND_PORT", "8300")
    settings = Settings(_env_file=env_file)
    assert (settings.app_env, settings.backend_port) == ("test", 8300)


def test_missing_env_file_is_allowed(tmp_path: Path) -> None:
    assert Settings(_env_file=tmp_path / "absent.env").app_env == "development"


def test_repository_env_file_is_at_the_repository_root() -> None:
    assert (REPOSITORY_ENV_FILE.parent / ".env.example").is_file()


@pytest.mark.parametrize(
    "values",
    [
        {"app_env": "local"},
        {"backend_port": 0},
        {"backend_port": 70000},
        {"shutdown_timeout_seconds": 0},
        {"shutdown_timeout_seconds": 121},
        {"app_debug": True, "app_env": "production"},
        {"app_debug": True, "app_env": "staging"},
    ],
)
def test_invalid_values_are_rejected(
    make_settings: MakeSettings, values: dict[str, object]
) -> None:
    with pytest.raises(ValidationError):
        make_settings(**values)


def test_settings_are_immutable(make_settings: MakeSettings) -> None:
    settings = make_settings()
    with pytest.raises(ValidationError):
        settings.app_env = "production"  # type: ignore[misc]  # intentional write to a frozen model


@pytest.mark.parametrize(
    ("environment", "enabled"),
    [("development", True), ("test", True), ("staging", False), ("production", False)],
)
def test_api_docs_only_in_local_environments(
    make_settings: MakeSettings, environment: str, enabled: bool
) -> None:
    settings = make_settings(app_env=environment, allowed_origins=["https://shop.example"])
    assert settings.api_docs_enabled is enabled


def test_allowed_origins_default_is_the_local_frontend(make_settings: MakeSettings) -> None:
    assert make_settings().allowed_origins == ["http://localhost:3000", "http://127.0.0.1:3000"]


def test_allowed_origins_parse_comma_list(
    make_settings: MakeSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ALLOWED_ORIGINS", " http://localhost:3000/ , ,https://a.example:8443 ")
    assert make_settings().allowed_origins == ["http://localhost:3000", "https://a.example:8443"]


@pytest.mark.parametrize(
    "value",
    [
        "*",
        "http://localhost:3000/app",
        "http://localhost:3000?x=1",
        "http://user:pw@localhost:3000",
        "localhost:3000",
        "ftp://localhost",
        "http://localhost:notaport",
    ],
)
def test_allowed_origins_reject_invalid_values(
    make_settings: MakeSettings, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("ALLOWED_ORIGINS", value)
    with pytest.raises(ValidationError):
        make_settings()


def test_allowed_origins_require_https_in_shared_environments(
    make_settings: MakeSettings,
) -> None:
    with pytest.raises(ValidationError):
        make_settings(app_env="production", allowed_origins=["http://shop.example"])
    ok = make_settings(app_env="staging", allowed_origins=["https://shop.example"])
    assert ok.allowed_origins == ["https://shop.example"]
