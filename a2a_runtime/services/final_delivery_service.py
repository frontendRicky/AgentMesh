"""Final delivery gate and writer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from a2a_runtime.core.clock import Clock
from a2a_runtime.core.constants import (
    ArtifactStatus,
    ArtifactType,
    MessageType,
    ReviewStatus,
    ReviewType,
    ReviewVerdict,
    Role,
    RiskSeverity,
    TaskStatus,
    ValidationOutcome,
    parse_enum,
)
from a2a_runtime.core.errors import FinalDeliveryError, RepositoryError, SchemaError
from a2a_runtime.models.artifact import Artifact
from a2a_runtime.models.message import Message
from a2a_runtime.models.review import ReviewRecord
from a2a_runtime.models.state import State
from a2a_runtime.repositories.artifact_repo import ArtifactRepo
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.risk_repo import RiskRepo
from a2a_runtime.repositories.review_repo import ReviewRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.repositories.task_repo import TaskRepo
from a2a_runtime.services.test_report import check_test_report_clean


@dataclass(frozen=True)
class FinalDeliveryGateResult:
    ok: bool
    errors: list[str]
    checked_artifacts: list[str]
    review_records: list[str]
    accepted_risks: list[str] | None = None


class FinalDeliveryService:
    def __init__(
        self,
        *,
        state_repo: StateRepo,
        task_repo: TaskRepo,
        artifact_repo: ArtifactRepo,
        review_repo: ReviewRepo,
        risk_repo: RiskRepo | None = None,
        message_repo: MessageRepo | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.state_repo = state_repo
        self.task_repo = task_repo
        self.artifact_repo = artifact_repo
        self.review_repo = review_repo
        self.risk_repo = risk_repo
        self.message_repo = message_repo
        self.clock = clock or Clock()

    def can_write_final_delivery(self, task_id: str) -> bool:
        return self.validate_final_delivery_gate(task_id).ok

    def validate_final_delivery_gate(self, task_id: str) -> FinalDeliveryGateResult:
        errors: list[str] = []
        checked_artifacts: list[str] = []
        review_records: list[str] = []
        accepted_risks: list[str] = []
        state = self.state_repo.read(task_id)

        if state.final_review_status != ReviewStatus.APPROVED:
            errors.append("state.final_review_status must be approved")
        if state.current_status != TaskStatus.COMPLETED:
            errors.append("state.current_status must be completed")
        if state.current_agent != Role.CONTROLLER:
            errors.append("state.current_agent must be controller")
        if state.active_blocker is not None:
            errors.append("state.active_blocker must be null")
        if state.blocked_context is not None:
            errors.append("state.blocked_context must be null")

        final_review = self._read_final_review(task_id, errors)
        if final_review is not None:
            review_records.append(final_review.review_id)
            if final_review.verdict != ReviewVerdict.APPROVED:
                errors.append("final-review.md verdict must be approved")
            if final_review.review_type != ReviewType.FINAL_REVIEW:
                errors.append("final-review.md review_type must be final_review")

        architect_review = self.review_repo.find_architect_review(task_id)
        if architect_review is None:
            errors.append("architect-review.md is required")
        else:
            review_records.append(architect_review.review_id)

        required_artifacts = self._required_upstream_artifacts(task_id)
        for artifact_type in required_artifacts:
            artifact = self.artifact_repo.find_artifact(task_id, artifact_type)
            if artifact is None:
                errors.append(f"required artifact missing: {artifact_type.value}")
                continue
            checked_artifacts.append(artifact.artifact_id)
            if artifact.status != ArtifactStatus.READY:
                errors.append(f"required artifact not ready: {artifact.artifact_id}")

        test_report = self.artifact_repo.find_artifact(task_id, ArtifactType.TEST_REPORT)
        if test_report is not None:
            report_check = check_test_report_clean(self.artifact_repo, task_id)
            if not report_check.ok:
                errors.append("test-report has unresolved fail")
                errors.extend(report_check.errors)

        if self.risk_repo is not None:
            for risk in self.risk_repo.list_open_risks(task_id):
                severity = parse_enum(RiskSeverity, risk.severity, "risk.severity")
                if severity in {RiskSeverity.P0_BLOCKER, RiskSeverity.P1_HIGH} or (
                    severity == RiskSeverity.P2_MEDIUM and risk.requires_human_decision
                ):
                    errors.append(f"unresolved blocking risk: {risk.risk_id}")
            accepted_risks = [
                decision.risk_id
                for decision in self.risk_repo.list_decisions(task_id)
                if decision.decision.value == "accept_risk_and_continue"
            ]

        return FinalDeliveryGateResult(
            ok=not errors,
            errors=errors,
            checked_artifacts=checked_artifacts,
            review_records=review_records,
            accepted_risks=accepted_risks,
        )

    def write_final_delivery(self, task_id: str) -> Path:
        gate = self.validate_final_delivery_gate(task_id)
        if not gate.ok:
            raise FinalDeliveryError("; ".join(gate.errors))
        artifact = Artifact(
            artifact_id=f"A-{task_id}-final_delivery",
            task_id=task_id,
            artifact_type=ArtifactType.FINAL_DELIVERY,
            produced_by=Role.CONTROLLER,
            consumed_by=[Role.HUMAN],
            file_path="artifacts/final/final-delivery.md",
            version=1,
            status=ArtifactStatus.READY,
            summary="Final delivery generated after all final gates passed",
            validation_result=ValidationOutcome.PASS,
            created_at=self.clock.now_iso(),
            dependencies=[*gate.checked_artifacts, *gate.review_records],
            validation_notes="final delivery gate passed",
        )
        path = self.artifact_repo.write_artifact(artifact, self._body(task_id, gate))
        if self.message_repo is not None:
            self._write_final_message(task_id, path)
        return path

    def _read_final_review(self, task_id: str, errors: list[str]) -> ReviewRecord | None:
        try:
            return self.review_repo.find_final_review(task_id)
        except (RepositoryError, SchemaError) as exc:
            errors.append(f"final-review.md invalid: {exc}")
            return None
        finally:
            path = self.review_repo.build_review_path(task_id, ReviewType.FINAL_REVIEW)
            if not path.exists():
                errors.append("final-review.md is required")

    def _required_upstream_artifacts(self, task_id: str) -> list[ArtifactType]:
        task = self.task_repo.read(task_id)
        required = [
            ArtifactType.REQUIREMENT,
            ArtifactType.TECH_PLAN,
            ArtifactType.FILE_CHANGE_PLAN,
            ArtifactType.RISK_PLAN,
            ArtifactType.IMPLEMENTATION_LOG,
            ArtifactType.CHANGED_FILES,
            ArtifactType.TEST_REPORT,
            ArtifactType.ACCEPTANCE_CHECKLIST,
        ]
        if task.task_type.value == "bugfix":
            required.extend([ArtifactType.BUG_BRIEF, ArtifactType.REGRESSION_SCOPE])
        else:
            required.extend([ArtifactType.PRD, ArtifactType.TASK_BREAKDOWN])
        return required

    def _test_report_clean(self, artifact: Artifact) -> bool:
        return check_test_report_clean(self.artifact_repo, artifact.task_id).ok

    def _body(self, task_id: str, gate: FinalDeliveryGateResult) -> str:
        artifacts = "\n".join(f"- {artifact_id}" for artifact_id in gate.checked_artifacts)
        reviews = "\n".join(f"- {review_id}" for review_id in gate.review_records)
        return f"""# Final Delivery: {task_id}

