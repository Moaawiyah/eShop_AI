"""Application factory: OpenAPI documentation, lifespan and unknown routes."""

from __future__ import annotations

import logging
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app

MakeSettings = Callable[..., Settings]


def test_openapi_and_docs_available_in_development(make_settings: MakeSettings) -> None:
    with TestClient(create_app(make_settings())) as client:
        schema = client.get("/api/v1/openapi.json")
        docs = client.get("/api/v1/docs")
    assert schema.status_code == 200
    assert schema.json()["info"]["title"] == "eShop_AI API"
    assert docs.status_code == 200
    assert "swagger-ui" in docs.text.lower()


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_openapi_and_docs_disabled_in_shared_environments(
    make_settings: MakeSettings, environment: str
) -> None:
    with TestClient(create_app(make_settings(app_env=environment))) as client:
        for path in ("/api/v1/openapi.json", "/api/v1/docs", "/docs", "/redoc"):
            assert client.get(path).status_code == 404, path


def test_unknown_route_returns_404(make_settings: MakeSettings) -> None:
    with TestClient(create_app(make_settings())) as client:
        assert client.get("/api/v1/does-not-exist").status_code == 404


def test_lifespan_logs_start_up_and_shutdown(
    make_settings: MakeSettings, caplog: pytest.LogCaptureFixture
) -> None:
    app = create_app(make_settings(app_env="test"))
    with caplog.at_level(logging.INFO, logger="app.main"), TestClient(app):
        assert "Backend starting (environment=test)" in caplog.text
        assert "shutting down" not in caplog.text
    assert "Backend shutting down" in caplog.text


def test_factory_uses_cached_settings_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    app = create_app()
    assert app.state.settings.app_env == "production"
    assert app.debug is False
    assert app.openapi_url is None
