"""Review record creation and review state flows."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

from a2a_runtime.core.clock import Clock
from a2a_runtime.core.constants import (
    ArtifactStatus,
    ArtifactType,
    MessageType,
    ReviewStatus,
    ReviewType,
    ReviewVerdict,
    RiskCategory,
    RiskDecisionAction,
    RiskSeverity,
    Role,
    TaskStatus,
)
from a2a_runtime.core.errors import ReviewError, StateMachineError
from a2a_runtime.models.review import ReviewIssue, ReviewRecord
from a2a_runtime.repositories.artifact_repo import ArtifactRepo
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.review_repo import ReviewRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.services.risk_decision_service import RiskDecisionService
from a2a_runtime.services.state_machine import StateMachine, StateTransitionResult
from a2a_runtime.services.test_report import check_test_report_clean

ARCHITECT_REQUIRED_REVIEW_ARTIFACTS = {"tech_plan", "file_change_plan", "risk_plan"}
FINAL_REQUIRED_REVIEW_ARTIFACTS = {"test_report", "acceptance_checklist"}


@dataclass(frozen=True)
class ReviewFlowResult:
    transition: StateTransitionResult
    message_id: str


class ReviewService:
    def __init__(
        self,
        *,
        review_repo: ReviewRepo,
        state_repo: StateRepo,
        message_repo: MessageRepo,
        artifact_repo: ArtifactRepo | None = None,
        state_machine: StateMachine | None = None,
        risk_decision_service: RiskDecisionService | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.review_repo = review_repo
        self.state_repo = state_repo
        self.message_repo = message_repo
        self.artifact_repo = artifact_repo or ArtifactRepo(state_repo.paths)
        self.risk_decision_service = risk_decision_service
        self.clock = clock or Clock()
        self.state_machine = state_machine or StateMachine(clock=self.clock)

    def create_architect_review(
        self,
        *,
        task_id: str,
        reviewer: str,
        verdict: ReviewVerdict | str,
        reviewed_artifacts: list[str],
        issues: list[ReviewIssue],
        followup_required: bool,
        notes: str | None = None,
        overwrite: bool = False,
        body: str = "",
    ) -> ReviewRecord:
        return self._create_review(
            task_id=task_id,
            reviewer=reviewer,
            verdict=verdict,
            reviewed_artifacts=reviewed_artifacts,
            issues=issues,
            followup_required=followup_required,
            notes=notes,
            review_type=ReviewType.ARCHITECT_REVIEW,
            required_artifacts=ARCHITECT_REQUIRED_REVIEW_ARTIFACTS,
            overwrite=overwrite,
            body=body,
        )

    def create_final_review(
        self,
        *,
        task_id: str,
        reviewer: str,
        verdict: ReviewVerdict | str,
        reviewed_artifacts: list[str],
        issues: list[ReviewIssue],
        followup_required: bool,
        notes: str | None = None,
        overwrite: bool = False,
        body: str = "",
    ) -> ReviewRecord:
        return self._create_review(
            task_id=task_id,
            reviewer=reviewer,
            verdict=verdict,
            reviewed_artifacts=reviewed_artifacts,
            issues=issues,
            followup_required=followup_required,
            notes=notes,
            review_type=ReviewType.FINAL_REVIEW,
            required_artifacts=FINAL_REQUIRED_REVIEW_ARTIFACTS,
            overwrite=overwrite,
            body=body,
        )

    def validate_architect_review(self, task_id: str) -> ReviewRecord:
        review = self.review_repo.find_architect_review(task_id)
        if review is None:
            raise ReviewError("architect-review.md is missing")
        self.validate_required_review_artifacts_ready(task_id, ReviewType.ARCHITECT_REVIEW)
        self._validate_review(
            review,
            expected_type=ReviewType.ARCHITECT_REVIEW,
            required_artifacts=ARCHITECT_REQUIRED_REVIEW_ARTIFACTS,
            require_approved=True,
        )
        return review

    def validate_final_review(self, task_id: str) -> ReviewRecord:
        review = self.review_repo.find_final_review(task_id)
        if review is None:
            raise ReviewError("final-review.md is missing")
        self.validate_required_review_artifacts_ready(task_id, ReviewType.FINAL_REVIEW)
        self._validate_review(
            review,
            expected_type=ReviewType.FINAL_REVIEW,
            required_artifacts=FINAL_REQUIRED_REVIEW_ARTIFACTS,
            require_approved=True,
        )
        return review

    def approve_architect_review_step_1(self, task_id: str) -> ReviewFlowResult:
        self.validate_architect_review(task_id)
        state, body = self.state_repo.read_with_body(task_id)
        result = self.state_machine.approve_architect_review_step_1(
            state,
            actor=Role.CONTROLLER,
            reason="architect review approved step 1",
        )
        self.state_repo.write_with_history(
            task_id,
            result.state,
            result.history_entry(),
            actor=Role.CONTROLLER,
            body=body,
        )
        message_id = self._write_message(
            task_id=task_id,
            to_agent=Role.HUMAN,
            message_type=MessageType.REVIEW,
            intent="architect_review_status_approved",
            summary="Architect Review approved; human_review_status updated",
            payload={"human_review_status": ReviewStatus.APPROVED.value},
        )
        return ReviewFlowResult(transition=result, message_id=message_id)

    def approve_architect_review_step_2(self, task_id: str) -> ReviewFlowResult:
        self.validate_architect_review(task_id)
        state, body = self.state_repo.read_with_body(task_id)
        result = self.state_machine.approve_architect_review_step_2(
            state,
            review_valid=True,
            actor=Role.CONTROLLER,
            reason="architect review approved step 2",
        )
        self.state_repo.write_with_history(
            task_id,
            result.state,
            result.history_entry(),
            actor=Role.CONTROLLER,
            body=body,
        )
        message_id = self._write_message(
            task_id=task_id,
            to_agent=Role.DEVELOPER,
            message_type=MessageType.HANDOFF,
            intent="human_review_to_developer_handoff",
            summary="Architect Review approved; handoff to developer",
            payload={"current_status": TaskStatus.DEVELOPER_PROCESSING.value},
        )
        return ReviewFlowResult(transition=result, message_id=message_id)

    def reject_architect_review(
        self,
        task_id: str,
        *,
        multiple_resume_candidates: bool = False,
    ) -> ReviewFlowResult:
        review = self.review_repo.find_architect_review(task_id)
        if review is None:
            raise ReviewError("architect-review.md is missing")
        self._validate_rejected_review(review, ReviewType.ARCHITECT_REVIEW)
        self._require_risk_decision_for_multiple_review_targets(
            task_id=task_id,
            review=review,
            multiple_resume_candidates=multiple_resume_candidates,
        )
        state, body = self.state_repo.read_with_body(task_id)
        if state.current_status != TaskStatus.HUMAN_REVIEW_REQUIRED:
            raise StateMachineError("architect review rejection requires human_review_required")
        rejected_state = self.state_machine.transition(
            replace(state, human_review_status=ReviewStatus.REJECTED),
            TaskStatus.ARCHITECT_PROCESSING,
            actor=Role.CONTROLLER,
            reason="architect review rejected",
        )
        self.state_repo.write_with_history(
            task_id,
            rejected_state.state,
            rejected_state.history_entry(),
            actor=Role.CONTROLLER,
            body=body,
        )
        message_id = self._write_message(
            task_id=task_id,
            to_agent=Role.ARCHITECT,
            message_type=MessageType.REVIEW,
            intent="architect_review_rejected",
            summary="Architect Review rejected; architect must revise the plan",
            payload={"issues": [issue.to_dict() for issue in review.issues]},
        )
        return ReviewFlowResult(transition=rejected_state, message_id=message_id)

    def approve_final_review_step_1(self, task_id: str) -> ReviewFlowResult:
        self.validate_final_review(task_id)
        state, body = self.state_repo.read_with_body(task_id)
        result = self.state_machine.approve_final_review_step_1(
            state,
            actor=Role.CONTROLLER,
            reason="final review approved step 1",
        )
        self.state_repo.write_with_history(
            task_id,
            result.state,
            result.history_entry(),
            actor=Role.CONTROLLER,
            body=body,
        )
        message_id = self._write_message(
            task_id=task_id,
            to_agent=Role.HUMAN,
            message_type=MessageType.REVIEW,
            intent="final_review_status_approved",
            summary="Final Review approved; final_review_status updated",
            payload={"final_review_status": ReviewStatus.APPROVED.value},
        )
        return ReviewFlowResult(transition=result, message_id=message_id)

    def approve_final_review_step_2(
        self,
        task_id: str,
    ) -> ReviewFlowResult:
        self.validate_final_review(task_id)
        test_report = check_test_report_clean(self.artifact_repo, task_id)
        if not test_report.ok:
            raise ReviewError("; ".join(test_report.errors))
        state, body = self.state_repo.read_with_body(task_id)
        result = self.state_machine.approve_final_review_step_2(
            state,
            final_review_valid=True,
            actor=Role.CONTROLLER,
            reason="final review approved step 2",
        )
        self.state_repo.write_with_history(
            task_id,
            result.state,
            result.history_entry(),
            actor=Role.CONTROLLER,
            body=body,
        )
        message_id = self._write_message(
            task_id=task_id,
            to_agent=Role.HUMAN,
            message_type=MessageType.FINAL,
            intent="final_delivery_completed",
            summary="Final Review approved; task is completed",
            payload={"current_status": TaskStatus.COMPLETED.value},
        )
        return ReviewFlowResult(transition=result, message_id=message_id)

    def reject_final_review(
        self,
        task_id: str,
        *,
        multiple_resume_candidates: bool = False,
    ) -> ReviewFlowResult:
        review = self.review_repo.find_final_review(task_id)
        if review is None:
            raise ReviewError("final-review.md is missing")
        self._validate_rejected_review(review, ReviewType.FINAL_REVIEW)
        self._require_risk_decision_for_multiple_review_targets(
            task_id=task_id,
            review=review,
            multiple_resume_candidates=multiple_resume_candidates,
        )
        state, body = self.state_repo.read_with_body(task_id)
        if state.current_status != TaskStatus.FINAL_REVIEW_REQUIRED:
            raise StateMachineError("final review rejection requires final_review_required")
        rejected_state = self.state_machine.transition(
            replace(state, final_review_status=ReviewStatus.REJECTED),
            TaskStatus.DEVELOPER_PROCESSING,
            actor=Role.CONTROLLER,
            reason="final review rejected",
        )
        self.state_repo.write_with_history(
            task_id,
            rejected_state.state,
            rejected_state.history_entry(),
            actor=Role.CONTROLLER,
            body=body,
        )
        message_id = self._write_message(
            task_id=task_id,
            to_agent=Role.DEVELOPER,
            message_type=MessageType.REVIEW,
            intent="final_review_rejected",
            summary="Final Review rejected; developer must fix or re-verify",
            payload={"issues": [issue.to_dict() for issue in review.issues]},
        )
        return ReviewFlowResult(transition=rejected_state, message_id=message_id)

    def _create_review(
        self,
        *,
        task_id: str,
        reviewer: str,
        verdict: ReviewVerdict | str,
        reviewed_artifacts: list[str],
        issues: list[ReviewIssue],
        followup_required: bool,
        notes: str | None,
        review_type: ReviewType,
        required_artifacts: set[str],
        overwrite: bool,
        body: str,
    ) -> ReviewRecord:
        parsed_verdict = ReviewVerdict(str(verdict))
        suffix = "architect" if review_type == ReviewType.ARCHITECT_REVIEW else "final"
        record = ReviewRecord(
            review_id=f"R-{task_id}-{suffix}",
            task_id=task_id,
            review_type=review_type,
            reviewed_artifacts=reviewed_artifacts,
            reviewer=reviewer,
            reviewed_at=self.clock.now_iso(),
            verdict=parsed_verdict,
            issues=issues,
            followup_required=followup_required,
            notes=notes,
        )
        self._validate_review(
            record,
            expected_type=review_type,
            required_artifacts=required_artifacts,
            require_approved=False,
        )
        if parsed_verdict == ReviewVerdict.APPROVED:
            self.validate_required_review_artifacts_ready(task_id, review_type)
        self.review_repo.write_review(record, body, overwrite=overwrite)
        return record

    def validate_required_review_artifacts_ready(
        self,
        task_id: str,
        review_type: ReviewType,
    ) -> None:
        required = (
            ARCHITECT_REQUIRED_REVIEW_ARTIFACTS
            if review_type == ReviewType.ARCHITECT_REVIEW
            else FINAL_REQUIRED_REVIEW_ARTIFACTS
        )
        type_map = {
            "tech_plan": ArtifactType.TECH_PLAN,
            "file_change_plan": ArtifactType.FILE_CHANGE_PLAN,
            "risk_plan": ArtifactType.RISK_PLAN,
            "test_report": ArtifactType.TEST_REPORT,
            "acceptance_checklist": ArtifactType.ACCEPTANCE_CHECKLIST,
        }
        errors: list[str] = []
        for name in sorted(required):
            artifact_type = type_map[name]
            artifact = self.artifact_repo.find_artifact(task_id, artifact_type)
            if artifact is None:
                errors.append(f"required reviewed artifact missing: {name}")
                continue
            if artifact.status != ArtifactStatus.READY:
                errors.append(f"required reviewed artifact not ready: {name}")
        if errors:
            raise ReviewError("; ".join(errors))

    def _validate_review(
        self,
        review: ReviewRecord,
        *,
        expected_type: ReviewType,
        required_artifacts: set[str],
        require_approved: bool,
    ) -> None:
        self.review_repo.validate_review_record(review)
        if review.review_type != expected_type:
            raise ReviewError("review_type does not match expected review flow")
        if require_approved and review.verdict != ReviewVerdict.APPROVED:
            raise ReviewError("review verdict must be approved")
        missing = self._missing_required_review_artifacts(
            review.reviewed_artifacts,
            required_artifacts,
        )
        if missing:
            raise ReviewError(f"reviewed_artifacts missing required entries: {', '.join(missing)}")

    def _validate_rejected_review(self, review: ReviewRecord, review_type: ReviewType) -> None:
        self.review_repo.validate_review_record(review)
        if review.review_type != review_type:
            raise ReviewError("review_type does not match expected review flow")
        if review.verdict not in {ReviewVerdict.REJECTED, ReviewVerdict.NEEDS_CHANGES}:
            raise ReviewError("review verdict must be rejected or needs_changes")
        if not review.issues:
            raise ReviewError("rejected or needs_changes review must include issues")

    def _require_risk_decision_for_multiple_review_targets(
        self,
        *,
        task_id: str,
        review: ReviewRecord,
        multiple_resume_candidates: bool,
    ) -> None:
        if not multiple_resume_candidates:
            return
        if self.risk_decision_service is None:
            raise ReviewError("multiple review rollback targets require Human Risk Decision Gate")
        issue_text = "; ".join(issue.description for issue in review.issues)
        self.risk_decision_service.create_risk_finding(
            task_id=task_id,
            source_agent=Role.CONTROLLER,
            category=RiskCategory.REVIEW,
            severity=RiskSeverity.P1_HIGH,
            title=f"{review.review_type.value} needs human rollback decision",
            description="Review rejection has multiple reasonable rollback targets.",
            evidence=issue_text or "review rejected or marked needs_changes",
            affected_files=[],
            affected_artifacts=list(review.reviewed_artifacts),
            recommended_options=[
                RiskDecisionAction.SEND_TO_ARCHITECT.value,
                RiskDecisionAction.SEND_TO_DEVELOPER.value,
                RiskDecisionAction.SEND_TO_QA.value,
                RiskDecisionAction.CONVERT_TO_BLOCKER.value,
                RiskDecisionAction.CANCEL_TASK.value,
            ],
            default_recommendation=RiskDecisionAction.SEND_TO_ARCHITECT.value,
        )
        raise ReviewError("review rollback has multiple targets and requires human risk decision")

    def _missing_required_review_artifacts(
        self,
        reviewed_artifacts: Iterable[str],
        required_artifacts: set[str],
    ) -> list[str]:
        normalized = {self._normalize_artifact_ref(value) for value in reviewed_artifacts}
        missing: list[str] = []
        for required in required_artifacts:
            if required in normalized:
                continue
            suffix = f"_{required}"
            if any(value.endswith(suffix) for value in normalized):
                continue
            missing.append(required)
        return sorted(missing)

    def _normalize_artifact_ref(self, value: str) -> str:
        return value.replace("-", "_")

    def _write_message(
        self,
        *,
        task_id: str,
        to_agent: Role,
        message_type: MessageType,
        intent: str,
        summary: str,
        payload: dict[str, object],
    ) -> str:
        from a2a_runtime.models.message import Message

        seq = self.message_repo.next_sequence(task_id)
        message = Message(
            message_id=f"M-{task_id}-{seq:03d}",
            task_id=task_id,
            from_agent=Role.CONTROLLER,
            to_agent=to_agent,
            message_type=message_type,
            intent=intent,
            summary=summary,
            payload=payload,
            referenced_artifacts=[],
            required_response=False,
            blockers=[],
            created_at=self.clock.now_iso(),
        )
        self.message_repo.write_message(message)
        return message.message_id
