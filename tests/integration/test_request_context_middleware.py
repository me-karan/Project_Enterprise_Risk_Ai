"""Integration tests for middleware and API error responses."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from aurarisk.api.errors import register_exception_handlers
from aurarisk.api.middleware import RequestContextMiddleware
from aurarisk.core.context import (
    get_correlation_id,
    get_request_id,
)
from aurarisk.core.exceptions import PolicyDeniedError


def create_test_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)

    @app.get("/ok")
    async def ok() -> dict[str, str | None]:
        return {
            "request_id": get_request_id(),
            "correlation_id": get_correlation_id(),
        }

    @app.get("/policy-denied")
    async def policy_denied() -> None:
        raise PolicyDeniedError(
            "Requested action is not permitted.",
            details={"policy_id": "TEST-POLICY"},
        )

    @app.get("/validated")
    async def validated(quantity: int) -> dict[str, int]:
        return {"quantity": quantity}

    @app.get("/unexpected")
    async def unexpected() -> None:
        raise RuntimeError("password=must-never-appear-in-response")

    return app


def test_request_identifiers_are_propagated() -> None:
    app = create_test_app()

    with TestClient(app) as client:
        response = client.get(
            "/ok",
            headers={
                "X-Request-ID": "request-123",
                "X-Correlation-ID": "correlation-456",
            },
        )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "request-123"
    assert response.headers["X-Correlation-ID"] == "correlation-456"
    assert response.json() == {
        "request_id": "request-123",
        "correlation_id": "correlation-456",
    }


def test_policy_error_uses_standard_contract() -> None:
    app = create_test_app()

    with TestClient(app) as client:
        response = client.get("/policy-denied")

    payload = response.json()

    assert response.status_code == 403
    assert payload["error"]["code"] == "POLICY_DENIED"
    assert payload["error"]["request_id"]
    assert payload["error"]["details"] == {"policy_id": "TEST-POLICY"}


def test_validation_response_does_not_echo_input() -> None:
    app = create_test_app()

    with TestClient(app) as client:
        response = client.get(
            "/validated",
            params={"quantity": "private-customer-value"},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert "private-customer-value" not in response.text
    assert '"input"' not in response.text


def test_unexpected_error_is_not_exposed() -> None:
    app = create_test_app()

    with TestClient(
        app,
        raise_server_exceptions=False,
    ) as client:
        response = client.get("/unexpected")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert "password" not in response.text
    assert response.headers["X-Request-ID"]
