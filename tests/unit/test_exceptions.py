"""Tests for controlled application exceptions."""

from aurarisk.core.exceptions import (
    ErrorCode,
    PolicyDeniedError,
)


def test_policy_error_has_stable_contract() -> None:
    error = PolicyDeniedError(
        "Account hold recommendation is not permitted.",
        details={
            "policy_id": "AURARISK-ACTION-APPROVAL",
        },
    )

    assert error.code is ErrorCode.POLICY_DENIED
    assert error.status_code == 403
    assert error.details["policy_id"] == ("AURARISK-ACTION-APPROVAL")
