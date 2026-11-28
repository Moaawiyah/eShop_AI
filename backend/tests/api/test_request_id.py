"""Request ID resolution, response header, context isolation and cleanup."""

from __future__ import annotations

import asyncio
import re

import httpx2
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.datastructures import Headers

from app.api.middleware import resolve_request_id
from tests.conftest import LogCapture

GENERATED = re.compile(r"^[0-9a-f]{32}$")


def test_request_id_generated_when_absent(app: FastAPI, log_capture: LogCapture) -> None:
    with TestClient(app) as client:
        response = client.get("/t/items/1")
    assert GENERATED.match(response.headers["X-Request-ID"])
    assert not [r for r in log_capture.records if r["level"] == "WARNING"]


def test_valid_request_id_is_echoed(app: FastAPI, log_capture: LogCapture) -> None:
    with TestClient(app) as client:
        response = client.get("/t/items/1", headers={"X-Request-ID": "my-test-request-01"})
    assert response.headers["X-Request-ID"] == "my-test-request-01"
    access = [r for r in log_capture.records if r["logger"] == "app.api.access"]
    assert access[0]["correlation_id"] == "my-test-request-01"


@pytest.mark.parametrize(
    "bad",
    ["short", "x" * 65, "has space in it", "bad/chars/here", ""],
)
def test_invalid_request_id_is_replaced_and_not_logged(
    app: FastAPI, log_capture: LogCapture, bad: str
) -> None:
    with TestClient(app) as client:
        response = client.get("/t/items/1", headers={"X-Request-ID": bad})
    assert GENERATED.match(response.headers["X-Request-ID"])
    warnings = [r for r in log_capture.records if r["level"] == "WARNING"]
    assert len(warnings) == 1
    assert warnings[0]["correlation_id"] == response.headers["X-Request-ID"]
    if bad:
        assert bad not in log_capture.text


@pytest.mark.parametrize(
    "raw", [b"abcdefgh\r\nSet-Cookie: a=b", b"caf\xc3\xa9-request-id", b"abcdefgh\nijkl"]
)
def test_header_injection_values_are_rejected(raw: bytes) -> None:
    # HTTP clients refuse these values, so the validator is exercised directly.
    scope = {"type": "http", "headers": [(b"x-request-id", raw)]}
    request_id, acceptable = resolve_request_id(Headers(scope=scope))
    assert GENERATED.match(request_id)
    assert acceptable is False


def test_multiple_request_id_headers_are_replaced(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.get(
            "/t/items/1",
            headers=[("X-Request-ID", "first-request-1"), ("X-Request-ID", "second-request-2")],
        )
    assert GENERATED.match(response.headers["X-Request-ID"])


@pytest.mark.anyio
async def test_concurrent_requests_keep_their_own_ids(
    app: FastAPI, log_capture: LogCapture
) -> None:
    ids = [f"concurrent-req-{n}" for n in range(5)]
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(transport=transport, base_url="http://test") as client:
        responses = await asyncio.gather(
            *(client.get(f"/t/slow/{rid}", headers={"X-Request-ID": rid}) for rid in ids)
        )
    for rid, response in zip(ids, responses, strict=True):
        assert response.headers["X-Request-ID"] == rid
    slow = [r for r in log_capture.records if r["logger"] == "app.test.slow"]
    assert len(slow) == 10
    for record in slow:
        assert record["event"].split()[1] == record["correlation_id"]
