"""Liveness and readiness endpoints."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.settings import Settings
from app.main import create_app
from tests.conftest import LogCapture

PATHS = ["/health/live", "/health/ready"]


@pytest.fixture
def health_app(make_settings: Callable[..., Settings]) -> FastAPI:
    return create_app(make_settings(app_env="test"))


def test_live_inside_lifespan(health_app: FastAPI) -> None:
    with TestClient(health_app) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-type"] == "application/json"


def test_live_without_lifespan(health_app: FastAPI) -> None:
    response = TestClient(health_app).get("/health/live")
    assert (response.status_code, response.json()) == (200, {"status": "ok"})
    assert response.headers["cache-control"] == "no-store"


def test_ready_inside_lifespan(health_app: FastAPI) -> None:
    with TestClient(health_app) as client:
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-type"] == "application/json"


def test_ready_before_lifespan_is_503(health_app: FastAPI) -> None:
    assert health_app.state.readiness.is_ready is False
    response = TestClient(health_app).get("/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-type"] == "application/json"


def test_ready_after_shutdown_is_503_and_logged(
    health_app: FastAPI, log_capture: LogCapture
) -> None:
    with TestClient(health_app):
        assert health_app.state.readiness.is_ready is True
    assert health_app.state.readiness.is_ready is False
    response = TestClient(health_app).get("/health/ready")
    assert (response.status_code, response.json()) == (503, {"status": "not_ready"})
    events = [r["event"] for r in log_capture.records if r["logger"] == "app.main"]
    assert events[1:] == [
        "Readiness established",
        "Readiness withdrawn",
        "Backend shutting down",
    ]


@pytest.mark.parametrize("path", PATHS)
def test_request_id_echoed_or_generated(health_app: FastAPI, path: str) -> None:
    with TestClient(health_app) as client:
        echoed = client.get(path, headers={"X-Request-ID": "probe-request-01"})
        generated = client.get(path)
    assert echoed.headers["x-request-id"] == "probe-request-01"
    assert len(generated.headers["x-request-id"]) == 32


@pytest.mark.parametrize(
    ("path", "started", "expected"),
    [("/health/live", True, 200), ("/health/ready", True, 200), ("/health/ready", False, 503)],
)
def test_access_log_route_and_status(
    health_app: FastAPI, log_capture: LogCapture, path: str, started: bool, expected: int
) -> None:
    if started:
        with TestClient(health_app) as client:
            client.get(path)
    else:
        TestClient(health_app).get(path)
    entry = next(r for r in log_capture.records if r["logger"] == "app.api.access")
    assert (entry["route"], entry["status_code"]) == (path, expected)


def test_openapi_documents_health(health_app: FastAPI) -> None:
    with TestClient(health_app) as client:
        schema = client.get("/api/v1/openapi.json").json()
    live = schema["paths"]["/health/live"]["get"]
    ready = schema["paths"]["/health/ready"]["get"]
    assert live["operationId"] == "health_live"
    assert ready["operationId"] == "health_ready"
    assert set(live["responses"]) == {"200"}
    assert set(ready["responses"]) == {"200", "503"}
    ref = "#/components/schemas/ReadinessResponse"
    for code in ("200", "503"):
        assert ready["responses"][code]["content"]["application/json"]["schema"]["$ref"] == ref
    assert schema["components"]["schemas"]["LivenessResponse"]["additionalProperties"] is False


def test_health_available_when_docs_disabled(make_settings: Callable[..., Settings]) -> None:
    app = create_app(make_settings(app_env="production", allowed_origins=["https://shop.example"]))
    with TestClient(app) as client:
        assert client.get("/api/v1/openapi.json").status_code == 404
        assert client.get("/health/live").json() == {"status": "ok"}
        assert client.get("/health/ready").json() == {"status": "ready"}


def test_bodies_contain_only_status(health_app: FastAPI) -> None:
    with TestClient(health_app) as client:
        assert client.get("/health/live").json() == {"status": "ok"}
        assert client.get("/health/ready").json() == {"status": "ready"}
    assert TestClient(health_app).get("/health/ready").json() == {"status": "not_ready"}
