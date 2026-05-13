"""Flow Controller facade for the implemented runtime phases.

This class wires repositories and services without writing business source,
forging human review, choosing risk decisions, or calling LLM providers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from a2a_runtime.agents.base import AgentBase
from a2a_runtime.core import frontmatter
from a2a_runtime.core.constants import (
    RiskCategory,
    RiskDecisionAction,
    RiskSeverity,
    ReviewType,
    ReviewVerdict,
    Role,
    TaskStatus,
    parse_enum,
)
from a2a_runtime.core.errors import (
    BlockerError,
    FinalDeliveryError,
    FrontmatterError,
    RepositoryError,
    SchemaError,
)
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.review import ReviewIssue, ReviewRecord
from a2a_runtime.models.risk import RuntimeRiskFinding
from a2a_runtime.models.risk_decision import RiskDecision
from a2a_runtime.repositories.artifact_repo import ArtifactRepo
from a2a_runtime.repositories.blocker_repo import BlockerRepo
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.risk_repo import RiskRepo
from a2a_runtime.repositories.review_repo import ReviewRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.repositories.task_repo import TaskRepo
from a2a_runtime.repositories.workspace_repo import WorkspaceRepo
from a2a_runtime.services.blocker_service import (
    BlockerResolveResult,
    BlockerService,
    FormalBlockerResult,
)
from a2a_runtime.services.final_delivery_service import (
    FinalDeliveryGateResult,
    FinalDeliveryService,
)
from a2a_runtime.services.review_service import ReviewFlowResult, ReviewService
from a2a_runtime.services.prompt_service import PromptService
from a2a_runtime.services.risk_decision_service import RiskDecisionService
from a2a_runtime.services.risk_prompt_regeneration_service import RiskPromptRegenerationService
from a2a_runtime.services.state_machine import StateMachine, StateTransitionResult
from a2a_runtime.services.task_identity_service import TaskIdentityService


@dataclass
class FlowControllerAgent(AgentBase):
    paths: A2APaths
    role: Role = Role.CONTROLLER
    workspace_repo: WorkspaceRepo = field(init=False)
    task_repo: TaskRepo = field(init=False)
    state_repo: StateRepo = field(init=False)
    message_repo: MessageRepo = field(init=False)
    artifact_repo: ArtifactRepo = field(init=False)
    blocker_repo: BlockerRepo = field(init=False)
    review_repo: ReviewRepo = field(init=False)
    risk_repo: RiskRepo = field(init=False)
    blocker_service: BlockerService = field(init=False)
    review_service: ReviewService = field(init=False)
    final_delivery_service: FinalDeliveryService = field(init=False)
    prompt_service: PromptService = field(init=False)
    risk_prompt_service: RiskPromptRegenerationService = field(init=False)
    risk_decision_service: RiskDecisionService = field(init=False)
    task_identity_service: TaskIdentityService = field(init=False)
    state_machine: StateMachine = field(default_factory=StateMachine)

    forbidden_actions: tuple[str, ...] = (
        "write_pm_architect_developer_or_qa_artifacts",
        "write_business_source",
        "forge_human_review",
        "accept_risk_for_user",
        "create_formal_blocker_without_request",
    )

    def __post_init__(self) -> None:
        self.workspace_repo = WorkspaceRepo(self.paths)
        self.task_repo = TaskRepo(self.paths)
        self.state_repo = StateRepo(self.paths)
        self.message_repo = MessageRepo(self.paths)
        self.artifact_repo = ArtifactRepo(self.paths)
        self.blocker_repo = BlockerRepo(self.paths)
        self.review_repo = ReviewRepo(self.paths)
        self.risk_repo = RiskRepo(self.message_repo)
        self.blocker_service = BlockerService(
            message_repo=self.message_repo,
            blocker_repo=self.blocker_repo,
            state_repo=self.state_repo,
            state_machine=self.state_machine,
            risk_repo=self.risk_repo,
        )
        self.risk_prompt_service = RiskPromptRegenerationService()
        self.risk_decision_service = RiskDecisionService(
            risk_repo=self.risk_repo,
            state_repo=self.state_repo,
            prompt_service=self.risk_prompt_service,
            state_machine=self.state_machine,
        )
        self.review_service = ReviewService(
            review_repo=self.review_repo,
            state_repo=self.state_repo,
            message_repo=self.message_repo,
            state_machine=self.state_machine,
            risk_decision_service=self.risk_decision_service,
        )
        self.final_delivery_service = FinalDeliveryService(
            state_repo=self.state_repo,
            task_repo=self.task_repo,
            artifact_repo=self.artifact_repo,
            review_repo=self.review_repo,
            risk_repo=self.risk_repo,
            message_repo=self.message_repo,
        )
        self.prompt_service = PromptService(
            self.paths,
            state_repo=self.state_repo,
            artifact_repo=self.artifact_repo,
            message_repo=self.message_repo,
            risk_repo=self.risk_repo,
        )
        self.task_identity_service = TaskIdentityService(self.workspace_repo)

    def load_active_task(self) -> str | None:
        return self.workspace_repo.read_active_task_id()

    def validate_task_identity(self, explicit_task_id: str | None = None) -> str:
        return self.task_identity_service.resolve_task_id(explicit_task_id)

    def transition_to_next_status(
        self,
        task_id: str,
        target_status: TaskStatus | str,
        *,
        reason: str = "controller transition",
        review_valid: bool = False,
        final_review_valid: bool = False,
    ) -> StateTransitionResult:
        state, body = self.state_repo.read_with_body(task_id)
        target = parse_enum(TaskStatus, target_status, "target_status")
        result = self.state_machine.transition(
            state,
            target,
            actor=Role.CONTROLLER,
            reason=reason,
            review_valid=review_valid,
            final_review_valid=final_review_valid,
        )
        self.state_repo.write_with_history(
            task_id,
            result.state,
            result.history_entry(),
            actor=Role.CONTROLLER,
            body=body,
        )
        return result

    def startup_recovery_check(self, task_id: str) -> StateTransitionResult:
        state, body = self.state_repo.read_with_body(task_id)
        architect_review_valid = self._review_record_valid(
            task_id,
            review_type=ReviewType.ARCHITECT_REVIEW,
        )
        final_review_valid = self._review_record_valid(
            task_id,
            review_type=ReviewType.FINAL_REVIEW,
        )
        result = self.state_machine.controller_startup_recovery_check(
            state,
            architect_review_valid=architect_review_valid,
            final_review_valid=final_review_valid,
            actor=Role.CONTROLLER,
        )
        if result.changed:
            self.state_repo.write_with_history(
                task_id,
                result.state,
                result.history_entry(),
                actor=Role.CONTROLLER,
                body=body,
            )
        return result

    def recover_from_blocked(
        self,
        task_id: str,
        resume_to_status: TaskStatus | str,
        resume_to_agent: Role | str,
        *,
        missing_artifacts_resolved: bool,
        reason: str = "controller blocked recovery",
    ) -> StateTransitionResult:
        state, body = self.state_repo.read_with_body(task_id)
        target = parse_enum(TaskStatus, resume_to_status, "resume_to_status")
        result = self.state_machine.recover_from_blocked(
            state,
            target,
            resume_to_agent,
            missing_artifacts_resolved=missing_artifacts_resolved,
            actor=Role.CONTROLLER,
            reason=reason,
        )
        self.state_repo.write_with_history(
            task_id,
            result.state,
            result.history_entry(),
            actor=Role.CONTROLLER,
            body=body,
        )
        return result

    def report_status(self, task_id: str) -> dict[str, Any]:
        state = self.state_repo.read(task_id)
        archive_hint = self.state_repo.archive_history_suggestion(
            task_id,
            self.state_repo.read_with_body(task_id)[1],
        )
        return {
            "task_id": task_id,
            "current_status": state.current_status.value,
            "previous_status": state.previous_status.value,
            "current_agent": state.current_agent.value if state.current_agent else "none",
            "next_agent": state.next_agent.value if state.next_agent else "none",
            "human_review_status": state.human_review_status.value,
            "final_review_status": state.final_review_status.value,
            "active_blocker": state.active_blocker,
            "archive_hint": archive_hint,
        }

    def handle_gate_failure_message(self, message_path: Path) -> dict[str, str]:
        message = self.message_repo.read_message(message_path)
        if message.message_type.value != "gate_failure":
            raise BlockerError("handle_gate_failure_message requires message_type gate_failure")
        return {
            "action": "acknowledged",
            "message_id": message.message_id,
            "state_changed": "false",
            "formal_blocker_created": "false",
            "reason": "gate_failure is not a real flow blocker",
        }

    def handle_blocker_request(self, message_path: Path) -> FormalBlockerResult:
        return self.create_formal_blocker(message_path)

    def create_formal_blocker(self, request_path: Path) -> FormalBlockerResult:
        return self.blocker_service.create_formal_blocker_from_request(request_path)

    def resolve_active_blocker(
        self,
        task_id: str,
        *,
        missing_artifacts_resolved: bool,
    ) -> BlockerResolveResult:
        state = self.state_repo.read(task_id)
        if state.blocked_context is None:
            raise BlockerError("active blocker cannot be resolved without blocked_context")
        return self.blocker_service.resolve_blocker(
            task_id=task_id,
            resume_to_status=state.blocked_context.resume_to_status,
            resume_to_agent=state.blocked_context.resume_to_agent,
            missing_artifacts_resolved=missing_artifacts_resolved,
        )

    def create_architect_review_record(
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
    ) -> ReviewRecord:
        return self.review_service.create_architect_review(
            task_id=task_id,
            reviewer=reviewer,
            verdict=verdict,
            reviewed_artifacts=reviewed_artifacts,
            issues=issues,
            followup_required=followup_required,
            notes=notes,
            overwrite=overwrite,
        )

    def create_final_review_record(
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
    ) -> ReviewRecord:
        return self.review_service.create_final_review(
            task_id=task_id,
            reviewer=reviewer,
            verdict=verdict,
            reviewed_artifacts=reviewed_artifacts,
            issues=issues,
            followup_required=followup_required,
            notes=notes,
            overwrite=overwrite,
        )

    def approve_architect_review(self, task_id: str) -> tuple[ReviewFlowResult, ReviewFlowResult]:
        step_1 = self.review_service.approve_architect_review_step_1(task_id)
        step_2 = self.review_service.approve_architect_review_step_2(task_id)
        return step_1, step_2

    def reject_architect_review(
        self,
        task_id: str,
        *,
        multiple_resume_candidates: bool = False,
    ) -> ReviewFlowResult:
        return self.review_service.reject_architect_review(
            task_id,
            multiple_resume_candidates=multiple_resume_candidates,
        )

    def approve_final_review(
        self,
        task_id: str,
        *,
        test_report_clean: bool | None = None,
    ) -> tuple[ReviewFlowResult, ReviewFlowResult]:
        step_1 = self.review_service.approve_final_review_step_1(task_id)
        step_2 = self.review_service.approve_final_review_step_2(task_id)
        return step_1, step_2

    def reject_final_review(
        self,
        task_id: str,
        *,
        multiple_resume_candidates: bool = False,
    ) -> ReviewFlowResult:
        return self.review_service.reject_final_review(
            task_id,
            multiple_resume_candidates=multiple_resume_candidates,
        )

    def validate_final_delivery_gate(self, task_id: str) -> FinalDeliveryGateResult:
        return self.final_delivery_service.validate_final_delivery_gate(task_id)

    def finalize_task(self, task_id: str) -> Path:
        self.ensure_no_unresolved_blocking_risks(task_id)
        gate = self.validate_final_delivery_gate(task_id)
        if not gate.ok:
            raise FinalDeliveryError("; ".join(gate.errors))
        return self.final_delivery_service.write_final_delivery(task_id)

    def create_risk_finding(
        self,
        *,
        task_id: str,
        source_agent: Role,
        category: RiskCategory,
        severity: RiskSeverity,
        title: str,
        description: str,
        evidence: str,
        affected_files: list[str],
        affected_artifacts: list[str],
        recommended_options: list[str],
        default_recommendation: str | None = None,
    ) -> RuntimeRiskFinding:
        return self.risk_decision_service.create_risk_finding(
            task_id=task_id,
            source_agent=source_agent,
            category=category,
            severity=severity,
            title=title,
            description=description,
            evidence=evidence,
            affected_files=affected_files,
            affected_artifacts=affected_artifacts,
            recommended_options=recommended_options,
            default_recommendation=default_recommendation,
        )

    def request_human_risk_decision(self, task_id: str) -> list[RuntimeRiskFinding]:
        return [
            risk
            for risk in self.risk_repo.list_open_risks(task_id)
            if risk.requires_human_decision
        ]

    def record_risk_decision(
        self,
        *,
        task_id: str,
        risk_id: str,
        decision_by: str,
        selected_option: str,
        decision: RiskDecisionAction | str,
        reason: str,
    ) -> RiskDecision:
        return self.risk_decision_service.record_decision(
            task_id=task_id,
            risk_id=risk_id,
            decision_by=decision_by,
            selected_option=selected_option,
            decision=decision,
            reason=reason,
        )

    def apply_risk_decision(self, task_id: str, decision: RiskDecision) -> RuntimeRiskFinding:
        return self.risk_decision_service.apply_decision(task_id=task_id, decision=decision)

    def dispatch_risk_prompt(self, task_id: str, decision: RiskDecision) -> str:
        risk = self.risk_repo.find_risk(task_id, decision.risk_id)
        state = self.state_repo.read(task_id)
        prompt = self.risk_prompt_service.generate_prompt_for_decision(
            risk=risk,
            decision=decision,
            state=state,
        )
        self.risk_repo.write_risk_dispatch(task_id=task_id, decision=decision, prompt=prompt)
        return prompt

    def ensure_no_unresolved_blocking_risks(self, task_id: str) -> None:
        self.risk_decision_service.ensure_no_unresolved_blocking_risks(task_id)

    def generate_prompt(self, task_id: str) -> str:
        return self.prompt_service.generate_controller_prompt(task_id)

    def _review_record_valid(self, task_id: str, *, review_type: ReviewType) -> bool:
        filename = (
            "architect-review.md"
            if review_type == ReviewType.ARCHITECT_REVIEW
            else "final-review.md"
        )
        path = self.paths.human_reviews_dir(task_id) / filename
        if not path.exists():
            return False
        try:
            document = frontmatter.load(path)
            record = ReviewRecord.from_frontmatter(document.data)
        except (FrontmatterError, RepositoryError, SchemaError, OSError, ValueError):
            return False
        return (
            record.task_id == task_id
            and record.review_type == review_type
            and record.verdict == ReviewVerdict.APPROVED
        )
