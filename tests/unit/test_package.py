"""
Basic tests for the AuraRisk Python package.

These tests verify that the package can be installed and that its central
domain values match the business concepts established in Phase 0.
"""

from aurarisk import __version__
from aurarisk.__main__ import main
from aurarisk.domain.enums import (
    ActionRiskLevel,
    ApprovalDecision,
    CaseCategory,
    CaseSeverity,
    CaseStatus,
    EvidenceClassification,
    InvestigationOutcome,
    UserRole,
    ValidationStatus,
)


def test_package_exposes_version() -> None:
    """The installed package must expose a usable application version."""

    assert __version__ == "0.1.0"


def test_command_line_entry_point_prints_application_details(
    capsys,
) -> None:
    """The application entry point should print its name and version."""

    main()

    captured_output = capsys.readouterr()

    assert "AuraRisk" in captured_output.out
    assert "0.1.0" in captured_output.out


def test_case_categories_match_phase_zero_taxonomy() -> None:
    """The Python domain model must preserve all business case categories."""

    expected_categories = {
        "FRAUD",
        "CREDIT_RISK",
        "TRANSACTION_MONITORING",
        "POLICY_COMPLIANCE",
        "MIXED_SIGNAL",
    }

    actual_categories = {category.value for category in CaseCategory}

    assert actual_categories == expected_categories


def test_case_severity_contains_expected_values() -> None:
    """Investigations must support all four configured severity levels."""

    assert {severity.value for severity in CaseSeverity} == {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    }


def test_case_lifecycle_contains_human_approval_state() -> None:
    """The workflow must explicitly represent cases awaiting human review."""

    assert CaseStatus.AWAITING_APPROVAL.value == "AWAITING_APPROVAL"


def test_evidence_classification_separates_facts_and_inferences() -> None:
    """Direct evidence and inferred conclusions must remain distinct."""

    assert EvidenceClassification.FACT != EvidenceClassification.INFERENCE

    assert EvidenceClassification.MODEL_OUTPUT != EvidenceClassification.RECOMMENDATION


def test_investigation_outcomes_include_account_hold_recommendation() -> None:
    """A consequential account-hold outcome must be explicitly represented."""

    assert InvestigationOutcome.RECOMMEND_ACCOUNT_HOLD.value == "RECOMMEND_ACCOUNT_HOLD"


def test_system_agent_role_remains_distinct_from_human_roles() -> None:
    """The service identity must not be confused with human reviewer roles."""

    assert UserRole.SYSTEM_AGENT.value == "system_agent"

    assert UserRole.SYSTEM_AGENT != UserRole.INVESTIGATION_SUPERVISOR


def test_prohibited_action_risk_level_is_explicit() -> None:
    """The policy engine must be able to represent prohibited actions."""

    assert ActionRiskLevel.PROHIBITED.value == "PROHIBITED"


def test_approval_decisions_support_approval_and_rejection() -> None:
    """A reviewer must be able to approve or reject a recommendation."""

    assert {decision.value for decision in ApprovalDecision} == {
        "APPROVED",
        "REJECTED",
    }


def test_validation_status_supports_fail_closed_workflows() -> None:
    """A failed validation must remain distinguishable from a passed one."""

    assert ValidationStatus.PASSED != ValidationStatus.FAILED
