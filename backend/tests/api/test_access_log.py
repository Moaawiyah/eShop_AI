"""Access log fields, sensitive-data protection and non-HTTP pass-through."""

from __future__ import annotations

import re

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.types import Message, Receive, Scope, Send

from app.api.middleware import RequestContextMiddleware
from app.core.context import get_request_id
from tests.api.conftest import LEAKY_MESSAGE
from tests.conftest import LogCapture


def test_access_log_uses_route_template_and_hides_query(
    app: FastAPI, log_capture: LogCapture
) -> None:
    with TestClient(app) as client:
        client.get("/t/items/42?token=abc-leak-value")
    access = [r for r in log_capture.records if r["logger"] == "app.api.access"]
    assert len(access) == 1
    entry = access[0]
    assert entry["event"] == "request completed"
    assert entry["level"] == "INFO"
    assert entry["method"] == "GET"
    assert entry["route"] == "/t/items/{item_id}"
    assert entry["status_code"] == 200
    assert entry["duration_ms"] >= 0
    assert "abc-leak-value" not in log_capture.text
    assert "/t/items/42" not in log_capture.text


@pytest.mark.parametrize("path", ["/api/v1/openapi.json", "/api/v1/docs"])
def test_access_log_for_plain_route_without_parameters(
    app: FastAPI, log_capture: LogCapture, path: str
) -> None:
    with TestClient(app) as client:
        client.get(f"{path}?token=abc-leak-value")
    entry = next(r for r in log_capture.records if r["logger"] == "app.api.access")
    assert (entry["route"], entry["status_code"]) == (path, 200)
    assert "abc-leak-value" not in log_capture.text


def test_access_log_for_unmatched_route(app: FastAPI, log_capture: LogCapture) -> None:
    with TestClient(app) as client:
        client.get("/nope/secret-path?x=1")
    entry = next(r for r in log_capture.records if r["logger"] == "app.api.access")
    assert (entry["route"], entry["status_code"]) == ("<unmatched>", 404)
    assert "secret-path" not in log_capture.text


def test_sensitive_headers_are_not_logged(app: FastAPI, log_capture: LogCapture) -> None:
    with TestClient(app) as client:
        client.get(
            "/t/items/1",
            headers={"Authorization": "Bearer top-secret-bearer", "Cookie": "sid=cookie-secret"},
        )
    assert "top-secret-bearer" not in log_capture.text
    assert "cookie-secret" not in log_capture.text


def test_unexpected_error_is_logged_without_message(app: FastAPI, log_capture: LogCapture) -> None:
    with TestClient(app) as client:
        response = client.get("/t/boom")
    assert response.status_code == 500
    error = next(r for r in log_capture.records if r["level"] == "ERROR")
    assert error["exc_type"] == "builtins.RuntimeError"
    assert error["correlation_id"] == response.headers["X-Request-ID"]
    assert error["exc_frames"]
    assert all(re.match(r".+:\d+ in \S+", frame) for frame in error["exc_frames"])
    assert "hunter2" not in log_capture.text
    assert "Traceback" not in log_capture.text
    assert LEAKY_MESSAGE not in log_capture.text
    access = next(r for r in log_capture.records if r["logger"] == "app.api.access")
    assert access["status_code"] == 500


@pytest.mark.anyio
async def test_non_http_scopes_pass_through() -> None:
    seen: list[str] = []

    async def inner(scope: Scope, receive: Receive, send: Send) -> None:
        seen.append(scope["type"])

    async def receive() -> Message:
        return {"type": "websocket.connect"}

    async def send(message: Message) -> None:
        seen.append("sent")

    await RequestContextMiddleware(inner)({"type": "websocket"}, receive, send)
    assert seen == ["websocket"]
    assert get_request_id() is None
