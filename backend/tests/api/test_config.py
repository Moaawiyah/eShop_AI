"""Public feature flag endpoint and the `get_flags` dependency."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient
from starlette.requests import Request

from app.api.dependencies import get_flags
from app.core.settings import Settings
from app.main import create_app
from tests.conftest import LogCapture

PATH = "/api/v1/config/public-flags"
MakeSettings = Callable[..., Settings]


def get(make_settings: MakeSettings, **values: Any) -> Any:
    return TestClient(create_app(make_settings(**values))).get(PATH)


def test_defaults_are_off(make_settings: MakeSettings) -> None:
    response = get(make_settings, app_env="test")
    assert response.status_code == 200
    assert response.json() == {"ai_assistant": False}
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-request-id"]


def test_enabled_public_flag_and_server_only_flags_hidden(make_settings: MakeSettings) -> None:
    response = get(
        make_settings,
        app_env="test",
        feature_ai_assistant=True,
        feature_external_product_sources=True,
        feature_notifications=True,
    )
    assert response.json() == {"ai_assistant": True}


def test_available_in_production(make_settings: MakeSettings) -> None:
    response = get(make_settings, app_env="production")
    assert (response.status_code, response.json()) == (200, {"ai_assistant": False})


def test_openapi_documents_the_operation(make_settings: MakeSettings) -> None:
    spec = TestClient(create_app(make_settings(app_env="test"))).get("/api/v1/openapi.json").json()
    assert spec["paths"][PATH]["get"]["operationId"] == "config_public_flags"
    assert spec["components"]["schemas"]["PublicFlagsResponse"]["additionalProperties"] is False


def test_get_flags_returns_the_app_instance(make_settings: MakeSettings) -> None:
    app = create_app(make_settings(app_env="test"))
    request = Request({"type": "http", "app": app})
    assert get_flags(request) is app.state.flags


def test_enabled_flag_names_are_logged_at_creation(
    make_settings: MakeSettings, log_capture: LogCapture
) -> None:
    create_app(make_settings(app_env="test", feature_notifications=True))
    events = [record["event"] for record in log_capture.records]
    assert "Feature flags loaded (enabled=['notifications'])" in events
