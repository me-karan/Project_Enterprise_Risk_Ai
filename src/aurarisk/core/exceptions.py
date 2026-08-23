"""Application exception hierarchy.

These exceptions represent expected business or application failures.
Unexpected programming failures remain ordinary Python exceptions.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TypeAlias


JSONValue: TypeAlias = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]


class ErrorCode(StrEnum):
    """Stable machine-readable API error codes."""

    BAD_REQUEST = "BAD_REQUEST"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    POLICY_DENIED = "POLICY_DENIED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    UPSTREAM_UNAVAILABLE = "UPSTREAM_UNAVAILABLE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AuraRiskError(Exception):
    """Base class for controlled, public-safe application errors."""

    code = ErrorCode.INTERNAL_ERROR
    status_code = 500

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, JSONValue] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ResourceNotFoundError(AuraRiskError):
    code = ErrorCode.NOT_FOUND
    status_code = 404

    def __init__(self, resource: str) -> None:
        super().__init__(f"{resource} was not found.")


class ConflictError(AuraRiskError):
    code = ErrorCode.CONFLICT
    status_code = 409


class AuthenticationError(AuraRiskError):
    code = ErrorCode.UNAUTHENTICATED
    status_code = 401


class AuthorizationError(AuraRiskError):
    code = ErrorCode.FORBIDDEN
    status_code = 403


class PolicyDeniedError(AuraRiskError):
    code = ErrorCode.POLICY_DENIED
    status_code = 403


class ApprovalRequiredError(AuraRiskError):
    code = ErrorCode.APPROVAL_REQUIRED
    status_code = 409


class RateLimitError(AuraRiskError):
    code = ErrorCode.RATE_LIMITED
    status_code = 429


class UpstreamServiceError(AuraRiskError):
    code = ErrorCode.UPSTREAM_UNAVAILABLE
    status_code = 503
