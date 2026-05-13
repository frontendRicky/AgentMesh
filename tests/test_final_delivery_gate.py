import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import (
    ArtifactStatus,
    ArtifactType,
    ReviewIssueSeverity,
    ReviewStatus,
    ReviewType,
    ReviewVerdict,
    Role,
    RiskCategory,
    RiskDecisionAction,
    RiskSeverity,
    TaskPriority,
    TaskStatus,
    TaskType,
    ValidationOutcome,
)
from a2a_runtime.core.errors import FinalDeliveryError
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.artifact import Artifact
from a2a_runtime.models.review import ReviewIssue, ReviewRecord
from a2a_runtime.models.state import BlockedContext, State
from a2a_runtime.models.task import Task, TaskScope
from a2a_runtime.repositories.artifact_repo import ArtifactRepo
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.review_repo import ReviewRepo
from a2a_runtime.repositories.risk_repo import RiskRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.repositories.task_repo import TaskRepo
from a2a_runtime.services.final_delivery_service import FinalDeliveryService
from a2a_runtime.services.risk_decision_service import RiskDecisionService


class FinalDeliveryGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.paths = A2APaths(Path(self.tmp.name))
        self.task_repo = TaskRepo(self.paths)
        self.state_repo = StateRepo(self.paths)
        self.artifact_repo = ArtifactRepo(self.paths)
        self.message_repo = MessageRepo(self.paths)
        self.review_repo = ReviewRepo(self.paths)
        self.risk_repo = RiskRepo(self.message_repo)
        self.risk_decision_service = RiskDecisionService(
            risk_repo=self.risk_repo,
            state_repo=self.state_repo,
        )
        self.service = FinalDeliveryService(
            state_repo=self.state_repo,
            task_repo=self.task_repo,
            artifact_repo=self.artifact_repo,
            review_repo=self.review_repo,
            risk_repo=self.risk_repo,
        )
        self.write_task()
        self.write_completed_state()
        self.write_all_artifacts()
        self.write_reviews()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_task(self) -> None:
        self.task_repo.create(
            Task(
                task_id="T-2026-001",
                task_type=TaskType.FEATURE,
                task_title="Feature",
                created_by="user",
                human_owner="zhangxia",
                priority=TaskPriority.P1,
                scope=TaskScope(in_scope=["feature"], out_of_scope=["none"]),
                constraints=["standard library"],
                required_artifacts=[],
                created_at="2026-05-12T10:00:00+08:00",
            ),
        )

    def write_completed_state(
        self,
        *,
        status: TaskStatus = TaskStatus.COMPLETED,
        final_review_status: ReviewStatus = ReviewStatus.APPROVED,
        active_blocker: str | None = None,
        blocked_context: BlockedContext | None = None,
    ) -> None:
        state = State(
            task_id="T-2026-001",
            current_status=status,
            previous_status=TaskStatus.FINAL_REVIEW_REQUIRED,
            current_agent=Role.CONTROLLER,
            next_agent=None,
            allowed_next_statuses=[],
            human_review_status=ReviewStatus.APPROVED,
            final_review_status=final_review_status,
            updated_at="2026-05-12T10:00:00+08:00",
            active_blocker=active_blocker,
            blockers_history=[active_blocker] if active_blocker else [],
            blocked_context=blocked_context,
        )
        self.state_repo.write("T-2026-001", state, actor=Role.CONTROLLER, body="# State")

    def write_all_artifacts(self, *, test_report_result: ValidationOutcome = ValidationOutcome.PASS) -> None:
        for artifact_type, role in [
            (ArtifactType.REQUIREMENT, Role.PM),
            (ArtifactType.PRD, Role.PM),
            (ArtifactType.TASK_BREAKDOWN, Role.PM),
            (ArtifactType.TECH_PLAN, Role.ARCHITECT),
            (ArtifactType.FILE_CHANGE_PLAN, Role.ARCHITECT),
            (ArtifactType.RISK_PLAN, Role.ARCHITECT),
            (ArtifactType.IMPLEMENTATION_LOG, Role.DEVELOPER),
            (ArtifactType.CHANGED_FILES, Role.DEVELOPER),
            (ArtifactType.TEST_REPORT, Role.QA),
            (ArtifactType.ACCEPTANCE_CHECKLIST, Role.QA),
        ]:
            validation = (
                test_report_result
                if artifact_type == ArtifactType.TEST_REPORT
                else ValidationOutcome.PASS
            )
            body = "# Artifact\n"
            if artifact_type == ArtifactType.TEST_REPORT and validation == ValidationOutcome.FAIL:
                body += "\nstatus: fail\n"
            self.write_artifact(artifact_type, role, validation, body)

    def write_artifact(
        self,
        artifact_type: ArtifactType,
        produced_by: Role,
        validation_result: ValidationOutcome,
        body: str,
    ) -> None:
        filename = artifact_type.value.replace("_", "-")
        directory = "qa" if produced_by == Role.QA else produced_by.value
        artifact = Artifact(
            artifact_id=f"A-T-2026-001-{artifact_type.value}",
            task_id="T-2026-001",
            artifact_type=artifact_type,
            produced_by=produced_by,
            consumed_by=[Role.CONTROLLER],
            file_path=f"artifacts/{directory}/{filename}.md",
            version=1,
            status=ArtifactStatus.READY,
            summary=f"{artifact_type.value} ready",
            validation_result=validation_result,
            created_at="2026-05-12T10:00:00+08:00",
        )
        self.artifact_repo.write_artifact(artifact, body)

    def write_reviews(
        self,
        *,
        final_verdict: ReviewVerdict = ReviewVerdict.APPROVED,
        final_reviewer: str = "zhangxia",
    ) -> None:
        self.review_repo.write_review(
            ReviewRecord(
                review_id="R-T-2026-001-architect",
                task_id="T-2026-001",
                review_type=ReviewType.ARCHITECT_REVIEW,
                reviewed_artifacts=["tech_plan", "file_change_plan", "risk_plan"],
                reviewer="zhangxia",
                reviewed_at="2026-05-12T10:00:00+08:00",
                verdict=ReviewVerdict.APPROVED,
                issues=[],
                followup_required=False,
            ),
            overwrite=True,
        )
        self.review_repo.write_review(
            ReviewRecord(
                review_id="R-T-2026-001-final",
                task_id="T-2026-001",
                review_type=ReviewType.FINAL_REVIEW,
                reviewed_artifacts=["test_report", "acceptance_checklist"],
                reviewer=final_reviewer,
                reviewed_at="2026-05-12T10:00:00+08:00",
                verdict=final_verdict,
                issues=[]
                if final_verdict == ReviewVerdict.APPROVED
                else [
                    ReviewIssue(
                        severity=ReviewIssueSeverity.MAJOR,
                        description="needs changes",
                        affected_artifact="test_report",
                    ),
                ],
                followup_required=False,
            ),
            overwrite=True,
        )

    def assert_gate_fails_with(self, expected: str) -> None:
        result = self.service.validate_final_delivery_gate("T-2026-001")
        self.assertFalse(result.ok)
        self.assertTrue(any(expected in error for error in result.errors), result.errors)
        with self.assertRaises(FinalDeliveryError):
            self.service.write_final_delivery("T-2026-001")

    def create_risk(
        self,
        severity: RiskSeverity,
        *,
        options: list[str] | None = None,
        requires_human_decision: bool | None = None,
    ) -> str:
        risk = self.risk_decision_service.create_risk_finding(
            task_id="T-2026-001",
            source_agent=Role.CONTROLLER,
            category=RiskCategory.REVIEW,
            severity=severity,
            title="Risk",
            description="Risk description",
            evidence="risk evidence",
            affected_files=[],
            affected_artifacts=["test_report"],
            recommended_options=options
            or [
                RiskDecisionAction.SEND_TO_QA.value,
                RiskDecisionAction.ACCEPT_RISK_AND_CONTINUE.value,
            ],
            default_recommendation=RiskDecisionAction.SEND_TO_QA.value,
            requires_human_decision=requires_human_decision,
        )
        return risk.risk_id

    def test_final_review_status_not_approved_blocks_write(self) -> None:
        self.write_completed_state(final_review_status=ReviewStatus.PENDING)

        self.assert_gate_fails_with("final_review_status")

    def test_current_status_not_completed_blocks_write(self) -> None:
        self.write_completed_state(status=TaskStatus.FINAL_REVIEW_REQUIRED)

        self.assert_gate_fails_with("current_status")

    def test_missing_final_review_blocks_write(self) -> None:
        self.review_repo.build_review_path("T-2026-001", "final_review").unlink()

        self.assert_gate_fails_with("final-review.md is required")

    def test_final_review_verdict_not_approved_blocks_write(self) -> None:
        self.write_reviews(final_verdict=ReviewVerdict.NEEDS_CHANGES)

        self.assert_gate_fails_with("verdict must be approved")

    def test_illegal_reviewer_blocks_write(self) -> None:
        path = self.review_repo.build_review_path("T-2026-001", "final_review")
        text = path.read_text(encoding="utf-8").replace("reviewer: zhangxia", "reviewer: controller")
        path.write_text(text, encoding="utf-8")

        self.assert_gate_fails_with("final-review.md invalid")

    def test_test_report_fail_blocks_write(self) -> None:
        self.write_all_artifacts(test_report_result=ValidationOutcome.FAIL)

        self.assert_gate_fails_with("test-report has unresolved fail")

    def test_active_blocker_blocks_write(self) -> None:
        self.write_completed_state(active_blocker="B-T-2026-001-001")

        self.assert_gate_fails_with("active_blocker")

    def test_blocked_context_blocks_write(self) -> None:
        self.write_completed_state(
            blocked_context=BlockedContext(
                blocker_id="B-T-2026-001-001",
                blocked_from_agent=Role.DEVELOPER,
                blocked_from_status=TaskStatus.DEVELOPER_PROCESSING,
                resume_to_agent=Role.ARCHITECT,
                resume_to_status=TaskStatus.DEVELOPER_PROCESSING,
                blocking_reason="blocked",
                missing_artifacts=["file_change_plan"],
                required_fix="fix",
            ),
        )

        self.assert_gate_fails_with("blocked_context")

    def test_missing_upstream_artifact_blocks_write(self) -> None:
        path = self.paths.task_dir("T-2026-001") / "artifacts/developer/changed-files.md"
        path.unlink()

        self.assert_gate_fails_with("required artifact missing")

    def test_unresolved_p0_risk_blocks_write(self) -> None:
        risk_id = self.create_risk(
            RiskSeverity.P0_BLOCKER,
            options=[RiskDecisionAction.SEND_TO_QA.value, RiskDecisionAction.CANCEL_TASK.value],
        )

        self.assert_gate_fails_with(f"unresolved blocking risk: {risk_id}")

    def test_unresolved_p1_risk_blocks_write(self) -> None:
        risk_id = self.create_risk(RiskSeverity.P1_HIGH)

        self.assert_gate_fails_with(f"unresolved blocking risk: {risk_id}")

    def test_unresolved_string_p0_risk_is_normalized_and_blocks_write(self) -> None:
        class FakeRisk:
            risk_id = "RISK-T-2026-001-999"
            severity = "P0_BLOCKER"

        class FakeRiskRepo:
            def list_open_risks(self, task_id: str):
                return [FakeRisk()]

            def list_decisions(self, task_id: str):
                return []

        service = FinalDeliveryService(
            state_repo=self.state_repo,
            task_repo=self.task_repo,
            artifact_repo=self.artifact_repo,
            review_repo=self.review_repo,
            risk_repo=FakeRiskRepo(),
        )

        result = service.validate_final_delivery_gate("T-2026-001")

        self.assertFalse(result.ok)
        self.assertIn("unresolved blocking risk: RISK-T-2026-001-999", result.errors)

    def test_unresolved_p2_risk_does_not_block_final_delivery(self) -> None:
        self.create_risk(RiskSeverity.P2_MEDIUM, requires_human_decision=False)

        result = self.service.validate_final_delivery_gate("T-2026-001")

        self.assertTrue(result.ok, result.errors)

    def test_unresolved_p2_requiring_human_decision_blocks_final_delivery(self) -> None:
        risk_id = self.create_risk(RiskSeverity.P2_MEDIUM, requires_human_decision=True)

        self.assert_gate_fails_with(f"unresolved blocking risk: {risk_id}")

    def test_p2_requiring_human_decision_with_accepted_decision_allows_and_is_referenced(self) -> None:
        risk_id = self.create_risk(RiskSeverity.P2_MEDIUM, requires_human_decision=True)
        decision = self.risk_decision_service.record_decision(
            task_id="T-2026-001",
            risk_id=risk_id,
            decision_by="zhangxia",
            selected_option=RiskDecisionAction.ACCEPT_RISK_AND_CONTINUE.value,
            decision=RiskDecisionAction.ACCEPT_RISK_AND_CONTINUE,
            reason="Accepted with explicit medium-risk follow-up.",
        )
        self.risk_decision_service.apply_decision(task_id="T-2026-001", decision=decision)

        path = self.service.write_final_delivery("T-2026-001")
        body = path.read_text(encoding="utf-8")

        self.assertIn(risk_id, body)

    def test_accepted_risk_can_be_referenced_in_final_delivery(self) -> None:
        risk_id = self.create_risk(RiskSeverity.P1_HIGH)
        decision = self.risk_decision_service.record_decision(
            task_id="T-2026-001",
            risk_id=risk_id,
            decision_by="zhangxia",
            selected_option=RiskDecisionAction.ACCEPT_RISK_AND_CONTINUE.value,
            decision=RiskDecisionAction.ACCEPT_RISK_AND_CONTINUE,
            reason="Accepted with explicit follow-up tracking.",
        )
        self.risk_decision_service.apply_decision(task_id="T-2026-001", decision=decision)

        path = self.service.write_final_delivery("T-2026-001")
        body = path.read_text(encoding="utf-8")

        self.assertIn("## Known Risks", body)
        self.assertIn(risk_id, body)

    def test_all_gates_pass_writes_final_delivery(self) -> None:
        path = self.service.write_final_delivery("T-2026-001")
        body = path.read_text(encoding="utf-8")

        self.assertIn("## Artifact Index", body)
        self.assertIn("## Review Record Index", body)
        self.assertIn("## Final Gate Check Summary", body)

    def test_final_delivery_write_does_not_modify_upstream_artifacts(self) -> None:
        upstream = self.paths.task_dir("T-2026-001") / "artifacts/pm/requirement.md"
        before = upstream.read_text(encoding="utf-8")

        self.service.write_final_delivery("T-2026-001")

        self.assertEqual(upstream.read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
