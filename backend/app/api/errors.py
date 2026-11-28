"""RFC 9457 problem responses and their central exception mapping (ARCHITECTURE 3.8).

Bodies never contain input values, exception messages or stack traces.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.context import get_request_id
from app.core.errors import AppError

PROBLEM_MEDIA_TYPE = "application/problem+json"
PROBLEM_TYPE_BASE = "https://eshop-ai.local/problems/"
INTERNAL_ERROR_DETAIL = "An unexpected error occurred. Quote the correlation ID when reporting it."


def problem_type(code: str) -> str:
    return PROBLEM_TYPE_BASE + code.replace("_", "-")


def problem_response(
    *,
    status: int,
    title: str,
    code: str,
    detail: str | None = None,
    type_uri: str | None = None,
    errors: list[dict[str, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    """Build an `application/problem+json` response carrying the correlation ID."""
    body: dict[str, Any] = {
        "type": type_uri or problem_type(code),
        "title": title,
        "status": status,
        "detail": detail or title,
        "code": code,
        "correlation_id": get_request_id(),
    }
    if errors is not None:
        body["errors"] = errors
    return JSONResponse(body, status_code=status, media_type=PROBLEM_MEDIA_TYPE, headers=headers)


def internal_error_response() -> JSONResponse:
    return problem_response(
        status=500,
        title="Internal Server Error",
        code="internal_error",
        detail=INTERNAL_ERROR_DETAIL,
    )


def _http_error(_: Request, exc: Exception) -> JSONResponse:
    error = cast(StarletteHTTPException, exc)
    try:
        phrase = HTTPStatus(error.status_code).phrase
    except ValueError:
        phrase = "Error"
    return problem_response(
        status=error.status_code,
        title=phrase,
        code=phrase.lower().replace(" ", "_").replace("'", ""),
        type_uri="about:blank",
        headers=dict(error.headers) if error.headers else None,
    )


def _location(loc: tuple[int | str, ...]) -> str:
    out = ""
    for part in loc:
        out += f"[{part}]" if isinstance(part, int) else (f".{part}" if out else str(part))
    return out


def _validation_error(_: Request, exc: Exception) -> JSONResponse:
    error = cast(RequestValidationError, exc)
    errors = [{"field": _location(e["loc"]), "code": str(e["type"])} for e in error.errors()]
    return problem_response(
        status=422,
        title="Validation Error",
        code="validation_error",
        detail="The request is invalid. See errors for the affected fields.",
        errors=errors,
    )


def _app_error(_: Request, exc: Exception) -> JSONResponse:
    error = cast(AppError, exc)
    return problem_response(
        status=error.status_code, title=error.title, code=error.code, detail=error.detail
    )


def register_error_handlers(app: FastAPI) -> None:
    """Map framework and application errors to problem responses.

    No `Exception` handler is registered on purpose: Starlette would route it
    to `ServerErrorMiddleware`, outside the request middleware. Unexpected
    errors are caught and logged by `RequestContextMiddleware` instead.
    """
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(AppError, _app_error)
