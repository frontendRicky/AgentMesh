"""Human Risk Decision Gate service."""

from __future__ import annotations

from dataclasses import replace

from a2a_runtime.core.clock import Clock
from a2a_runtime.core.constants import (
    RiskCategory,
    RiskDecisionAction,
    RiskSeverity,
    RiskStatus,
    Role,
    TaskStatus,
    parse_enum,
)
from a2a_runtime.core.errors import RiskDecisionError
from a2a_runtime.models.risk import RuntimeRiskFinding
from a2a_runtime.models.risk_decision import RiskDecision, RiskOption
from a2a_runtime.models.review import ROLE_REVIEWER_VALUES
from a2a_runtime.repositories.risk_repo import RiskRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.services.risk_prompt_regeneration_service import RiskPromptRegenerationService
from a2a_runtime.services.state_machine import StateMachine, StateTransitionResult


class RiskDecisionService:
    def __init__(
        self,
        *,
        risk_repo: RiskRepo,
        state_repo: StateRepo,
        prompt_service: RiskPromptRegenerationService | None = None,
        state_machine: StateMachine | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.risk_repo = risk_repo
        self.state_repo = state_repo
        self.prompt_service = prompt_service or RiskPromptRegenerationService()
        self.clock = clock or Clock()
        self.state_machine = state_machine or StateMachine(clock=self.clock)

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
        source_file: str | None = None,
        source_artifact: str | None = None,
        requires_human_decision: bool | None = None,
    ) -> RuntimeRiskFinding:
        seq = self.risk_repo.next_risk_sequence(task_id)
        requires = self.requires_human_decision(severity) if requires_human_decision is None else requires_human_decision
        status = RiskStatus.WAITING_HUMAN_DECISION if requires else RiskStatus.OPEN
        risk = RuntimeRiskFinding(
            risk_id=self.risk_repo.build_risk_id(task_id, seq),
            task_id=task_id,
            source_agent=source_agent,
            source_file=source_file,
            source_artifact=source_artifact,
            category=category,
            severity=severity,
            title=title,
            description=description,
            evidence=evidence,
            affected_files=affected_files,
            affected_artifacts=affected_artifacts,
            detected_at=self.clock.now_iso(),
            requires_human_decision=requires,
            recommended_options=recommended_options,
            default_recommendation=default_recommendation,
            status=status,
        )
        self.risk_repo.write_risk_review_request(risk)
        return risk

    def requires_human_decision(self, severity: RiskSeverity | str) -> bool:
        parsed = parse_enum(RiskSeverity, severity, "severity")
        return parsed in {
            RiskSeverity.P0_BLOCKER,
            RiskSeverity.P1_HIGH,
            RiskSeverity.P2_MEDIUM,
        }

    def render_options(self, risk: RuntimeRiskFinding) -> list[RiskOption]:
        return [self._option_from_decision(value) for value in risk.recommended_options]

    def record_decision(
        self,
        *,
        task_id: str,
        risk_id: str,
        decision_by: str,
        selected_option: str,
        decision: RiskDecisionAction | str,
        reason: str,
        local_user: str | None = None,
        user_mismatch_warning: bool = False,
    ) -> RiskDecision:
        if decision_by in ROLE_REVIEWER_VALUES:
            raise RiskDecisionError("decision_by must be a real user handle")
        if not reason.strip():
            raise RiskDecisionError("reason is required")
        risk = self.risk_repo.find_risk(task_id, risk_id)
        parsed_decision = parse_enum(RiskDecisionAction, decision, "decision")
        options = self.render_options(risk)
        selected = self._select_option(options, selected_option, parsed_decision)
        self._validate_decision_against_risk(risk, parsed_decision, reason)
        seq = len(self.risk_repo.list_decisions(task_id)) + 1
        decision_record = RiskDecision(
            decision_id=f"RD-{task_id}-{seq:03d}",
            risk_id=risk_id,
            task_id=task_id,
            decision_by=decision_by,
            decision_at=self.clock.now_iso(),
            decision=parsed_decision,
            selected_option=selected.option_id,
            reason=reason,
            allowed_next_action=parsed_decision.value,
            requires_regeneration=selected.requires_regeneration,
            target_agent=selected.target_agent,
            target_status=selected.target_status,
            local_user=local_user,
            user_mismatch_warning=user_mismatch_warning,
        )
        self.risk_repo.write_risk_decision(decision_record)
        return decision_record

    def apply_decision(
        self,
        *,
        task_id: str,
        decision: RiskDecision,
    ) -> RuntimeRiskFinding:
        risk = self.risk_repo.find_risk(task_id, decision.risk_id)
        if decision.decision == RiskDecisionAction.CANCEL_TASK:
            self._cancel_task(task_id, decision)
            return replace(risk, status=RiskStatus.REJECTED)
        if decision.decision == RiskDecisionAction.CONVERT_TO_BLOCKER:
            prompt = self.prompt_service.generate_prompt_for_decision(
                risk=risk,
                decision=decision,
                state=self.state_repo.read(task_id),
            )
            self.risk_repo.write_risk_dispatch(task_id=task_id, decision=decision, prompt=prompt)
            return replace(risk, status=RiskStatus.CONVERTED_TO_BLOCKER)
        if decision.decision == RiskDecisionAction.MARK_MANUAL_REQUIRED:
            prompt = self.prompt_service.generate_prompt_for_decision(
                risk=risk,
                decision=decision,
                state=self.state_repo.read(task_id),
            )
            self.risk_repo.write_risk_dispatch(task_id=task_id, decision=decision, prompt=prompt)
            return replace(risk, status=RiskStatus.PENDING_MANUAL_REVIEW)
        if decision.requires_regeneration:
            prompt = self.prompt_service.generate_prompt_for_decision(
                risk=risk,
                decision=decision,
                state=self.state_repo.read(task_id),
            )
            self.risk_repo.write_risk_dispatch(task_id=task_id, decision=decision, prompt=prompt)
            return replace(risk, status=RiskStatus.SENT_TO_REPLAN)
        return replace(risk, status=RiskStatus.ACCEPTED)

    def ensure_no_unresolved_blocking_risks(self, task_id: str) -> None:
        blocking = [
            risk
            for risk in self.risk_repo.list_open_risks(task_id)
            if risk.severity in {RiskSeverity.P0_BLOCKER, RiskSeverity.P1_HIGH}
        ]
        if blocking:
            ids = ", ".join(risk.risk_id for risk in blocking)
            raise RiskDecisionError(f"unresolved P0/P1 risks block progress: {ids}")

    def _validate_decision_against_risk(
        self,
        risk: RuntimeRiskFinding,
        decision: RiskDecisionAction,
        reason: str,
    ) -> None:
        allowed = {option.decision for option in self.render_options(risk)}
        if decision not in allowed:
            raise RiskDecisionError("decision is not one of this risk's recommended options")
        if risk.severity == RiskSeverity.P0_BLOCKER and decision in {
            RiskDecisionAction.APPROVE_CONTINUE,
            RiskDecisionAction.ACCEPT_RISK_AND_CONTINUE,
            RiskDecisionAction.MARK_MANUAL_REQUIRED,
        }:
            raise RiskDecisionError("P0 risk cannot be approved, accepted, or marked manual_required")
        if (
            risk.severity == RiskSeverity.P1_HIGH
            and decision == RiskDecisionAction.ACCEPT_RISK_AND_CONTINUE
            and not reason.strip()
        ):
            raise RiskDecisionError("P1 accept_risk_and_continue requires reason")

    def _select_option(
        self,
        options: list[RiskOption],
        selected_option: str,
        decision: RiskDecisionAction,
    ) -> RiskOption:
        for option in options:
            if option.option_id == selected_option or option.decision == decision:
                return option
        raise RiskDecisionError("selected_option is not available for this risk")

    def _option_from_decision(self, value: str) -> RiskOption:
        decision = parse_enum(RiskDecisionAction, value, "recommended_options[]")
        target_agent, target_status, requires_regeneration = self._target_for(decision)
        return RiskOption(
            option_id=decision.value,
            label=decision.value.replace("_", " "),
            decision=decision,
            target_agent=target_agent,
            target_status=target_status,
            requires_regeneration=requires_regeneration,
            description=f"Dispatch {decision.value}",
        )

    def _target_for(
        self,
        decision: RiskDecisionAction,
    ) -> tuple[Role | None, TaskStatus | None, bool]:
        mapping = {
            RiskDecisionAction.REJECT_AND_REPLAN: (Role.ARCHITECT, TaskStatus.ARCHITECT_PROCESSING, True),
            RiskDecisionAction.SEND_TO_PM: (Role.PM, TaskStatus.PM_PROCESSING, True),
            RiskDecisionAction.SEND_TO_ARCHITECT: (
                Role.ARCHITECT,
                TaskStatus.ARCHITECT_PROCESSING,
                True,
            ),
            RiskDecisionAction.SEND_TO_DEVELOPER: (
                Role.DEVELOPER,
                TaskStatus.DEVELOPER_PROCESSING,
                True,
            ),
            RiskDecisionAction.SEND_TO_QA: (Role.QA, TaskStatus.QA_PROCESSING, True),
            RiskDecisionAction.CONVERT_TO_BLOCKER: (Role.CONTROLLER, TaskStatus.BLOCKED, True),
            RiskDecisionAction.MARK_MANUAL_REQUIRED: (Role.QA, TaskStatus.QA_PROCESSING, True),
            RiskDecisionAction.CANCEL_TASK: (Role.CONTROLLER, TaskStatus.CANCELLED, False),
        }
        return mapping.get(decision, (None, None, False))

    def _cancel_task(self, task_id: str, decision: RiskDecision) -> StateTransitionResult:
        state, body = self.state_repo.read_with_body(task_id)
        result = self.state_machine.transition(
            state,
            TaskStatus.CANCELLED,
            actor=Role.CONTROLLER,
            reason=f"risk decision {decision.decision_id}: cancel task",
        )
        self.state_repo.write_with_history(
            task_id,
            result.state,
            result.history_entry(),
            actor=Role.CONTROLLER,
            body=body,
        )
        return result
