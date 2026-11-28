"""Request context middleware: request ID, access log and last-resort 500.

Pure ASGI (not `BaseHTTPMiddleware`) so context variables and streaming
behave predictably.
"""

from __future__ import annotations

import logging
import re
import time
import uuid

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.errors import internal_error_response
from app.core.context import reset_request_id, set_request_id

REQUEST_ID_HEADER = "X-Request-ID"
VALID_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{8,64}")
UNMATCHED_ROUTE = "<unmatched>"

access_logger = logging.getLogger("app.api.access")
logger = logging.getLogger(__name__)


def resolve_request_id(headers: Headers) -> tuple[str, bool]:
    """Return `(request_id, was_valid)`: a well-formed single incoming ID or a new one."""
    values = headers.getlist(REQUEST_ID_HEADER)
    if len(values) == 1 and VALID_REQUEST_ID.fullmatch(values[0]):
        return values[0], True
    return uuid.uuid4().hex, not values


def route_label(scope: Scope) -> str:
    """Matched route template, never a raw path with parameters or a query string.

    FastAPI routes set `scope["route"]`. Plain Starlette routes (docs, OpenAPI)
    only set `endpoint`; without path parameters their raw path equals the
    template, so it is safe to log.
    """
    template = getattr(scope.get("route"), "path", None)
    if template:
        return str(template)
    if scope.get("endpoint") is not None and not scope.get("path_params"):
        return str(scope["path"])
    return UNMATCHED_ROUTE


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id, acceptable = resolve_request_id(Headers(scope=scope))
        token = set_request_id(request_id)
        if not acceptable:
            logger.warning("Invalid X-Request-ID header replaced")  # never log the value
        scope.setdefault("state", {})["request_id"] = request_id
        started = False
        status_code = 500

        async def send_with_id(message: Message) -> None:
            nonlocal started, status_code
            if message["type"] == "http.response.start":
                started = True
                status_code = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        start = time.perf_counter()
        try:
            try:
                await self.app(scope, receive, send_with_id)
            except Exception:
                logger.error("Unhandled exception", exc_info=True)
                if not started:
                    response = internal_error_response()
                    await response(scope, receive, send_with_id)
            route = route_label(scope)
            access_logger.info(
                "request completed",
                extra={
                    "method": scope["method"],
                    "route": route,
                    "status_code": status_code,
                    "duration_ms": round((time.perf_counter() - start) * 1000, 3),
                },
            )
        finally:
            reset_request_id(token)
