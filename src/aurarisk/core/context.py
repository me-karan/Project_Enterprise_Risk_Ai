"""Request-scoped context management.

Request and correlation IDs are stored in ContextVar instances so concurrent
async requests cannot overwrite each other's values.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from uuid import uuid4

from structlog.contextvars import (
    bind_contextvars,
    clear_contextvars,
    get_contextvars,
)


# Prevent oversized values, spaces and control characters from entering logs.
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

_request_id_var: ContextVar[str | None] = ContextVar(
    "aurarisk_request_id",
    default=None,
)

_correlation_id_var: ContextVar[str | None] = ContextVar(
    "aurarisk_correlation_id",
    default=None,
)


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Identifiers associated with one HTTP request."""

    request_id: str
    correlation_id: str


def generate_request_id() -> str:
    """Generate an opaque request identifier."""

    return uuid4().hex


def normalize_header_identifier(value: str | None) -> str | None:
    """Accept only bounded identifiers that are safe for logs and headers."""

    if value is None:
        return None

    candidate = value.strip()

    if not _IDENTIFIER_PATTERN.fullmatch(candidate):
        return None

    return candidate


def create_request_context(
    inbound_request_id: str | None = None,
    inbound_correlation_id: str | None = None,
) -> RequestContext:
    """Build sanitized identifiers for an incoming request."""

    request_id = normalize_header_identifier(inbound_request_id) or generate_request_id()

    correlation_id = normalize_header_identifier(inbound_correlation_id) or request_id

    return RequestContext(
        request_id=request_id,
        correlation_id=correlation_id,
    )


def get_request_id() -> str | None:
    """Return the request ID for the current async execution context."""

    return _request_id_var.get()


def get_correlation_id() -> str | None:
    """Return the correlation ID for the current async execution context."""

    return _correlation_id_var.get()


@contextmanager
def request_context(
    context: RequestContext,
) -> Iterator[RequestContext]:
    """Activate request identifiers and reliably restore prior context.

    Restoring the previous context makes this safe for tests and nested
    application operations.
    """

    previous_structlog_context = get_contextvars()

    request_token = _request_id_var.set(context.request_id)
    correlation_token = _correlation_id_var.set(context.correlation_id)

    clear_contextvars()
    bind_contextvars(
        request_id=context.request_id,
        correlation_id=context.correlation_id,
    )

    try:
        yield context
    finally:
        clear_contextvars()

        if previous_structlog_context:
            bind_contextvars(**previous_structlog_context)

        _correlation_id_var.reset(correlation_token)
        _request_id_var.reset(request_token)
