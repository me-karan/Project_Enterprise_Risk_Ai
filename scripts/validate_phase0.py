"""
Validate the AuraRisk Phase 0 product-definition artifacts.

This script checks:

1. Required project files exist.
2. Gold cases are complete and uniquely identified.
3. Approval policies deny unknown or prohibited actions.
4. Business outcomes map to explicit policy actions.
5. Gold-case approval expectations match the action mapping.
6. Release gates contain valid operators and thresholds.
7. Sensitive files are covered by .gitignore.

Run:

    uv run python scripts/validate_phase0.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# Resolve the repository root without depending on the caller's current
# working directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# These files represent the minimum deliverables required to complete Phase 0.
REQUIRED_FILES = (
    "README.md",
    ".gitignore",
    "docs/products/business_problem.md",
    "docs/products/investigation_taxonomy.md",
    "docs/products/gold_cases.yaml",
    "docs/products/decision_and_approval_policy.md",
    "docs/products/non_functional_requirements.md",
    "config/policies/action_approval_policy.yaml",
    "config/policies/outcome_action_mapping.yaml",
    "config/quality/release_gates.yaml",
)


ALLOWED_CASE_CATEGORIES = {
    "FRAUD",
    "CREDIT_RISK",
    "TRANSACTION_MONITORING",
    "POLICY_COMPLIANCE",
    "MIXED_SIGNAL",
}


ALLOWED_CASE_SEVERITIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}


ALLOWED_AGENT_NAMES = {
    "customer_context",
    "fraud",
    "credit_risk",
    "transaction",
    "policy_rag",
    "investigation",
    "validator",
    "reporting",
}


ALLOWED_GATE_OPERATORS = {
    "EQ",
    "GT",
    "GTE",
    "LT",
    "LTE",
}


ALLOWED_ACTION_RISK_LEVELS = {
    "READ_ONLY",
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
    "PROHIBITED",
}


@dataclass
class ValidationIssue:
    """Represent a single actionable validation error."""

    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.location}: {self.message}"


@dataclass
class ValidationSummary:
    """Collect validation results for the final console report."""

    gold_case_count: int = 0
    covered_categories: set[str] = field(default_factory=set)
    policy_action_count: int = 0
    outcome_mapping_count: int = 0
    release_gate_count: int = 0


class PhaseZeroValidator:
    """Validate all Phase 0 artifacts and cross-file relationships."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.issues: list[ValidationIssue] = []
        self.summary = ValidationSummary()

        self.gold_cases: dict[str, Any] = {}
        self.approval_policy: dict[str, Any] = {}
        self.outcome_mapping: dict[str, Any] = {}
        self.release_gates: dict[str, Any] = {}

    def add_issue(self, location: str, message: str) -> None:
        """Record a validation issue without stopping the remaining checks."""

        self.issues.append(
            ValidationIssue(
                location=location,
                message=message,
            )
        )

    def validate_required_files(self) -> None:
        """Ensure that required documentation and configuration files exist."""

        for relative_path in REQUIRED_FILES:
            absolute_path = self.project_root / relative_path

            if not absolute_path.is_file():
                self.add_issue(
                    relative_path,
                    "Required file does not exist.",
                )
                continue

            if absolute_path.stat().st_size == 0:
                self.add_issue(
                    relative_path,
                    "Required file is empty.",
                )

    def load_yaml_file(self, relative_path: str) -> dict[str, Any]:
        """
        Safely load a YAML file and require a mapping at the document root.

        yaml.safe_load avoids constructing arbitrary Python objects from YAML.
        """

        absolute_path = self.project_root / relative_path

        if not absolute_path.is_file():
            return {}

        try:
            content = absolute_path.read_text(encoding="utf-8")

            parsed_content = yaml.safe_load(content)

        except OSError as exc:
            self.add_issue(
                relative_path,
                f"Could not read file: {exc}",
            )
            return {}

        except yaml.YAMLError as exc:
            self.add_issue(
                relative_path,
                f"Invalid YAML: {exc}",
            )
            return {}

        if not isinstance(parsed_content, dict):
            self.add_issue(
                relative_path,
                "The YAML document must contain a top-level mapping.",
            )
            return {}

        return parsed_content

    def load_configuration(self) -> None:
        """Load all machine-readable Phase 0 configuration documents."""

        self.gold_cases = self.load_yaml_file(
            "docs/products/gold_cases.yaml"
        )

        self.approval_policy = self.load_yaml_file(
            "config/policies/action_approval_policy.yaml"
        )

        self.outcome_mapping = self.load_yaml_file(
            "config/policies/outcome_action_mapping.yaml"
        )

        self.release_gates = self.load_yaml_file(
            "config/quality/release_gates.yaml"
        )

    def validate_gitignore(self) -> None:
        """
        Ensure local secrets and virtual environments are not committed.

        This checks that the required patterns are present. It is not a
        replacement for a dedicated secret-scanning tool in CI.
        """

        relative_path = ".gitignore"
        gitignore_path = self.project_root / relative_path

        if not gitignore_path.is_file():
            return

        lines = {
            line.strip()
            for line in gitignore_path.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        required_patterns = {
            ".env",
            ".venv/",
            "__pycache__/",
            "node_modules/",
        }

        for required_pattern in sorted(required_patterns):
            if required_pattern not in lines:
                self.add_issue(
                    relative_path,
                    f"Missing required ignore rule: {required_pattern}",
                )

        if "uv.lock" in lines:
            self.add_issue(
                relative_path,
                "uv.lock must be committed and must not be ignored.",
            )

    def validate_roles(self) -> dict[str, Any]:
        """Validate role definitions and return the configured role mapping."""

        location = "config/policies/action_approval_policy.yaml"
        roles = self.approval_policy.get("roles")

        if not isinstance(roles, dict) or not roles:
            self.add_issue(
                location,
                "The approval policy must define at least one role.",
            )
            return {}

        system_agent = roles.get("system_agent")

        if not isinstance(system_agent, dict):
            self.add_issue(
                location,
                "The system_agent role must be defined.",
            )

        elif system_agent.get("human") is not False:
            self.add_issue(
                location,
                "The system_agent role must be marked human: false.",
            )

        for role_name, role_definition in roles.items():
            if not isinstance(role_definition, dict):
                self.add_issue(
                    location,
                    f"Role {role_name!r} must contain a mapping.",
                )
                continue

            if not isinstance(role_definition.get("human"), bool):
                self.add_issue(
                    location,
                    f"Role {role_name!r} must define a boolean human field.",
                )

        return roles

    def validate_approval_policy(self) -> None:
        """Check deny-by-default behavior and approval-policy integrity."""

        location = "config/policies/action_approval_policy.yaml"

        policy_details = self.approval_policy.get("policy")

        if not isinstance(policy_details, dict):
            self.add_issue(
                location,
                "Missing policy metadata.",
            )
            return

        if policy_details.get("default_effect") != "DENY":
            self.add_issue(
                location,
                "The approval policy must deny unknown actions by default.",
            )

        roles = self.validate_roles()
        actions = self.approval_policy.get("actions")

        if not isinstance(actions, dict) or not actions:
            self.add_issue(
                location,
                "The approval policy must define at least one action.",
            )
            return

        self.summary.policy_action_count = len(actions)

        for action_name, action_definition in actions.items():
            action_location = f"{location}::{action_name}"

            if not isinstance(action_definition, dict):
                self.add_issue(
                    action_location,
                    "The action definition must contain a mapping.",
                )
                continue

            risk_level = action_definition.get("risk_level")

            if risk_level not in ALLOWED_ACTION_RISK_LEVELS:
                self.add_issue(
                    action_location,
                    f"Unsupported risk level: {risk_level!r}.",
                )

            approvals_required = action_definition.get(
                "approvals_required"
            )

            if (
                not isinstance(approvals_required, int)
                or isinstance(approvals_required, bool)
                or approvals_required < 0
            ):
                self.add_issue(
                    action_location,
                    "approvals_required must be a non-negative integer.",
                )
                continue

            if action_definition.get("audit_required") is not True:
                self.add_issue(
                    action_location,
                    "Every action must require an audit record.",
                )

            if risk_level == "PROHIBITED":
                if (
                    action_definition.get("execution_mode")
                    != "PROHIBITED"
                ):
                    self.add_issue(
                        action_location,
                        "Prohibited actions must use PROHIBITED execution.",
                    )

                continue

            requester_roles = action_definition.get(
                "requester_roles",
                [],
            )

            if not isinstance(requester_roles, list) or not requester_roles:
                self.add_issue(
                    action_location,
                    "Non-prohibited actions require requester_roles.",
                )
            else:
                for role_name in requester_roles:
                    if role_name not in roles:
                        self.add_issue(
                            action_location,
                            f"Unknown requester role: {role_name!r}.",
                        )

            if approvals_required > 0:
                approver_roles = action_definition.get(
                    "approver_roles",
                    [],
                )

                if (
                    not isinstance(approver_roles, list)
                    or not approver_roles
                ):
                    self.add_issue(
                        action_location,
                        "Approval-required actions must define approver_roles.",
                    )
                    continue

                for role_name in approver_roles:
                    role_definition = roles.get(role_name)

                    if not isinstance(role_definition, dict):
                        self.add_issue(
                            action_location,
                            f"Unknown approver role: {role_name!r}.",
                        )
                        continue

                    if role_definition.get("human") is not True:
                        self.add_issue(
                            action_location,
                            f"Non-human role cannot approve: {role_name!r}.",
                        )

                if action_definition.get("validator_required") is not True:
                    self.add_issue(
                        action_location,
                        "Approval-required actions must require validation.",
                    )

                if (
                    action_definition.get("human_rationale_required")
                    is not True
                ):
                    self.add_issue(
                        action_location,
                        "Approval-required actions must require rationale.",
                    )

            if risk_level in {"HIGH", "CRITICAL"}:
                if approvals_required < 1:
                    self.add_issue(
                        action_location,
                        "High-impact actions require human approval.",
                    )

                if (
                    action_definition.get("self_approval_allowed")
                    is not False
                ):
                    self.add_issue(
                        action_location,
                        "High-impact actions must prohibit self-approval.",
                    )

            if risk_level == "CRITICAL":
                if approvals_required < 2:
                    self.add_issue(
                        action_location,
                        "Critical actions require at least two approvals.",
                    )

                if (
                    action_definition.get(
                        "distinct_approvers_required"
                    )
                    is not True
                ):
                    self.add_issue(
                        action_location,
                        "Critical actions require distinct approvers.",
                    )

    def validate_outcome_mapping(self) -> None:
        """Verify that business outcomes map to defined policy actions."""

        location = "config/policies/outcome_action_mapping.yaml"

        mapping_policy = self.outcome_mapping.get("mapping_policy")

        if not isinstance(mapping_policy, dict):
            self.add_issue(
                location,
                "Missing mapping_policy metadata.",
            )
            return

        if mapping_policy.get("default_effect") != "DENY":
            self.add_issue(
                location,
                "Unknown outcomes must be denied by default.",
            )

        mappings = self.outcome_mapping.get("mappings")

        if not isinstance(mappings, dict) or not mappings:
            self.add_issue(
                location,
                "The outcome mapping must define at least one outcome.",
            )
            return

        self.summary.outcome_mapping_count = len(mappings)

        actions = self.approval_policy.get("actions", {})

        for outcome_name, mapping_definition in mappings.items():
            mapping_location = f"{location}::{outcome_name}"

            if not isinstance(mapping_definition, dict):
                self.add_issue(
                    mapping_location,
                    "Each outcome mapping must contain a mapping.",
                )
                continue

            action_name = mapping_definition.get("policy_action")

            if action_name not in actions:
                self.add_issue(
                    mapping_location,
                    f"Mapped policy action does not exist: {action_name!r}.",
                )
                continue

            for required_boolean in (
                "final_confirmation_required",
                "consequential_approval_required",
            ):
                if not isinstance(
                    mapping_definition.get(required_boolean),
                    bool,
                ):
                    self.add_issue(
                        mapping_location,
                        f"{required_boolean} must be true or false.",
                    )

            action_definition = actions[action_name]

            if mapping_definition.get(
                "final_confirmation_required"
            ) is True:
                if action_definition.get("approvals_required", 0) < 1:
                    self.add_issue(
                        mapping_location,
                        "Final confirmation requires at least one approver.",
                    )

            if mapping_definition.get(
                "consequential_approval_required"
            ) is True:
                if action_definition.get("risk_level") not in {
                    "HIGH",
                    "CRITICAL",
                }:
                    self.add_issue(
                        mapping_location,
                        "Consequential outcomes require HIGH or CRITICAL actions.",
                    )

    def validate_gold_cases(self) -> None:
        """Validate case completeness and alignment with policy mappings."""

        location = "docs/products/gold_cases.yaml"

        metadata = self.gold_cases.get("metadata")

        if not isinstance(metadata, dict):
            self.add_issue(
                location,
                "Gold-case metadata is missing.",
            )
            return

        if metadata.get("data_classification") != "SYNTHETIC":
            self.add_issue(
                location,
                "Gold cases must be explicitly classified as SYNTHETIC.",
            )

        cases = self.gold_cases.get("cases")

        if not isinstance(cases, list) or not cases:
            self.add_issue(
                location,
                "Gold cases must contain a non-empty cases list.",
            )
            return

        self.summary.gold_case_count = len(cases)

        quality_policy = self.release_gates.get("quality_policy", {})

        minimum_case_count = quality_policy.get(
            "minimum_gold_case_count",
            20,
        )

        if len(cases) < minimum_case_count:
            self.add_issue(
                location,
                (
                    f"Expected at least {minimum_case_count} gold cases; "
                    f"found {len(cases)}."
                ),
            )

        seen_case_ids: set[str] = set()

        mappings = self.outcome_mapping.get("mappings", {})

        for case in cases:
            if not isinstance(case, dict):
                self.add_issue(
                    location,
                    "Each gold case must contain a mapping.",
                )
                continue

            case_id = case.get("case_id", "<missing>")
            case_location = f"{location}::{case_id}"

            if not isinstance(case_id, str) or not case_id.strip():
                self.add_issue(
                    case_location,
                    "Each case requires a non-empty case_id.",
                )
                continue

            if case_id in seen_case_ids:
                self.add_issue(
                    case_location,
                    "Duplicate gold-case identifier.",
                )

            seen_case_ids.add(case_id)

            category = case.get("category")

            if category not in ALLOWED_CASE_CATEGORIES:
                self.add_issue(
                    case_location,
                    f"Unsupported case category: {category!r}.",
                )
            else:
                self.summary.covered_categories.add(category)

            severity = case.get("severity")

            if severity not in ALLOWED_CASE_SEVERITIES:
                self.add_issue(
                    case_location,
                    f"Unsupported severity: {severity!r}.",
                )

            trigger = case.get("trigger")

            if not isinstance(trigger, dict) or not trigger.get("type"):
                self.add_issue(
                    case_location,
                    "Each case requires a trigger with a type.",
                )

            customer_context = case.get("customer_context")

            if (
                not isinstance(customer_context, dict)
                or not customer_context.get("customer_id")
            ):
                self.add_issue(
                    case_location,
                    "Each case requires customer_context.customer_id.",
                )

            for field_name in (
                "required_evidence",
                "expected_agents",
                "evaluation_checks",
            ):
                field_value = case.get(field_name)

                if not isinstance(field_value, list) or not field_value:
                    self.add_issue(
                        case_location,
                        f"{field_name} must be a non-empty list.",
                    )

            expected_agents = case.get("expected_agents", [])

            if isinstance(expected_agents, list):
                for agent_name in expected_agents:
                    if agent_name not in ALLOWED_AGENT_NAMES:
                        self.add_issue(
                            case_location,
                            f"Unsupported agent name: {agent_name!r}.",
                        )

            expected_outcome = case.get("expected_outcome")

            if expected_outcome not in mappings:
                self.add_issue(
                    case_location,
                    (
                        "Expected outcome has no policy mapping: "
                        f"{expected_outcome!r}."
                    ),
                )
                continue

            requires_human_approval = case.get(
                "requires_human_approval"
            )

            if not isinstance(requires_human_approval, bool):
                self.add_issue(
                    case_location,
                    "requires_human_approval must be true or false.",
                )
                continue

            expected_consequential_approval = mappings[
                expected_outcome
            ].get(
                "consequential_approval_required"
            )

            if (
                requires_human_approval
                != expected_consequential_approval
            ):
                self.add_issue(
                    case_location,
                    (
                        "Gold-case approval expectation conflicts with "
                        "the outcome-to-action policy."
                    ),
                )

        missing_categories = (
            ALLOWED_CASE_CATEGORIES
            - self.summary.covered_categories
        )

        if missing_categories:
            self.add_issue(
                location,
                (
                    "Gold cases do not cover categories: "
                    f"{sorted(missing_categories)}."
                ),
            )

    def validate_release_gates(self) -> None:
        """Validate release-gate structure and non-waivable categories."""

        location = "config/quality/release_gates.yaml"

        quality_policy = self.release_gates.get("quality_policy")

        if not isinstance(quality_policy, dict):
            self.add_issue(
                location,
                "Missing quality_policy metadata.",
            )
            return

        if (
            quality_policy.get("release_rule")
            != "ALL_BLOCKING_GATES_PASS"
        ):
            self.add_issue(
                location,
                "Release policy must require all blocking gates to pass.",
            )

        non_waivable_categories = set(
            quality_policy.get("non_waivable_categories", [])
        )

        required_non_waivable = {
            "SECURITY",
            "SAFETY",
            "APPROVAL",
            "AUDIT",
        }

        missing_non_waivable = (
            required_non_waivable
            - non_waivable_categories
        )

        if missing_non_waivable:
            self.add_issue(
                location,
                (
                    "Missing non-waivable categories: "
                    f"{sorted(missing_non_waivable)}."
                ),
            )

        gates = self.release_gates.get("release_gates")

        if not isinstance(gates, list) or not gates:
            self.add_issue(
                location,
                "release_gates must be a non-empty list.",
            )
            return

        self.summary.release_gate_count = len(gates)

        seen_gate_ids: set[str] = set()

        for gate in gates:
            if not isinstance(gate, dict):
                self.add_issue(
                    location,
                    "Each release gate must contain a mapping.",
                )
                continue

            gate_id = gate.get("gate_id", "<missing>")
            gate_location = f"{location}::{gate_id}"

            if not isinstance(gate_id, str) or not gate_id.strip():
                self.add_issue(
                    gate_location,
                    "Every release gate requires a gate_id.",
                )
                continue

            if gate_id in seen_gate_ids:
                self.add_issue(
                    gate_location,
                    "Duplicate release-gate identifier.",
                )

            seen_gate_ids.add(gate_id)

            operator = gate.get("operator")

            if operator not in ALLOWED_GATE_OPERATORS:
                self.add_issue(
                    gate_location,
                    f"Unsupported comparison operator: {operator!r}.",
                )

            threshold = gate.get("threshold")

            if (
                not isinstance(threshold, int | float)
                or isinstance(threshold, bool)
            ):
                self.add_issue(
                    gate_location,
                    "Threshold must contain a numeric value.",
                )

            blocking = gate.get("blocking")

            if not isinstance(blocking, bool):
                self.add_issue(
                    gate_location,
                    "blocking must be true or false.",
                )

            if gate.get("category") in non_waivable_categories:
                if blocking is not True:
                    self.add_issue(
                        gate_location,
                        "Non-waivable categories must use blocking gates.",
                    )

    def run(self) -> bool:
        """Run every validation stage and return whether all checks passed."""

        self.validate_required_files()
        self.load_configuration()
        self.validate_gitignore()
        self.validate_approval_policy()
        self.validate_outcome_mapping()
        self.validate_release_gates()
        self.validate_gold_cases()

        return not self.issues

    def print_report(self) -> None:
        """Print an actionable validation report."""

        print("\nAuraRisk Phase 0 validation")
        print("-" * 32)

        if self.issues:
            print(f"Status: FAILED ({len(self.issues)} issues)\n")

            for issue in self.issues:
                print(f"- {issue}")

            return

        print("Status: PASSED")
        print(f"Gold cases: {self.summary.gold_case_count}")

        categories = ", ".join(
            sorted(self.summary.covered_categories)
        )

        print(f"Covered categories: {categories}")

        print(
            f"Policy actions: "
            f"{self.summary.policy_action_count}"
        )

        print(
            f"Outcome mappings: "
            f"{self.summary.outcome_mapping_count}"
        )

        print(
            f"Release gates: "
            f"{self.summary.release_gate_count}"
        )


def main() -> int:
    """Return a shell-friendly exit code for local runs and CI."""

    validator = PhaseZeroValidator(
        project_root=PROJECT_ROOT,
    )

    passed = validator.run()

    validator.print_report()

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())