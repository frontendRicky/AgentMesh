import unittest
import inspect

from a2a_runtime.core.constants import (
    FileOperation,
    GateFailureType,
    ReviewStatus,
    RiskCategory,
    RiskDecisionAction,
    RiskSeverity,
    Role,
    TaskStatus,
)
from a2a_runtime.models.file_change_plan import FileChangePlan, FileChangePlanEntry
from a2a_runtime.models.state import State
from a2a_runtime.services.gate_service import GateService


def make_state(
    *,
    status: TaskStatus = TaskStatus.DEVELOPER_PROCESSING,
    human_review_status: ReviewStatus = ReviewStatus.APPROVED,
    current_agent: Role = Role.DEVELOPER,
) -> State:
    return State(
        task_id="T-2026-001",
        current_status=status,
        previous_status=status,
        current_agent=current_agent,
        next_agent=Role.QA,
        allowed_next_statuses=[],
        human_review_status=human_review_status,
        final_review_status=ReviewStatus.NOT_REQUIRED,
        updated_at="2026-05-12T10:00:00+08:00",
    )


def plan_entry(
    path: str = "src/settings.py",
    operation: FileOperation = FileOperation.MODIFY,
    *,
    allowed: bool = True,
    reason: str = "planned change",
    owner: str = "developer",
) -> FileChangePlanEntry:
    return FileChangePlanEntry(
        path=path,
        operation=operation,
        allowed=allowed,
        reason=reason,
        risk="low",
        owner=owner,
    )


class DeveloperGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = GateService()

    def test_all_conditions_satisfied_allows_write(self) -> None:
        result = self.service.check_developer_write(
            state=make_state(),
            target_path="src/settings.py",
            operation="modify",
            file_change_plan=FileChangePlan([plan_entry()]),
        )

        self.assertTrue(result.allowed)
        self.assertEqual(result.failure_type, GateFailureType.NONE)

    def test_current_status_not_developer_processing_is_gate_failure(self) -> None:
        result = self.service.check_developer_write(
            state=make_state(status=TaskStatus.HUMAN_REVIEW_REQUIRED),
            target_path="src/settings.py",
            operation="modify",
            file_change_plan=FileChangePlan([plan_entry()]),
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.failure_type, GateFailureType.GATE_FAILURE)

    def test_human_review_not_approved_is_gate_failure(self) -> None:
        result = self.service.check_developer_write(
            state=make_state(human_review_status=ReviewStatus.PENDING),
            target_path="src/settings.py",
            operation="modify",
            file_change_plan=FileChangePlan([plan_entry()]),
        )

        self.assertEqual(result.failure_type, GateFailureType.GATE_FAILURE)

    def test_current_agent_not_developer_is_gate_failure(self) -> None:
        result = self.service.check_developer_write(
            state=make_state(current_agent=Role.QA),
            target_path="src/settings.py",
            operation="modify",
            file_change_plan=FileChangePlan([plan_entry()]),
        )

        self.assertEqual(result.failure_type, GateFailureType.GATE_FAILURE)

    def test_signature_does_not_accept_current_agent_parameter(self) -> None:
        signature = inspect.signature(self.service.check_developer_write)

        self.assertNotIn("current_agent", signature.parameters)

    def test_file_not_in_file_change_plan_is_blocker_request(self) -> None:
        result = self.service.check_developer_write(
            state=make_state(),
            target_path="src/missing.py",
            operation="create",
            file_change_plan=FileChangePlan([plan_entry()]),
        )

        self.assertEqual(result.failure_type, GateFailureType.BLOCKER_REQUEST)

    def test_operation_mismatch_is_blocker_request(self) -> None:
        result = self.service.check_developer_write(
            state=make_state(),
            target_path="src/settings.py",
            operation="delete",
            file_change_plan=FileChangePlan([plan_entry(operation=FileOperation.MODIFY)]),
        )

        self.assertEqual(result.failure_type, GateFailureType.BLOCKER_REQUEST)

    def test_not_allowed_entry_is_blocker_request(self) -> None:
        result = self.service.check_developer_write(
            state=make_state(),
            target_path="src/settings.py",
            operation="modify",
            file_change_plan=FileChangePlan([plan_entry(allowed=False)]),
        )

        self.assertEqual(result.failure_type, GateFailureType.BLOCKER_REQUEST)

    def test_package_json_default_forbidden_is_not_allowed(self) -> None:
        result = self.service.check_developer_write(
            state=make_state(),
            target_path="package.json",
            operation="modify",
            file_change_plan=FileChangePlan([plan_entry(path="package.json")]),
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.failure_type, GateFailureType.RISK_DECISION_REQUIRED)

    def test_pnpm_lock_default_forbidden_requires_risk_decision(self) -> None:
        result = self.service.check_developer_write(
            state=make_state(),
            target_path="pnpm-lock.yaml",
            operation="modify",
            file_change_plan=FileChangePlan([plan_entry(path="pnpm-lock.yaml")]),
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.failure_type, GateFailureType.RISK_DECISION_REQUIRED)

    def test_github_workflow_default_forbidden_requires_risk_decision(self) -> None:
        result = self.service.check_developer_write(
            state=make_state(),
            target_path=".github/workflows/deploy.yml",
            operation="modify",
            file_change_plan=FileChangePlan([plan_entry(path=".github/workflows/deploy.yml")]),
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.failure_type, GateFailureType.RISK_DECISION_REQUIRED)

    def test_risk_decision_gate_result_can_build_risk_finding_input(self) -> None:
        result = self.service.check_developer_write(
            state=make_state(),
            target_path="package.json",
            operation="modify",
            file_change_plan=FileChangePlan([plan_entry(path="package.json")]),
        )

        kwargs = self.service.build_risk_finding_kwargs(
            task_id="T-2026-001",
            gate_result=result,
            target_path="package.json",
        )

        self.assertEqual(kwargs["severity"], RiskSeverity.P1_HIGH)
        self.assertEqual(kwargs["category"], RiskCategory.DEPENDENCY)
        self.assertIn(RiskDecisionAction.SEND_TO_ARCHITECT.value, kwargs["recommended_options"])
        self.assertIn(RiskDecisionAction.CANCEL_TASK.value, kwargs["recommended_options"])

    def test_new_file_missing_from_whitelist_is_blocker_request(self) -> None:
        result = self.service.check_developer_write(
            state=make_state(),
            target_path="src/new_file.py",
            operation="create",
            file_change_plan=FileChangePlan([plan_entry()]),
        )

        self.assertEqual(result.failure_type, GateFailureType.BLOCKER_REQUEST)

    def test_delete_without_reason_is_blocker_request(self) -> None:
        result = self.service.check_developer_write(
            state=make_state(),
            target_path="src/settings.py",
            operation="delete",
            file_change_plan=FileChangePlan(
                [plan_entry(operation=FileOperation.DELETE, reason="")],
            ),
        )

        self.assertEqual(result.failure_type, GateFailureType.BLOCKER_REQUEST)

    def test_missing_changed_files_audit_is_blocker_request(self) -> None:
        result = self.service.check_developer_write(
            state=make_state(),
            target_path="src/settings.py",
            operation="modify",
            file_change_plan=FileChangePlan([plan_entry()]),
            changed_files_audit_available=False,
        )

        self.assertEqual(result.failure_type, GateFailureType.BLOCKER_REQUEST)


if __name__ == "__main__":
    unittest.main()
