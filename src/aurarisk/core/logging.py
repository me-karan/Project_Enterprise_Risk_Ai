"""Secure structured logging configuration for AuraRisk."""

from __future__ import annotations

import logging
import re
import sys
from collections.abc import Mapping
from datetime import date, datetime
from enum import Enum
from typing import Any, TextIO, cast
from uuid import UUID

import structlog
from pydantic import BaseModel, SecretBytes, SecretStr
from structlog.stdlib import BoundLogger
from structlog.typing import EventDict, Processor, WrappedLogger

from aurarisk.core.settings import LoggingSettings, get_settings


REDACTED = "[REDACTED]"

# These fields must never be written to application logs.
_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "client_secret",
        "clientsecret",
        "token",
        "access_token",
        "accesstoken",
        "refresh_token",
        "refreshtoken",
        "id_token",
        "authorization",
        "api_key",
        "apikey",
        "cookie",
        "set_cookie",
        "ssn",
        "pan",
        "cvv",
        "pin",
        "account_number",
        "accountnumber",
        "routing_number",
        "routingnumber",
        "customer_id",
        "customerid",
        "email",
        "phone",
        "date_of_birth",
    }
)

_SENSITIVE_SUFFIXES = (
    "_password",
    "_secret",
    "_token",
    "_api_key",
    "_cookie",
)

_BEARER_PATTERN = re.compile(
    r"\bbearer\s+[A-Za-z0-9\-._~+/]+=*",
    flags=re.IGNORECASE,
)

_ASSIGNMENT_PATTERN = re.compile(
    r"\b("
    r"password|passwd|api[_-]?key|access[_-]?token|"
    r"refresh[_-]?token|client[_-]?secret"
    r")(\s*[:=]\s*)([^\s,;]+)",
    flags=re.IGNORECASE,
)


def _normalize_key(key: object) -> str:
    """Normalize dictionary keys before classifying them."""

    normalized = re.sub(
        r"[^a-z0-9]+",
        "_",
        str(key).lower(),
    )
    return normalized.strip("_")


def _is_sensitive_key(key: object) -> bool:
    """Return whether a field name represents sensitive data."""

    normalized = _normalize_key(key)

    return normalized in _SENSITIVE_KEYS or normalized.endswith(_SENSITIVE_SUFFIXES)


def _redact_embedded_secrets(value: str) -> str:
    """Redact common secrets embedded inside free-form messages."""

    redacted = _BEARER_PATTERN.sub(
        "Bearer [REDACTED]",
        value,
    )

    return _ASSIGNMENT_PATTERN.sub(
        lambda match: f"{match.group(1)}{match.group(2)}{REDACTED}",
        redacted,
    )


def redact_sensitive_data(
    value: Any,
    *,
    field_name: object | None = None,
) -> Any:
    """Recursively redact secrets and normalize values for JSON output."""

    if field_name is not None and _is_sensitive_key(field_name):
        return REDACTED

    if isinstance(value, (SecretStr, SecretBytes)):
        return REDACTED

    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        return _redact_embedded_secrets(value)

    if isinstance(value, bytes):
        # Never put raw binary content into logs.
        return f"<bytes:{len(value)}>"

    if isinstance(value, BaseModel):
        return redact_sensitive_data(value.model_dump(mode="python"))

    if isinstance(value, Mapping):
        return {
            str(key): redact_sensitive_data(
                nested_value,
                field_name=key,
            )
            for key, nested_value in value.items()
        }

    if isinstance(value, (list, tuple, set, frozenset)):
        return [redact_sensitive_data(item) for item in value]

    if isinstance(value, Enum):
        return redact_sensitive_data(value.value)

    if isinstance(value, (date, datetime, UUID)):
        return str(value)

    # Avoid potentially sensitive __repr__ output from arbitrary objects.
    return f"<{type(value).__name__}>"


def redact_sensitive_processor(
    _logger: WrappedLogger,
    _method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Structlog processor that redacts the complete event dictionary."""

    redacted = redact_sensitive_data(event_dict)
    return cast(EventDict, redacted)


def _add_runtime_metadata(
    service_name: str,
    environment: str,
) -> Processor:
    """Create a processor that adds stable service metadata."""

    def processor(
        _logger: WrappedLogger,
        _method_name: str,
        event_dict: EventDict,
    ) -> EventDict:
        event_dict.setdefault("service", service_name)
        event_dict.setdefault("environment", environment)
        event_dict.setdefault("log_schema_version", "1.0")
        return event_dict

    return processor


def configure_logging(
    logging_settings: LoggingSettings | None = None,
    *,
    service_name: str = "aurarisk",
    environment: str = "local",
    stream: TextIO | None = None,
) -> None:
    """Configure structlog and standard-library logging consistently."""

    config = logging_settings or get_settings().logging

    if not config.redact_sensitive_fields:
        raise ValueError("Sensitive log redaction cannot be disabled.")

    configured_level = getattr(
        logging,
        config.level.upper(),
        None,
    )

    if not isinstance(configured_level, int):
        raise ValueError(f"Unsupported logging level: {config.level}")

    output_stream = stream or sys.stdout

    timestamper = structlog.processors.TimeStamper(
        fmt="iso",
        utc=True,
    )

    runtime_metadata = _add_runtime_metadata(
        service_name,
        environment,
    )

    # Structlog-originated events.
    structlog_processors: list[Processor] = [
        # Structlog recommends this as the first processor.
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        runtime_metadata,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        redact_sensitive_processor,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    # Events from Uvicorn, FastAPI and other standard logging users.
    foreign_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        runtime_metadata,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.ExtraAdder(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        redact_sensitive_processor,
    ]

    if config.json_output:
        renderer: Processor = structlog.processors.JSONRenderer(sort_keys=True)
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=output_stream.isatty())

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=foreign_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(output_stream)
    handler.setLevel(configured_level)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(configured_level)

    # Route Uvicorn logs through the same formatter.
    for logger_name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
    ):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True

    logging.captureWarnings(True)

    structlog.configure(
        processors=structlog_processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> BoundLogger:
    """Return a type-safe structured logger."""

    return structlog.stdlib.get_logger(name)
