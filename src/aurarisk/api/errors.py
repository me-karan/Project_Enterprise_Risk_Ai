"""FastAPI exception handlers and public error contract."""

from __future__ import annotations

import traceback
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from aurarisk.core.context import (
    generate_request_id,
    get_correlation_id,
    get_request_id,
)
from aurarisk.core.exceptions import AuraRiskError, ErrorCode
from aurarisk.core.logging import get_logger


logger = get_logger(__name__)


_HTTP_ERROR_CODES: dict[int, ErrorCode] = {
    400: ErrorCode.BAD_REQUEST,
    401: ErrorCode.UNAUTHENTICATED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.METHOD_NOT_ALLOWED,
    409: ErrorCode.CONFLICT,
    429: ErrorCode.RATE_LIMITED,
}


def _request_identifiers(
    request: Request,
) -> tuple[str, str]:
    """Get identifiers from context or middleware-created request state."""

    request_id = (
        get_request_id() or getattr(request.state, "request_id", None) or generate_request_id()
    )

    correlation_id = (
        get_correlation_id() or getattr(request.state, "correlation_id", None) or request_id
    )

    return request_id, correlation_id


def _tracking_headers(
    request_id: str,
    correlation_id: str,
) -> dict[str, str]:
    return {
        "X-Request-ID": request_id,
        "X-Correlation-ID": correlation_id,
    }


def _error_body(
    *,
    code: ErrorCode,
    message: str,
    request_id: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create the single public error-envelope format."""

    return {
        "error": {
            "code": code.value,
            "message": message,
            "request_id": request_id,
            "details": details or {},
        }
    }


def _route_template(request: Request) -> str:
    """Return the route template without logging raw URL parameters."""

    route = request.scope.get("route")
    path = getattr(route, "path", None)

    return path if isinstance(path, str) else "unmatched"


async def handle_aurarisk_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle expected domain and policy failures."""

    if not isinstance(exc, AuraRiskError):
        raise TypeError("Expected AuraRiskError")

    request_id, correlation_id = _request_identifiers(request)

    logger.warning(
        "controlled_request_rejected",
        error_code=exc.code.value,
        status_code=exc.status_code,
        http_method=request.method,
        http_route=_route_template(request),
        error_details=exc.details,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(
            code=exc.code,
            message=exc.message,
            request_id=request_id,
            details=exc.details,
        ),
        headers=_tracking_headers(
            request_id,
            correlation_id,
        ),
    )


async def handle_http_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Normalize framework-generated HTTP errors."""

    if not isinstance(exc, StarletteHTTPException):
        raise TypeError("Expected StarletteHTTPException")

    request_id, correlation_id = _request_identifiers(request)

    code = _HTTP_ERROR_CODES.get(
        exc.status_code,
        (ErrorCode.BAD_REQUEST if exc.status_code < 500 else ErrorCode.INTERNAL_ERROR),
    )

    # Never expose internal HTTP exception detail for server failures.
    if exc.status_code >= 500:
        message = "The service could not complete the request."
    elif isinstance(exc.detail, str):
        message = exc.detail
    else:
        message = "The request could not be completed."

    headers = dict(exc.headers or {})
    headers.update(_tracking_headers(request_id, correlation_id))

    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(
            code=code,
            message=message,
            request_id=request_id,
        ),
        headers=headers,
    )


async def handle_validation_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Return validation issues without reflecting submitted input."""

    if not isinstance(exc, RequestValidationError):
        raise TypeError("Expected RequestValidationError")

    request_id, correlation_id = _request_identifiers(request)

    # Pydantic errors can contain the original `input`. We intentionally
    # whitelist only location, message and type.
    issues = [
        {
            "location": [str(part) for part in error.get("loc", ())],
            "message": str(error.get("msg", "Invalid value"))[:300],
            "type": str(error.get("type", "validation_error")),
        }
        for error in exc.errors()
    ]

    logger.info(
        "request_validation_failed",
        http_method=request.method,
        http_route=_route_template(request),
        issue_count=len(issues),
    )

    return JSONResponse(
        status_code=422,
        content=_error_body(
            code=ErrorCode.VALIDATION_ERROR,
            message="The request failed validation.",
            request_id=request_id,
            details={"issues": issues},
        ),
        headers=_tracking_headers(
            request_id,
            correlation_id,
        ),
    )


async def handle_unexpected_exception(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Log an unexpected failure while returning a safe public response."""

    request_id, correlation_id = _request_identifiers(request)

    # format_tb records frames without including the exception's raw message,
    # which might contain customer-submitted values.
    safe_stack_trace = "".join(traceback.format_tb(exc.__traceback__))

    logger.error(
        "unhandled_application_exception",
        error_type=type(exc).__name__,
        stack_trace=safe_stack_trace,
        http_method=request.method,
        http_route=_route_template(request),
    )

    return JSONResponse(
        status_code=500,
        content=_error_body(
            code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred.",
            request_id=request_id,
        ),
        headers=_tracking_headers(
            request_id,
            correlation_id,
        ),
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register AuraRisk's global API error contract."""

    app.add_exception_handler(
        AuraRiskError,
        handle_aurarisk_error,
    )
    app.add_exception_handler(
        StarletteHTTPException,
        handle_http_exception,
    )
    app.add_exception_handler(
        RequestValidationError,
        handle_validation_error,
    )
    app.add_exception_handler(
        Exception,
        handle_unexpected_exception,
    )
