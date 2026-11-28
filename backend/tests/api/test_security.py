"""Security headers, CORS and Origin verification (NFR-SEC-008, NFR-SEC-009, SHOP-019)."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.security import API_CSP, DOCS_CSP
from app.core.settings import Settings
from app.main import create_app
from tests.api.conftest import LEAKY_MESSAGE
from tests.conftest import LogCapture

ALLOWED = "http://localhost:3000"
EVIL = "https://evil.example"
EXPECTED = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
    "cross-origin-opener-policy": "same-origin",
    "permissions-policy": "camera=(), microphone=(), geolocation=()",
    "content-security-policy": API_CSP,
}


def assert_secure(headers: Mapping[str, str]) -> None:
    for name, value in EXPECTED.items():
        assert headers[name] == value
    assert "strict-transport-security" not in headers


def test_headers_on_success_and_error_responses(app: FastAPI) -> None:
    """The 500 is the request middleware's last-resort response (unhandled error)."""
    with TestClient(app, raise_server_exceptions=False) as client:
        responses = [
            client.get("/health/live"),
            client.get("/missing"),
            client.post("/health/live"),
            client.post("/t/items", json={"quantity": "x"}),
            client.get("/t/boom"),
        ]
    assert [r.status_code for r in responses] == [200, 404, 405, 422, 500]
    for response in responses:
        assert_secure(response.headers)
    assert LEAKY_MESSAGE not in responses[-1].text
    assert responses[-1].json()["code"] == "internal_error"


def test_docs_have_their_own_csp_only_on_the_docs_path(app: FastAPI) -> None:
    with TestClient(app) as client:
        docs = client.get("/api/v1/docs")
        spec = client.get("/api/v1/openapi.json")
    assert docs.status_code == 200
    assert docs.headers["content-security-policy"] == DOCS_CSP
    assert "cdn.jsdelivr.net" in DOCS_CSP
    assert "*" not in DOCS_CSP
    assert spec.headers["content-security-policy"] == API_CSP


def test_docs_disabled_in_production_still_get_headers(
    make_settings: Callable[..., Settings],
) -> None:
    settings = make_settings(app_env="production", allowed_origins=["https://shop.example"])
    with TestClient(create_app(settings)) as client:
        response = client.get("/api/v1/docs")
    assert response.status_code == 404
    assert response.headers["content-security-policy"] == API_CSP
    assert response.headers["x-frame-options"] == "DENY"


def test_hsts_only_in_staging_and_production(make_settings: Callable[..., Settings]) -> None:
    hsts = "max-age=31536000; includeSubDomains"
    cases = (
        ("development", "http://localhost:3000", None),
        ("test", "http://localhost:3000", None),
        ("staging", "https://shop.example", hsts),
        ("production", "https://shop.example", hsts),
    )
    for env, origin, expected in cases:
        app = create_app(make_settings(app_env=env, allowed_origins=[origin]))
        with TestClient(app) as client:
            value = client.get("/health/live").headers.get("strict-transport-security")
        assert value == expected


def test_cors_preflight_from_allowed_origin(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.options(
            "/t/items",
            headers={
                "Origin": ALLOWED,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, X-CSRF-Token",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED
    assert response.headers["access-control-allow-credentials"] == "true"
    assert response.headers["access-control-max-age"] == "600"
    assert "X-CSRF-Token" in response.headers["access-control-allow-headers"]
    assert_secure(response.headers)


def test_cors_preflight_from_disallowed_origin(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.options(
            "/t/items", headers={"Origin": EVIL, "Access-Control-Request-Method": "POST"}
        )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_cors_exposes_request_id_for_allowed_origin(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.get("/health/live", headers={"Origin": ALLOWED})
    assert response.headers["access-control-expose-headers"] == "X-Request-ID"


def test_post_from_disallowed_origin_is_rejected_and_logged(
    app: FastAPI, log_capture: LogCapture
) -> None:
    with TestClient(app) as client:
        response = client.post("/t/items", json={"quantity": 1}, headers={"Origin": EVIL})
    body = response.json()
    assert response.status_code == 403
    assert response.headers["content-type"] == "application/problem+json"
    assert body["code"] == "origin_not_allowed"
    assert body["title"] == "Forbidden"
    assert body["correlation_id"] == response.headers["X-Request-ID"]
    assert_secure(response.headers)
    assert "evil.example" not in response.text
    assert "evil.example" not in log_capture.text
    events = [r for r in log_capture.records if r["event"] == "Request origin rejected"]
    assert len(events) == 1
    assert events[0]["level"] == "WARNING"
    assert events[0]["method"] == "POST"


def test_null_origin_is_rejected(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.delete("/t/items/1", headers={"Origin": "null"})
    assert response.status_code == 403


def test_allowed_and_missing_origin_pass(app: FastAPI) -> None:
    with TestClient(app) as client:
        allowed = client.post("/t/items", json={"quantity": 1}, headers={"Origin": ALLOWED})
        missing = client.post("/t/items", json={"quantity": 2})
    assert allowed.status_code == missing.status_code == 200


def test_safe_methods_are_not_blocked_by_origin(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.get("/t/items/1", headers={"Origin": EVIL})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
