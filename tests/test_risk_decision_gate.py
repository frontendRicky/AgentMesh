import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import (
    MessageType,
    ReviewStatus,
    RiskCategory,
    RiskDecisionAction,
    RiskSeverity,
    RiskStatus,
    Role,
    TaskStatus,
)
from a2a_runtime.core.errors import RiskDecisionError
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.state import State
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.risk_repo import RiskRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.services.risk_decision_service import RiskDecisionService


class RiskDecisionGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.paths = A2APaths(Path(self.tmp.name))
        self.state_repo = StateRepo(self.paths)
        self.message_repo = MessageRepo(self.paths)
        self.risk_repo = RiskRepo(self.message_repo)
        self.service = RiskDecisionService(
            risk_repo=self.risk_repo,
            state_repo=self.state_repo,
        )
        self.write_state()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_state(
        self,
        *,
        status: TaskStatus = TaskStatus.DEVELOPER_PROCESSING,
        agent: Role = Role.DEVELOPER,
        human_review_status: ReviewStatus = ReviewStatus.APPROVED,
    ) -> None:
        state = State(
            task_id="T-2026-001",
            current_status=status,
            previous_status=status,
            current_agent=agent,
            next_agent=None,
            allowed_next_statuses=[],
            human_review_status=human_review_status,
            final_review_status=ReviewStatus.NOT_REQUIRED,
            updated_at="2026-05-12T10:00:00+08:00",
        )
        self.state_repo.write("T-2026-001", state, actor=Role.CONTROLLER, body="# State")

    def create_risk(
        self,
        severity: RiskSeverity,
        *,
        options: list[str] | None = None,
    ):
        return self.service.create_risk_finding(
            task_id="T-2026-001",
            source_agent=Role.CONTROLLER,
            category=RiskCategory.SCOPE,
            severity=severity,
            title="Scope risk",
            description="The requested change expands scope.",
            evidence="package.json was requested",
            affected_files=["package.json"],
            affected_artifacts=["file_change_plan"],
            recommended_options=options
            if options is not None
            else [
                RiskDecisionAction.SEND_TO_ARCHITECT.value,
                RiskDecisionAction.ACCEPT_RISK_AND_CONTINUE.value,
                RiskDecisionAction.CANCEL_TASK.value,
            ],
            default_recommendation=RiskDecisionAction.SEND_TO_ARCHITECT.value,
        )

    def record(
        self,
        risk_id: str,
        action: RiskDecisionAction,
        *,
        decision_by: str = "zhangxia",
        reason: str = "Human decision recorded.",
    ):
        return self.service.record_decision(
            task_id="T-2026-001",
            risk_id=risk_id,
            decision_by=decision_by,
            selected_option=action.value,
            decision=action,
            reason=reason,
        )

    def test_p0_risk_waits_for_human_decision(self) -> None:
        risk = self.create_risk(
            RiskSeverity.P0_BLOCKER,
            options=[RiskDecisionAction.SEND_TO_ARCHITECT.value, RiskDecisionAction.CANCEL_TASK.value],
        )

        self.assertEqual(risk.status, RiskStatus.WAITING_HUMAN_DECISION)
        self.assertTrue(risk.requires_human_decision)

    def test_p1_risk_waits_for_human_decision(self) -> None:
        risk = self.create_risk(RiskSeverity.P1_HIGH)

        self.assertEqual(risk.status, RiskStatus.WAITING_HUMAN_DECISION)

    def test_p3_risk_does_not_block_flow(self) -> None:
        risk = self.create_risk(RiskSeverity.P3_LOW, options=[])

        self.assertEqual(risk.status, RiskStatus.OPEN)
        self.service.ensure_no_unresolved_blocking_risks("T-2026-001")

    def test_p0_does_not_allow_approve_continue(self) -> None:
        risk = self.create_risk(
            RiskSeverity.P0_BLOCKER,
            options=[RiskDecisionAction.APPROVE_CONTINUE.value, RiskDecisionAction.CANCEL_TASK.value],
        )

        with self.assertRaises(RiskDecisionError):
            self.record(risk.risk_id, RiskDecisionAction.APPROVE_CONTINUE)

    def test_p1_accept_risk_and_continue_requires_reason(self) -> None:
        risk = self.create_risk(RiskSeverity.P1_HIGH)

        with self.assertRaises(RiskDecisionError):
            self.record(risk.risk_id, RiskDecisionAction.ACCEPT_RISK_AND_CONTINUE, reason="")

    def test_controller_cannot_record_decision(self) -> None:
        risk = self.create_risk(RiskSeverity.P1_HIGH)

        with self.assertRaises(RiskDecisionError):
            self.record(
                risk.risk_id,
                RiskDecisionAction.SEND_TO_ARCHITECT,
                decision_by="controller",
            )

    def test_developer_cannot_record_decision(self) -> None:
        risk = self.create_risk(RiskSeverity.P1_HIGH)

        with self.assertRaises(RiskDecisionError):
            self.record(
                risk.risk_id,
                RiskDecisionAction.SEND_TO_ARCHITECT,
                decision_by="developer",
            )

    def test_record_decision_writes_from_human_message(self) -> None:
        risk = self.create_risk(RiskSeverity.P1_HIGH)
        self.record(risk.risk_id, RiskDecisionAction.SEND_TO_ARCHITECT)

        decisions = [
            message
            for message in self.risk_repo.list_risk_messages("T-2026-001")
            if message.intent == "risk_decision"
        ]
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0].from_agent, Role.HUMAN)

    def test_risk_review_request_message_type_is_status(self) -> None:
        self.create_risk(RiskSeverity.P1_HIGH)

        requests = [
            message
            for message in self.risk_repo.list_risk_messages("T-2026-001")
            if message.intent == "risk_review_request"
        ]
        self.assertEqual(requests[0].message_type, MessageType.STATUS)

    def test_risk_decision_message_type_is_review(self) -> None:
        risk = self.create_risk(RiskSeverity.P1_HIGH)
        self.record(risk.risk_id, RiskDecisionAction.SEND_TO_ARCHITECT)

        decisions = [
            message
            for message in self.risk_repo.list_risk_messages("T-2026-001")
            if message.intent == "risk_decision"
        ]
        self.assertEqual(decisions[0].message_type, MessageType.REVIEW)

    def test_unresolved_p0_p1_risk_blocks_progress(self) -> None:
        risk = self.create_risk(RiskSeverity.P1_HIGH)

        with self.assertRaisesRegex(RiskDecisionError, risk.risk_id):
            self.service.ensure_no_unresolved_blocking_risks("T-2026-001")

    def test_cancel_task_sets_state_to_cancelled(self) -> None:
        risk = self.create_risk(
            RiskSeverity.P1_HIGH,
            options=[RiskDecisionAction.CANCEL_TASK.value],
        )
        decision = self.record(risk.risk_id, RiskDecisionAction.CANCEL_TASK, reason="Stop task.")

        self.service.apply_decision(task_id="T-2026-001", decision=decision)

        self.assertEqual(self.state_repo.read("T-2026-001").current_status, TaskStatus.CANCELLED)

    def test_convert_to_blocker_does_not_write_formal_blocker(self) -> None:
        risk = self.create_risk(
            RiskSeverity.P1_HIGH,
            options=[RiskDecisionAction.CONVERT_TO_BLOCKER.value],
        )
        decision = self.record(risk.risk_id, RiskDecisionAction.CONVERT_TO_BLOCKER)

        self.service.apply_decision(task_id="T-2026-001", decision=decision)

        blockers_dir = self.paths.blockers_dir("T-2026-001")
        self.assertFalse(blockers_dir.exists() and list(blockers_dir.glob("*.md")))

    def test_send_to_architect_generates_dispatch_prompt(self) -> None:
        risk = self.create_risk(RiskSeverity.P1_HIGH)
        decision = self.record(risk.risk_id, RiskDecisionAction.SEND_TO_ARCHITECT)

        self.service.apply_decision(task_id="T-2026-001", decision=decision)

        dispatch = [
            path
            for path in self.message_repo.list_messages("T-2026-001")
            if path.name.endswith("risk-decision-dispatch.md")
        ]
        self.assertEqual(len(dispatch), 1)
        body = dispatch[0].read_text(encoding="utf-8")
        self.assertIn("target_agent: architect", body)
        self.assertIn(decision.decision_id, body)

    def test_accepted_risk_is_available_for_reports(self) -> None:
        risk = self.create_risk(RiskSeverity.P1_HIGH)
        decision = self.record(risk.risk_id, RiskDecisionAction.ACCEPT_RISK_AND_CONTINUE)

        updated = self.service.apply_decision(task_id="T-2026-001", decision=decision)

        self.assertEqual(updated.status, RiskStatus.ACCEPTED)
        self.assertEqual(self.risk_repo.find_decision("T-2026-001", risk.risk_id), decision)
        self.assertNotIn(risk.risk_id, [item.risk_id for item in self.risk_repo.list_open_risks("T-2026-001")])


if __name__ == "__main__":
    unittest.main()
