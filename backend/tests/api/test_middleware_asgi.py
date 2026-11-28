"""Middleware driven directly through ASGI, in the same task as the assertions."""

from __future__ import annotations

import pytest
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.middleware import RequestContextMiddleware
from app.core.context import get_request_id
from app.core.logging import configure_logging
from tests.conftest import LogCapture

SCOPE: Scope = {"type": "http", "method": "GET", "path": "/x", "headers": []}


async def receive() -> Message:
    return {"type": "http.request", "body": b"", "more_body": False}


class Recorder:
    def __init__(self) -> None:
        self.messages: list[Message] = []

    async def __call__(self, message: Message) -> None:
        self.messages.append(message)

    @property
    def starts(self) -> list[Message]:
        return [m for m in self.messages if m["type"] == "http.response.start"]


async def run(inner: ASGIApp) -> Recorder:
    recorder = Recorder()
    middleware = RequestContextMiddleware(inner)
    await middleware(dict(SCOPE), receive, recorder)
    return recorder


async def ok_app(scope: Scope, receive: Receive, send: Send) -> None:
    assert get_request_id() is not None
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"ok"})


async def failing_app(scope: Scope, receive: Receive, send: Send) -> None:
    assert get_request_id() is not None
    raise RuntimeError("never-logged-message")


async def fail_after_start_app(scope: Scope, receive: Receive, send: Send) -> None:
    await send({"type": "http.response.start", "status": 200, "headers": []})
    raise RuntimeError("never-logged-message")


@pytest.mark.anyio
@pytest.mark.parametrize("inner", [ok_app, failing_app])
async def test_context_reset_after_success_and_failure(inner: ASGIApp) -> None:
    assert get_request_id() is None
    await run(inner)
    assert get_request_id() is None


@pytest.mark.anyio
async def test_error_after_response_started_is_logged_without_second_response(
    log_capture: LogCapture,
) -> None:
    configure_logging("INFO", "json")
    recorder = await run(fail_after_start_app)
    assert len(recorder.starts) == 1
    assert recorder.starts[0]["status"] == 200
    error = next(r for r in log_capture.records if r["level"] == "ERROR")
    assert error["exc_type"] == "builtins.RuntimeError"
    access = next(r for r in log_capture.records if r["logger"] == "app.api.access")
    assert access["status_code"] == 200
    assert "never-logged-message" not in log_capture.text
    assert get_request_id() is None
