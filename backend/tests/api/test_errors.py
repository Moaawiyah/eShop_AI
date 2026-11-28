"""Problem-details responses never leak internals or input values."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import LogCapture

PROBLEM = "application/problem+json"


def test_not_found_problem(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.get("/missing")
    body = response.json()
    assert response.status_code == 404
    assert response.headers["content-type"] == PROBLEM
    assert body == {
        "type": "about:blank",
        "title": "Not Found",
        "status": 404,
        "detail": "Not Found",
        "code": "not_found",
        "correlation_id": response.headers["X-Request-ID"],
    }


def test_method_not_allowed_keeps_allow_header(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.delete("/t/items/1")
    body = response.json()
    assert response.status_code == 405
    assert "GET" in response.headers["Allow"]
    assert response.headers["content-type"] == PROBLEM
    assert body["code"] == "method_not_allowed"
    assert body["correlation_id"] == response.headers["X-Request-ID"]


def test_validation_error_lists_fields_without_input(app: FastAPI, log_capture: LogCapture) -> None:
    distinct = "distinct-secret-value-9981"
    with TestClient(app) as client:
        response = client.post("/t/items", json={"quantity": distinct})
        path_response = client.get(f"/t/items/{distinct}")
    body = response.json()
    assert response.status_code == 422
    assert response.headers["content-type"] == PROBLEM
    assert body["type"] == "https://eshop-ai.local/problems/validation-error"
    assert body["code"] == "validation_error"
    assert body["errors"] == [{"field": "body.quantity", "code": "int_parsing"}]
    assert body["correlation_id"] == response.headers["X-Request-ID"]
    assert path_response.json()["errors"] == [{"field": "path.item_id", "code": "int_parsing"}]
    for text in (response.text, path_response.text, log_capture.text):
        assert distinct not in text


def test_missing_body_field_reported(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.post("/t/items", json={})
    assert response.json()["errors"] == [{"field": "body.quantity", "code": "missing"}]


def test_app_error_mapped(app: FastAPI) -> None:
    with TestClient(app) as client:
        response = client.get("/t/conflict")
    body = response.json()
    assert response.status_code == 409
    assert response.headers["content-type"] == PROBLEM
    assert body["type"] == "https://eshop-ai.local/problems/out-of-stock"
    assert body["title"] == "Product out of stock"
    assert body["code"] == "out_of_stock"
    assert body["detail"] == "One or more items are no longer available."
    assert body["correlation_id"] == response.headers["X-Request-ID"]


def test_unexpected_error_is_generic(app: FastAPI, log_capture: LogCapture) -> None:
    with TestClient(app) as client:
        response = client.get("/t/boom")
    body = response.json()
    assert response.status_code == 500
    assert response.headers["content-type"] == PROBLEM
    assert body["title"] == "Internal Server Error"
    assert body["code"] == "internal_error"
    assert body["type"] == "https://eshop-ai.local/problems/internal-error"
    assert body["correlation_id"] == response.headers["X-Request-ID"]
    for forbidden in ("hunter2", "secret.py", "Traceback", "RuntimeError", "/srv"):
        assert forbidden not in response.text
