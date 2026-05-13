"""Blocker request, formal blocker creation, and resolve flow."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from a2a_runtime.core.clock import Clock
from a2a_runtime.core.constants import (
    MessageType,
    RiskCategory,
    RiskSeverity,
    Role,
    TaskStatus,
    normalize_role,
    parse_enum,
    role_to_wire,
)
from a2a_runtime.core.errors import BlockerError, GateError, SchemaError
from a2a_runtime.models.blocker import Blocker
from a2a_runtime.models._coerce import as_str_list
from a2a_runtime.models.message import Message
from a2a_runtime.models.state import BlockedContext
from a2a_runtime.repositories.blocker_repo import BlockerRepo
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.risk_repo import RiskRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.services.risk_decision_service import RiskDecisionService
from a2a_runtime.services.state_machine import StateMachine, StateTransitionResult

PROFESSIONAL_BLOCKER_REQUEST_ROLES = {
    Role.PM,
    Role.ARCHITECT,
    Role.DEVELOPER,
    Role.QA,
}

REQUIRED_BLOCKER_REQUEST_PAYLOAD_FIELDS = {
    "proposed_blocked_from_agent",
    "proposed_blocked_from_status",
    "proposed_resume_to_agent",
    "proposed_resume_to_status",
    "proposed_blocking_reason",
    "proposed_missing_artifacts",
    "proposed_required_fix",
}


@dataclass(frozen=True)
class FormalBlockerResult:
    blocker: Blocker
    transition: StateTransitionResult
    notification_message: Message
    blocker_path: Path


@dataclass(frozen=True)
class BlockerResolveResult:
    transition: StateTransitionResult
    handoff_message: Message


class BlockerService:
    def __init__(
        self,
        *,
        message_repo: MessageRepo,
        blocker_repo: BlockerRepo,
        state_repo: StateRepo,
        state_machine: StateMachine | None = None,
        risk_repo: RiskRepo | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.message_repo = message_repo
        self.blocker_repo = blocker_repo
        self.state_repo = state_repo
        self.state_machine = state_machine or StateMachine(clock=clock)
        self.clock = clock or Clock()
        self.risk_decision_service = (
            RiskDecisionService(risk_repo=risk_repo, state_repo=state_repo, clock=self.clock)
            if risk_repo is not None
            else None
        )

    def create_blocker_request(
        self,
        *,
        task_id: str,
        from_agent: Role,
        blocked_from_status: TaskStatus,
        resume_to_agent: Role,
        resume_to_status: TaskStatus,
        blocking_reason: str,
        missing_artifacts: list[str],
        required_fix: str,
        summary: str | None = None,
        body: str = "",
    ) -> Message:
        if from_agent not in PROFESSIONAL_BLOCKER_REQUEST_ROLES:
            raise GateError("only pm, architect, developer, or qa may create blocker_request")
        seq = self.message_repo.next_sequence(task_id)
        message = Message(
            message_id=f"M-{task_id}-{seq:03d}",
            task_id=task_id,
            from_agent=from_agent,
            to_agent=Role.CONTROLLER,
            message_type=MessageType.BLOCKER,
            intent="blocker_request",
            summary=summary or blocking_reason,
            payload={
                "proposed_blocked_from_agent": role_to_wire(from_agent),
                "proposed_blocked_from_status": blocked_from_status.value,
                "proposed_resume_to_agent": role_to_wire(resume_to_agent),
                "proposed_resume_to_status": resume_to_status.value,
                "proposed_blocking_reason": blocking_reason,
                "proposed_missing_artifacts": list(missing_artifacts),
                "proposed_required_fix": required_fix,
            },
            referenced_artifacts=[],
            required_response=True,
            blockers=[],
            created_at=self.clock.now_iso(),
        )
        self.message_repo.write_message(message, body)
        return message

    def create_formal_blocker_from_request(
        self,
        request_path: Path,
        *,
        body: str = "",
    ) -> FormalBlockerResult:
        request = self.message_repo.read_message(request_path)
        self._validate_blocker_request_message(request)
        state, state_body = self.state_repo.read_with_body(request.task_id)
        if state.active_blocker is not None:
            raise BlockerError("cannot create a new formal blocker while active_blocker is set")

        payload = request.payload
        seq = self.blocker_repo.next_sequence(request.task_id)
        blocker = Blocker(
            blocker_id=f"B-{request.task_id}-{seq:03d}",
            task_id=request.task_id,
            blocked_from_agent=self._role(payload["proposed_blocked_from_agent"]),
            blocked_from_status=self._status(payload["proposed_blocked_from_status"]),
            resume_to_agent=self._role(payload["proposed_resume_to_agent"]),
            resume_to_status=self._status(payload["proposed_resume_to_status"]),
            blocking_reason=str(payload["proposed_blocking_reason"]),
            missing_artifacts=as_str_list(
                payload["proposed_missing_artifacts"],
                "proposed_missing_artifacts",
            ),
            required_fix=str(payload["proposed_required_fix"]),
            created_by=Role.CONTROLLER.value,
            source_request_message=request.message_id,
            created_at=self.clock.now_iso(),
        )
        blocker_path = self.blocker_repo.write_blocker(
            blocker,
            body or self._formal_blocker_body(blocker),
        )

        blocked_context = BlockedContext(
            blocker_id=blocker.blocker_id,
            blocked_from_agent=blocker.blocked_from_agent,
            blocked_from_status=blocker.blocked_from_status,
            resume_to_agent=blocker.resume_to_agent,
            resume_to_status=blocker.resume_to_status,
            blocking_reason=blocker.blocking_reason,
            missing_artifacts=list(blocker.missing_artifacts),
            required_fix=blocker.required_fix,
        )
        next_state = replace(
            state,
            previous_status=state.current_status,
            current_status=TaskStatus.BLOCKED,
            current_agent=Role.CONTROLLER,
            next_agent=blocker.resume_to_agent,
            allowed_next_statuses=[blocker.resume_to_status],
            active_blocker=blocker.blocker_id,
            blockers_history=[*state.blockers_history, blocker.blocker_id],
            blocked_context=blocked_context,
            updated_at=self.clock.now_iso(),
        )
        transition = StateTransitionResult(
            previous_state=state,
            state=next_state,
            actor=Role.CONTROLLER,
            reason=f"formal blocker created from {request.message_id}",
            at=next_state.updated_at,
        )
        self.state_repo.write_with_history(
            request.task_id,
            next_state,
            transition.history_entry(),
            actor=Role.CONTROLLER,
            body=state_body,
        )
        notification = self._write_controller_blocker_notification(blocker)
        return FormalBlockerResult(
            blocker=blocker,
            transition=transition,
            notification_message=notification,
            blocker_path=blocker_path,
        )

    def resolve_blocker(
        self,
        *,
        task_id: str,
        resume_to_status: TaskStatus,
        resume_to_agent: Role,
        missing_artifacts_resolved: bool,
        multiple_resume_candidates: bool = False,
    ) -> BlockerResolveResult:
        state, state_body = self.state_repo.read_with_body(task_id)
        if multiple_resume_candidates:
            if self.risk_decision_service is None:
                raise BlockerError("multiple resume candidates require RiskDecisionService")
            self.risk_decision_service.create_risk_finding(
                task_id=task_id,
                source_agent=Role.CONTROLLER,
                category=RiskCategory.ROLLBACK,
                severity=RiskSeverity.P1_HIGH,
                title="Multiple blocker resume targets require human decision",
                description="Controller found multiple reasonable resume targets.",
                evidence="multiple_resume_candidates=True",
                affected_files=[],
                affected_artifacts=[],
                recommended_options=[
                    "send_to_pm",
                    "send_to_architect",
                    "send_to_developer",
                    "send_to_qa",
                    "cancel_task",
                ],
                default_recommendation="send_to_architect",
            )
            raise BlockerError("multiple resume candidates require Human Risk Decision Gate")
        if state.active_blocker is None or state.blocked_context is None:
            raise BlockerError("state must have active_blocker and blocked_context to resolve blocker")
        self.blocker_repo.find_active_blocker(task_id, state)
        transition = self.state_machine.recover_from_blocked(
            state,
            resume_to_status,
            resume_to_agent,
            missing_artifacts_resolved=missing_artifacts_resolved,
            actor=Role.CONTROLLER,
            reason=f"resolve blocker {state.active_blocker}",
        )
        self.state_repo.write_with_history(
            task_id,
            transition.state,
            transition.history_entry(),
            actor=Role.CONTROLLER,
            body=state_body,
        )
        handoff = self._write_controller_handoff(
            task_id=task_id,
            to_agent=resume_to_agent,
            state_snapshot=transition.state.current_status.value,
        )
        return BlockerResolveResult(transition=transition, handoff_message=handoff)

    def _validate_blocker_request_message(self, message: Message) -> None:
        if message.message_type != MessageType.BLOCKER or message.intent != "blocker_request":
            raise BlockerError("formal blocker can only be created from blocker_request message")
        if message.from_agent not in PROFESSIONAL_BLOCKER_REQUEST_ROLES:
            raise GateError("blocker_request must come from a professional agent")
        missing = sorted(REQUIRED_BLOCKER_REQUEST_PAYLOAD_FIELDS.difference(message.payload))
        if missing:
            raise SchemaError(f"blocker_request payload missing fields: {', '.join(missing)}")

    def _role(self, value: Any) -> Role:
        role = normalize_role(value, field_name="role")
        if role is None:
            raise SchemaError("role cannot be none")
        return role

    def _status(self, value: Any) -> TaskStatus:
        return parse_enum(TaskStatus, value, "status")

    def _write_controller_blocker_notification(self, blocker: Blocker) -> Message:
        seq = self.message_repo.next_sequence(blocker.task_id)
        message = Message(
            message_id=f"M-{blocker.task_id}-{seq:03d}",
            task_id=blocker.task_id,
            from_agent=Role.CONTROLLER,
            to_agent=blocker.resume_to_agent,
            message_type=MessageType.BLOCKER,
            intent="blocker",
            summary=blocker.blocking_reason,
            payload={
                "blocker_id": blocker.blocker_id,
                "resume_to_agent": role_to_wire(blocker.resume_to_agent),
                "resume_to_status": blocker.resume_to_status.value,
                "required_fix": blocker.required_fix,
            },
            referenced_artifacts=[],
            required_response=True,
            blockers=[blocker.blocker_id],
            created_at=self.clock.now_iso(),
        )
        self.message_repo.write_message(message)
        return message

    def _write_controller_handoff(
        self,
        *,
        task_id: str,
        to_agent: Role,
        state_snapshot: str,
    ) -> Message:
        seq = self.message_repo.next_sequence(task_id)
        message = Message(
            message_id=f"M-{task_id}-{seq:03d}",
            task_id=task_id,
            from_agent=Role.CONTROLLER,
            to_agent=to_agent,
            message_type=MessageType.HANDOFF,
            intent="handoff",
            summary="blocker resolved; resume workflow",
            payload={
                "state_snapshot": {"current_status": state_snapshot},
                "reason": "blocker_resolved",
            },
            referenced_artifacts=[],
            required_response=True,
            blockers=[],
            created_at=self.clock.now_iso(),
        )
        self.message_repo.write_message(message)
        return message

    def _formal_blocker_body(self, blocker: Blocker) -> str:
        missing = ", ".join(blocker.missing_artifacts) or "none"
        return (
            "## 已读取的上游 Artifact 与缺漏点\n"
            f"- missing_artifacts: {missing}\n\n"
            "## 给 resume_to_agent 的具体修复指引\n"
            f"- {blocker.required_fix}\n"
        )
