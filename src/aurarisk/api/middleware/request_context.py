"""Pure ASGI middleware for request observability context."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from aurarisk.core.context import (
    create_request_context,
    request_context,
)
from aurarisk.core.logging import get_logger


logger = get_logger(__name__)


def _route_template(scope: Scope) -> str:
    """Get the matched route without exposing raw URL identifiers."""

    route: Any = scope.get("route")
    route_path = getattr(route, "path", None)

    return route_path if isinstance(route_path, str) else "unmatched"


class RequestContextMiddleware:
    """Attach request identifiers and structured lifecycle logs."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        inbound_headers = Headers(scope=scope)

        context = create_request_context(
            inbound_request_id=inbound_headers.get("x-request-id"),
            inbound_correlation_id=inbound_headers.get("x-correlation-id"),
        )

        # Starlette exposes this dictionary through request.state.
        state = scope.setdefault("state", {})
        state["request_id"] = context.request_id
        state["correlation_id"] = context.correlation_id

        started_at = perf_counter()
        status_code = 500
        response_started = False

        async def send_with_tracking_headers(
            message: Message,
        ) -> None:
            nonlocal status_code, response_started

            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_started = True

                response_headers = MutableHeaders(scope=message)
                response_headers["X-Request-ID"] = context.request_id
                response_headers["X-Correlation-ID"] = context.correlation_id

            await send(message)

        with request_context(context):
            logger.info(
                "http_request_started",
                http_method=scope["method"],
            )

            try:
                await self.app(
                    scope,
                    receive,
                    send_with_tracking_headers,
                )
            except Exception as exc:
                duration_ms = round(
                    (perf_counter() - started_at) * 1000,
                    2,
                )

                # Do not log str(exc); exception messages can contain input.
                logger.error(
                    "http_request_failed",
                    http_method=scope["method"],
                    http_route=_route_template(scope),
                    status_code=(status_code if response_started else 500),
                    duration_ms=duration_ms,
                    error_type=type(exc).__name__,
                    response_started=response_started,
                )
                raise
            else:
                duration_ms = round(
                    (perf_counter() - started_at) * 1000,
                    2,
                )

                logger.info(
                    "http_request_completed",
                    http_method=scope["method"],
                    http_route=_route_template(scope),
                    status_code=status_code,
                    duration_ms=duration_ms,
                )
