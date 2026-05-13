import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import (
    ArtifactStatus,
    ArtifactType,
    ReviewIssueSeverity,
    ReviewStatus,
    ReviewVerdict,
    RiskCategory,
    RiskSeverity,
    RiskStatus,
    Role,
    TaskStatus,
    ValidationOutcome,
)
from a2a_runtime.core.errors import ReviewError, SchemaError, StateMachineError
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.artifact import Artifact
from a2a_runtime.models.review import ReviewIssue
from a2a_runtime.models.state import State
from a2a_runtime.repositories.artifact_repo import ArtifactRepo
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.review_repo import ReviewRepo
from a2a_runtime.repositories.risk_repo import RiskRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.services.risk_decision_service import RiskDecisionService
from a2a_runtime.services.review_service import ReviewService


def make_state(
    status: TaskStatus,
    *,
    human_review_status: ReviewStatus = ReviewStatus.PENDING,
    final_review_status: ReviewStatus = ReviewStatus.PENDING,
) -> State:
    return State(
        task_id="T-2026-001",
        current_status=status,
        previous_status=status,
        current_agent=Role.HUMAN,
        next_agent=Role.DEVELOPER,
        allowed_next_statuses=[],
        human_review_status=human_review_status,
        final_review_status=final_review_status,
        updated_at="2026-05-12T10:00:00+08:00",
    )


def issue() -> ReviewIssue:
    return ReviewIssue(
        severity=ReviewIssueSeverity.MAJOR,
        description="needs revision",
        affected_artifact="tech_plan",
    )


class ReviewFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.paths = A2APaths(Path(self.tmp.name))
        self.state_repo = StateRepo(self.paths)
        self.artifact_repo = ArtifactRepo(self.paths)
        self.review_repo = ReviewRepo(self.paths)
        self.message_repo = MessageRepo(self.paths)
        self.risk_repo = RiskRepo(self.message_repo)
        self.risk_decision_service = RiskDecisionService(
            risk_repo=self.risk_repo,
            state_repo=self.state_repo,
        )
        self.service = ReviewService(
            review_repo=self.review_repo,
            state_repo=self.state_repo,
            message_repo=self.message_repo,
            artifact_repo=self.artifact_repo,
            risk_decision_service=self.risk_decision_service,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_state(self, state: State) -> None:
        self.state_repo.write("T-2026-001", state, actor=Role.CONTROLLER, body="# State")

    def create_approved_architect_review(self) -> None:
        self.write_ready_review_artifacts("architect")
        self.service.create_architect_review(
            task_id="T-2026-001",
            reviewer="zhangxia",
            verdict=ReviewVerdict.APPROVED,
            reviewed_artifacts=["tech_plan", "file_change_plan", "risk_plan"],
            issues=[],
            followup_required=False,
        )

    def create_approved_final_review(self) -> None:
        self.write_ready_review_artifacts("final")
        self.service.create_final_review(
            task_id="T-2026-001",
            reviewer="zhangxia",
            verdict=ReviewVerdict.APPROVED,
            reviewed_artifacts=["test_report", "acceptance_checklist"],
            issues=[],
            followup_required=False,
        )

    def write_ready_review_artifacts(self, stage: str) -> None:
        artifacts = (
            [
                (ArtifactType.TECH_PLAN, Role.ARCHITECT),
                (ArtifactType.FILE_CHANGE_PLAN, Role.ARCHITECT),
                (ArtifactType.RISK_PLAN, Role.ARCHITECT),
            ]
            if stage == "architect"
            else [
                (ArtifactType.TEST_REPORT, Role.QA),
                (ArtifactType.ACCEPTANCE_CHECKLIST, Role.QA),
            ]
        )
        for artifact_type, role in artifacts:
            directory = "qa" if role == Role.QA else role.value
            filename = artifact_type.value.replace("_", "-")
            artifact = Artifact(
                artifact_id=f"A-T-2026-001-{artifact_type.value}",
                task_id="T-2026-001",
                artifact_type=artifact_type,
                produced_by=role,
                consumed_by=[Role.CONTROLLER],
                file_path=f"artifacts/{directory}/{filename}.md",
                version=1,
                status=ArtifactStatus.READY,
                summary=f"{artifact_type.value} ready",
                validation_result=ValidationOutcome.PASS,
                created_at="2026-05-12T10:00:00+08:00",
            )
            body = "# Test Report\nstatus: pass\n" if artifact_type == ArtifactType.TEST_REPORT else "# Artifact\n"
            self.artifact_repo.write_artifact(artifact, body)

    def test_create_architect_review_success(self) -> None:
        self.write_ready_review_artifacts("architect")
        record = self.service.create_architect_review(
            task_id="T-2026-001",
            reviewer="zhangxia",
            verdict="approved",
            reviewed_artifacts=["tech_plan", "file_change_plan", "risk_plan"],
            issues=[],
            followup_required=False,
        )

        self.assertEqual(record.review_id, "R-T-2026-001-architect")
        self.assertTrue(self.review_repo.build_review_path("T-2026-001", "architect_review").exists())

    def test_role_reviewer_is_rejected(self) -> None:
        for reviewer in ["controller", "pm", "architect", "developer", "qa"]:
            with self.subTest(reviewer=reviewer):
                with self.assertRaises(SchemaError):
                    self.service.create_architect_review(
                        task_id="T-2026-001",
                        reviewer=reviewer,
                        verdict="approved",
                        reviewed_artifacts=["tech_plan", "file_change_plan", "risk_plan"],
                        issues=[],
                        followup_required=False,
                        overwrite=True,
                    )

    def test_approved_architect_review_missing_tech_plan_is_rejected(self) -> None:
        with self.assertRaises(ReviewError):
            self.service.create_architect_review(
                task_id="T-2026-001",
                reviewer="zhangxia",
                verdict="approved",
                reviewed_artifacts=["file_change_plan", "risk_plan"],
                issues=[],
                followup_required=False,
            )

    def test_rejected_review_without_issues_is_rejected(self) -> None:
        with self.assertRaises(SchemaError):
            self.service.create_architect_review(
                task_id="T-2026-001",
                reviewer="zhangxia",
                verdict="rejected",
                reviewed_artifacts=["tech_plan", "file_change_plan", "risk_plan"],
                issues=[],
                followup_required=True,
            )

    def test_architect_review_step_1_only_changes_human_review_status(self) -> None:
        self.write_state(make_state(TaskStatus.HUMAN_REVIEW_REQUIRED))
        self.create_approved_architect_review()

        result = self.service.approve_architect_review_step_1("T-2026-001")
        state = result.transition.state

        self.assertEqual(state.current_status, TaskStatus.HUMAN_REVIEW_REQUIRED)
        self.assertEqual(state.human_review_status, ReviewStatus.APPROVED)

    def test_architect_review_step_2_rejects_when_status_not_approved(self) -> None:
        self.write_state(
            make_state(
                TaskStatus.HUMAN_REVIEW_REQUIRED,
                human_review_status=ReviewStatus.PENDING,
            ),
        )
        self.create_approved_architect_review()

        with self.assertRaises(StateMachineError):
            self.service.approve_architect_review_step_2("T-2026-001")

    def test_architect_review_step_2_enters_developer_processing(self) -> None:
        self.write_state(
            make_state(
                TaskStatus.HUMAN_REVIEW_REQUIRED,
                human_review_status=ReviewStatus.APPROVED,
            ),
        )
        self.create_approved_architect_review()

        result = self.service.approve_architect_review_step_2("T-2026-001")

        self.assertEqual(result.transition.state.current_status, TaskStatus.DEVELOPER_PROCESSING)
        self.assertEqual(result.transition.state.current_agent, Role.DEVELOPER)

    def test_architect_review_rejected_does_not_enter_developer_processing(self) -> None:
        self.write_state(make_state(TaskStatus.HUMAN_REVIEW_REQUIRED))
        self.service.create_architect_review(
            task_id="T-2026-001",
            reviewer="zhangxia",
            verdict="rejected",
            reviewed_artifacts=["tech_plan", "file_change_plan", "risk_plan"],
            issues=[issue()],
            followup_required=True,
        )

        result = self.service.reject_architect_review("T-2026-001")

        self.assertEqual(result.transition.state.current_status, TaskStatus.ARCHITECT_PROCESSING)
        self.assertNotEqual(result.transition.state.current_status, TaskStatus.DEVELOPER_PROCESSING)

    def test_create_final_review_success(self) -> None:
        self.write_ready_review_artifacts("final")
        record = self.service.create_final_review(
            task_id="T-2026-001",
            reviewer="zhangxia",
            verdict="approved",
            reviewed_artifacts=["test_report", "acceptance_checklist"],
            issues=[],
            followup_required=False,
        )

        self.assertEqual(record.review_id, "R-T-2026-001-final")
        self.assertTrue(self.review_repo.build_review_path("T-2026-001", "final_review").exists())

    def test_approved_final_review_missing_test_report_is_rejected(self) -> None:
        with self.assertRaises(ReviewError):
            self.service.create_final_review(
                task_id="T-2026-001",
                reviewer="zhangxia",
                verdict="approved",
                reviewed_artifacts=["acceptance_checklist"],
                issues=[],
                followup_required=False,
            )

    def test_final_review_step_1_only_changes_final_review_status(self) -> None:
        self.write_state(make_state(TaskStatus.FINAL_REVIEW_REQUIRED))
        self.create_approved_final_review()

        result = self.service.approve_final_review_step_1("T-2026-001")

        self.assertEqual(result.transition.state.current_status, TaskStatus.FINAL_REVIEW_REQUIRED)
        self.assertEqual(result.transition.state.final_review_status, ReviewStatus.APPROVED)

    def test_final_review_step_2_rejects_when_status_not_approved(self) -> None:
        self.write_state(
            make_state(
                TaskStatus.FINAL_REVIEW_REQUIRED,
                final_review_status=ReviewStatus.PENDING,
            ),
        )
        self.create_approved_final_review()

        with self.assertRaises(StateMachineError):
            self.service.approve_final_review_step_2("T-2026-001")

    def test_final_review_step_2_enters_completed_when_clean(self) -> None:
        self.write_state(
            make_state(
                TaskStatus.FINAL_REVIEW_REQUIRED,
                human_review_status=ReviewStatus.APPROVED,
                final_review_status=ReviewStatus.APPROVED,
            ),
        )
        self.create_approved_final_review()

        result = self.service.approve_final_review_step_2("T-2026-001")

        self.assertEqual(result.transition.state.current_status, TaskStatus.COMPLETED)
        self.assertEqual(result.transition.state.current_agent, Role.CONTROLLER)

    def test_final_review_rejected_does_not_enter_completed(self) -> None:
        self.write_state(make_state(TaskStatus.FINAL_REVIEW_REQUIRED))
        self.service.create_final_review(
            task_id="T-2026-001",
            reviewer="zhangxia",
            verdict="needs_changes",
            reviewed_artifacts=["test_report", "acceptance_checklist"],
            issues=[issue()],
            followup_required=True,
        )

        result = self.service.reject_final_review("T-2026-001")

        self.assertEqual(result.transition.state.current_status, TaskStatus.DEVELOPER_PROCESSING)
        self.assertNotEqual(result.transition.state.current_status, TaskStatus.COMPLETED)

    def test_review_rejection_with_multiple_targets_creates_risk_gate(self) -> None:
        self.write_state(make_state(TaskStatus.FINAL_REVIEW_REQUIRED))
        self.service.create_final_review(
            task_id="T-2026-001",
            reviewer="zhangxia",
            verdict="needs_changes",
            reviewed_artifacts=["test_report", "acceptance_checklist"],
            issues=[issue()],
            followup_required=True,
        )

        with self.assertRaises(ReviewError):
            self.service.reject_final_review(
                "T-2026-001",
                multiple_resume_candidates=True,
            )

        risks = self.risk_repo.list_risks("T-2026-001")
        self.assertEqual(len(risks), 1)
        self.assertEqual(risks[0].category, RiskCategory.REVIEW)
        self.assertEqual(risks[0].severity, RiskSeverity.P1_HIGH)
        self.assertEqual(risks[0].status, RiskStatus.WAITING_HUMAN_DECISION)
        self.assertEqual(
            self.state_repo.read("T-2026-001").current_status,
            TaskStatus.FINAL_REVIEW_REQUIRED,
        )


if __name__ == "__main__":
    unittest.main()