## Final Status
completed

## Artifact Index
{artifacts}

## Review Record Index
{reviews}

## Blocker Summary
- No active blocker at final delivery time.

## Known Risks
{self._risk_lines(gate.accepted_risks or [])}

## Final Gate Check Summary
- state.final_review_status == approved
- state.current_status == completed
- final-review.md verdict == approved
- required upstream artifacts exist and are ready
- test-report has no unresolved fail
"""

    def _risk_lines(self, risk_ids: list[str]) -> str:
        if not risk_ids:
            return "- No accepted risks recorded."
        return "\n".join(f"- accepted risk decision: {risk_id}" for risk_id in risk_ids)

    def _write_final_message(self, task_id: str, final_delivery_path: Path) -> None:
        if self.message_repo is None:
            return
        seq = self.message_repo.next_sequence(task_id)
        message = Message(
            message_id=f"M-{task_id}-{seq:03d}",
            task_id=task_id,
            from_agent=Role.CONTROLLER,
            to_agent=Role.HUMAN,
            message_type=MessageType.FINAL,
            intent="final_delivery_completed",
            summary="Final delivery written",
            payload={"final_delivery_path": str(final_delivery_path)},
            referenced_artifacts=["final_delivery"],
            required_response=False,
            blockers=[],
            created_at=self.clock.now_iso(),
        )
        self.message_repo.write_message(message)
