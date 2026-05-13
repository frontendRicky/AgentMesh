import unittest

from a2a_runtime.core.constants import (
    ReviewStatus,
    RiskCategory,
    RiskDecisionAction,
    RiskSeverity,
    RiskStatus,
    Role,
    TaskStatus,
)
from a2a_runtime.models.risk import RuntimeRiskFinding
from a2a_runtime.models.risk_decision import RiskDecision
from a2a_runtime.models.file_change_plan import FileChangePlan, FileChangePlanEntry
from a2a_runtime.models.state import State
from a2a_runtime.core.constants import FileOperation
from a2a_runtime.core.constants import GateFailureType
from a2a_runtime.services.gate_service import GateCheckResult
from a2a_runtime.services.risk_prompt_regeneration_service import RiskPromptRegenerationService


class RiskPromptRegenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = RiskPromptRegenerationService()
        self.risk = RuntimeRiskFinding(
            risk_id="RISK-T-2026-001-001",
            task_id="T-2026-001",
            source_agent=Role.CONTROLLER,
            category=RiskCategory.SCOPE,
            severity=RiskSeverity.P1_HIGH,
            title="Scope risk",
            description="Scope expanded.",
            evidence="file outside plan",
            detected_at="2026-05-12T10:00:00+08:00",
            requires_human_decision=True,
            status=RiskStatus.WAITING_HUMAN_DECISION,
            affected_files=["package.json"],
            affected_artifacts=["file_change_plan"],
            recommended_options=[
                RiskDecisionAction.SEND_TO_PM.value,
                RiskDecisionAction.SEND_TO_ARCHITECT.value,
                RiskDecisionAction.SEND_TO_DEVELOPER.value,
                RiskDecisionAction.SEND_TO_QA.value,
                RiskDecisionAction.CONVERT_TO_BLOCKER.value,
            ],
            default_recommendation=RiskDecisionAction.SEND_TO_ARCHITECT.value,
        )

    def state(
        self,
        *,
        status: TaskStatus = TaskStatus.ARCHITECT_PROCESSING,
        human_review_status: ReviewStatus = ReviewStatus.PENDING,
        current_agent: Role = Role.CONTROLLER,
    ) -> State:
        return State(
            task_id="T-2026-001",
            current_status=status,
            previous_status=status,
            current_agent=current_agent,
            next_agent=None,
            allowed_next_statuses=[],
            human_review_status=human_review_status,
            final_review_status=ReviewStatus.NOT_REQUIRED,
            updated_at="2026-05-12T10:00:00+08:00",
        )

    def decision(self, action: RiskDecisionAction) -> RiskDecision:
        target_agent, target_status = {
            RiskDecisionAction.SEND_TO_PM: (Role.PM, TaskStatus.PM_PROCESSING),
            RiskDecisionAction.SEND_TO_ARCHITECT: (
                Role.ARCHITECT,
                TaskStatus.ARCHITECT_PROCESSING,
            ),
            RiskDecisionAction.SEND_TO_DEVELOPER: (
                Role.DEVELOPER,
                TaskStatus.DEVELOPER_PROCESSING,
            ),
            RiskDecisionAction.SEND_TO_QA: (Role.QA, TaskStatus.QA_PROCESSING),
            RiskDecisionAction.CONVERT_TO_BLOCKER: (Role.CONTROLLER, TaskStatus.BLOCKED),
        }[action]
        return RiskDecision(
            decision_id=f"RD-T-2026-001-{list(RiskDecisionAction).index(action) + 1:03d}",
            risk_id=self.risk.risk_id,
            task_id=self.risk.task_id,
            decision_by="zhangxia",
            decision_at="2026-05-12T10:00:00+08:00",
            decision=action,
            selected_option=action.value,
            reason="Human selected this option.",
            allowed_next_action=action.value,
            requires_regeneration=True,
            target_agent=target_agent,
            target_status=target_status,
        )

    def prompt_for(
        self,
        action: RiskDecisionAction,
        *,
        status: TaskStatus = TaskStatus.ARCHITECT_PROCESSING,
        human_review_status: ReviewStatus = ReviewStatus.PENDING,
    ) -> str:
        return self.service.generate_prompt_for_decision(
            risk=self.risk,
            decision=self.decision(action),
            state=self.state(status=status, human_review_status=human_review_status),
        )

    def test_send_to_pm_may_write_code_no(self) -> None:
        prompt = self.prompt_for(RiskDecisionAction.SEND_TO_PM)

        self.assertIn("May Write Code: no", prompt)

    def test_send_to_architect_may_write_code_no(self) -> None:
        prompt = self.prompt_for(RiskDecisionAction.SEND_TO_ARCHITECT)

        self.assertIn("May Write Code: no", prompt)

    def test_send_to_qa_may_write_code_no(self) -> None:
        prompt = self.prompt_for(RiskDecisionAction.SEND_TO_QA)

        self.assertIn("May Write Code: no", prompt)

    def test_send_to_developer_without_approved_human_review_may_write_code_no(self) -> None:
        prompt = self.prompt_for(
            RiskDecisionAction.SEND_TO_DEVELOPER,
            status=TaskStatus.DEVELOPER_PROCESSING,
            human_review_status=ReviewStatus.PENDING,
        )

        self.assertIn("May Write Code: no", prompt)

    def test_send_to_developer_with_approved_processing_may_write_code_yes(self) -> None:
        prompt = self.prompt_for(
            RiskDecisionAction.SEND_TO_DEVELOPER,
            status=TaskStatus.DEVELOPER_PROCESSING,
            human_review_status=ReviewStatus.APPROVED,
        )

        self.assertIn("May Write Code: no", prompt)

    def test_send_to_developer_allowed_path_may_write_code_yes(self) -> None:
        prompt = self.service.generate_prompt_for_decision(
            risk=self.risk,
            decision=self.decision(RiskDecisionAction.SEND_TO_DEVELOPER),
            state=self.state(
                status=TaskStatus.DEVELOPER_PROCESSING,
                human_review_status=ReviewStatus.APPROVED,
                current_agent=Role.DEVELOPER,
            ),
            target_path="src/app.py",
            operation="modify",
            file_change_plan=FileChangePlan(
                [
                    FileChangePlanEntry(
                        path="src/app.py",
                        operation=FileOperation.MODIFY,
                        allowed=True,
                        reason="planned",
                        risk="low",
                        owner="developer",
                    ),
                ],
            ),
        )

        self.assertIn("May Write Code: yes", prompt)

    def test_prompt_contains_required_risk_context(self) -> None:
        decision = self.decision(RiskDecisionAction.SEND_TO_ARCHITECT)
        prompt = self.service.generate_prompt_for_decision(
            risk=self.risk,
            decision=decision,
            state=self.state(),
        )

        self.assertIn(self.risk.risk_id, prompt)
        self.assertIn(decision.decision_id, prompt)
        self.assertIn("target_agent: architect", prompt)
        self.assertIn("## Expected Output Artifacts", prompt)

    def test_prompt_contains_forbidden_actions(self) -> None:
        prompt = self.prompt_for(RiskDecisionAction.SEND_TO_ARCHITECT)

        self.assertIn("## Forbidden Actions", prompt)
        self.assertIn("Do not decide on behalf of the user.", prompt)

    def test_prompt_does_not_auto_accept_risk(self) -> None:
        prompt = self.prompt_for(RiskDecisionAction.SEND_TO_ARCHITECT)

        self.assertNotIn("accept risk", prompt.lower())

    def test_convert_to_blocker_prompt_mentions_two_stage_blocker(self) -> None:
        prompt = self.prompt_for(RiskDecisionAction.CONVERT_TO_BLOCKER)

        self.assertIn("Two-stage Blocker", prompt)
        self.assertIn("formal blockers are Controller-only", prompt)

    def test_injected_gate_service_denied_controls_developer_may_write(self) -> None:
        class FakeGate:
            def check_developer_write(self, **kwargs):
                return GateCheckResult(
                    allowed=False,
                    failure_type=GateFailureType.GATE_FAILURE,
                    failed_conditions=["fake_denied"],
                    reason="fake gate denied",
                    recommended_next_action="stop",
                )

        service = RiskPromptRegenerationService(gate_service=FakeGate())
        prompt = service.generate_prompt_for_decision(
            risk=self.risk,
            decision=self.decision(RiskDecisionAction.SEND_TO_DEVELOPER),
            state=self.state(
                status=TaskStatus.DEVELOPER_PROCESSING,
                human_review_status=ReviewStatus.APPROVED,
                current_agent=Role.DEVELOPER,
            ),
            target_path="src/app.py",
            operation="modify",
            file_change_plan=FileChangePlan([plan_entry_for_test()]),
        )

        self.assertIn("May Write Code: no", prompt)
        self.assertIn("fake gate denied", prompt)

    def test_injected_gate_service_allowed_controls_developer_may_write(self) -> None:
        class FakeGate:
            def check_developer_write(self, **kwargs):
                return GateCheckResult(
                    allowed=True,
                    failure_type=GateFailureType.NONE,
                    failed_conditions=[],
                    reason="fake gate allowed",
                    recommended_next_action="go",
                )

        service = RiskPromptRegenerationService(gate_service=FakeGate())
        prompt = service.generate_prompt_for_decision(
            risk=self.risk,
            decision=self.decision(RiskDecisionAction.SEND_TO_DEVELOPER),
            state=self.state(
                status=TaskStatus.DEVELOPER_PROCESSING,
                human_review_status=ReviewStatus.APPROVED,
                current_agent=Role.DEVELOPER,
            ),
            target_path="src/app.py",
            operation="modify",
            file_change_plan=FileChangePlan([]),
        )

        self.assertIn("May Write Code: yes", prompt)
        self.assertIn("fake gate allowed", prompt)

    def test_risk_prompt_forbidden_section_uses_shared_default_paths(self) -> None:
        prompt = self.prompt_for(RiskDecisionAction.SEND_TO_ARCHITECT)

        self.assertIn("## Forbidden Actions", prompt)
        self.assertIn("package.json", prompt)
        self.assertIn("pnpm-lock.yaml", prompt)
        self.assertIn(".github/**", prompt)
        self.assertNotIn("## Files Not Allowed", prompt)


def plan_entry_for_test() -> FileChangePlanEntry:
    return FileChangePlanEntry(
        path="src/app.py",
        operation=FileOperation.MODIFY,
        allowed=True,
        reason="planned",
        risk="low",
        owner="developer",
    )


if __name__ == "__main__":
    unittest.main()
