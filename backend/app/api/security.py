"""Security headers and Origin verification (NFR-SEC-008, SHOP-019).

Pure ASGI middleware. Cookie sessions and CSRF tokens arrive with SHOP-032;
the Origin check here is the first, token-independent layer.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.errors import problem_response
from app.api.middleware import route_label
from app.api.router import API_PREFIX

DOCS_PATH = f"{API_PREFIX}/docs"
UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
HSTS_VALUE = "max-age=31536000; includeSubDomains"

API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
# Swagger UI from FastAPI's default assets (development and test only): script and
# stylesheet from cdn.jsdelivr.net, favicon from fastapi.tiangolo.com. The page
# bootstraps itself with one inline script, so inline code is allowed here only.
DOCS_CSP = (
    "default-src 'none'; "
    "script-src https://cdn.jsdelivr.net 'unsafe-inline'; "
    "style-src https://cdn.jsdelivr.net 'unsafe-inline'; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
)
BASE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """Add the security headers to every HTTP response, errors included."""

    def __init__(self, app: ASGIApp, *, hsts: bool, docs_enabled: bool) -> None:
        self.app = app
        self.hsts = hsts
        self.docs_enabled = docs_enabled

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        is_docs = self.docs_enabled and scope["path"] == DOCS_PATH

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in BASE_HEADERS.items():
                    headers[name] = value
                headers["Content-Security-Policy"] = DOCS_CSP if is_docs else API_CSP
                if self.hsts:
                    headers["Strict-Transport-Security"] = HSTS_VALUE
            await send(message)

        await self.app(scope, receive, send_with_headers)


class OriginCheckMiddleware:
    """Reject unsafe requests whose `Origin` header is present but not allowed.

    Requests without `Origin` pass (non-browser clients; the CSRF token of
    SHOP-032 protects browsers). Safe methods are never blocked. The check
    runs before routing, so the logged route label is usually `<unmatched>`.
    """

    def __init__(self, app: ASGIApp, *, allowed_origins: Iterable[str]) -> None:
        self.app = app
        self.allowed = frozenset(allowed_origins)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["method"] in UNSAFE_METHODS:
            origin = Headers(scope=scope).get("origin")
            if origin is not None and origin not in self.allowed:
                logger.warning(
                    "Request origin rejected",
                    extra={"method": scope["method"], "route": route_label(scope)},
                )
                response = problem_response(
                    status=403,
                    title="Forbidden",
                    code="origin_not_allowed",
                    detail="The request origin is not allowed.",
                )
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
