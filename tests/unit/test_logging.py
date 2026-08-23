"""Tests for structured logging and redaction."""

import json
import logging
from io import StringIO

from aurarisk.core.context import (
    create_request_context,
    request_context,
)
from aurarisk.core.logging import (
    REDACTED,
    configure_logging,
    get_logger,
)
from aurarisk.core.settings import LoggingSettings


def test_json_log_redacts_nested_sensitive_data() -> None:
    output = StringIO()

    configure_logging(
        LoggingSettings(
            level="INFO",
            json_output=True,
            redact_sensitive_fields=True,
        ),
        environment="test",
        stream=output,
    )

    context = create_request_context(
        "request-123",
        "correlation-456",
    )

    with request_context(context):
        get_logger("tests.security").info(
            "customer_lookup_completed",
            password="do-not-log",
            prompt_tokens=42,
            customer={
                "customer_id": "CUSTOMER-99",
                "risk_tier": "HIGH",
            },
            authorization="Bearer private-token",
        )

    payload = json.loads(output.getvalue().strip().splitlines()[-1])

    assert payload["event"] == "customer_lookup_completed"
    assert payload["request_id"] == "request-123"
    assert payload["correlation_id"] == "correlation-456"
    assert payload["password"] == REDACTED
    assert payload["authorization"] == REDACTED
    assert payload["customer"]["customer_id"] == REDACTED
    assert payload["customer"]["risk_tier"] == "HIGH"

    # Observability metrics must not be mistaken for credentials.
    assert payload["prompt_tokens"] == 42


def test_standard_library_logs_use_json_formatter() -> None:
    output = StringIO()

    configure_logging(
        LoggingSettings(
            level="INFO",
            json_output=True,
            redact_sensitive_fields=True,
        ),
        environment="test",
        stream=output,
    )

    logging.getLogger("dependency").warning("dependency_warning")

    payload = json.loads(output.getvalue().strip().splitlines()[-1])

    assert payload["event"] == "dependency_warning"
    assert payload["logger"] == "dependency"
    assert payload["level"] == "warning"
