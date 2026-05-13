"""State machine execution for the frozen A2A v1 status graph."""

from __future__ import annotations

from dataclasses import dataclass, replace

from a2a_runtime.core.clock import Clock
from a2a_runtime.core.constants import (
    ALLOWED_TASK_TRANSITIONS,
    TERMINAL_TASK_STATUSES,
    ReviewStatus,
    Role,
    TaskStatus,
    normalize_role,
    role_to_wire,
)
from a2a_runtime.core.errors import StateMachineError
from a2a_runtime.models.state import State

_SENTINEL = object()


@dataclass(frozen=True)
class StateTransitionResult:
    previous_state: State
    state: State
    actor: Role
    reason: str
    at: str
    changed: bool = True
    recovery: bool = False

    def history_entry(self) -> dict[str, str]:
        return {
            "previous_status": self.previous_state.current_status.value,
            "current_status": self.state.current_status.value,
            "actor": role_to_wire(self.actor),
            "reason": self.reason,
            "at": self.at,
        }


class StateMachine:
    """Pure state transition engine.

    This service does not write files. Repositories are responsible for
    persisting the returned state and appending write history to Markdown body.
    """

    def __init__(self, clock: Clock | None = None) -> None:
        self.clock = clock or Clock()

    def allowed_next_statuses(self, status: TaskStatus) -> list[TaskStatus]:
        return sorted(ALLOWED_TASK_TRANSITIONS[status], key=lambda item: item.value)

    def can_transition(
        self,
        state: State,
        target_status: TaskStatus,
        *,
        review_valid: bool = False,
        final_review_valid: bool = False,
    ) -> bool:
        try:
            self.validate_transition(
                state,
                target_status,
                review_valid=review_valid,
                final_review_valid=final_review_valid,
            )
        except StateMachineError:
            return False
        return True

    def validate_transition(
        self,
        state: State,
        target_status: TaskStatus,
        *,
        review_valid: bool = False,
        final_review_valid: bool = False,
    ) -> None:
        if state.current_status in TERMINAL_TASK_STATUSES:
            raise StateMachineError(f"{state.current_status.value} is terminal")

        if target_status not in ALLOWED_TASK_TRANSITIONS[state.current_status]:
            raise StateMachineError(
                f"illegal transition: {state.current_status.value} -> {target_status.value}",
            )

        if (
            state.current_status == TaskStatus.HUMAN_REVIEW_REQUIRED
            and target_status == TaskStatus.DEVELOPER_PROCESSING
        ):
            if state.human_review_status != ReviewStatus.APPROVED:
                raise StateMachineError(
                    "human_review_required -> developer_processing requires "
                    "human_review_status == approved",
                )
            if not review_valid:
                raise StateMachineError(
                    "human_review_required -> developer_processing requires valid review record",
                )

        if (
            state.current_status == TaskStatus.HUMAN_REVIEW_REQUIRED
            and target_status == TaskStatus.ARCHITECT_PROCESSING
            and state.human_review_status != ReviewStatus.REJECTED
        ):
            raise StateMachineError(
                "human_review_required -> architect_processing requires "
                "human_review_status == rejected",
            )

        if (
            state.current_status == TaskStatus.FINAL_REVIEW_REQUIRED
            and target_status == TaskStatus.COMPLETED
        ):
            if state.final_review_status != ReviewStatus.APPROVED:
                raise StateMachineError(
                    "final_review_required -> completed requires final_review_status == approved",
                )
            if not final_review_valid:
                raise StateMachineError(
                    "final_review_required -> completed requires valid final review record",
                )

        if (
            state.current_status == TaskStatus.FINAL_REVIEW_REQUIRED
            and target_status == TaskStatus.DEVELOPER_PROCESSING
            and state.final_review_status != ReviewStatus.REJECTED
        ):
            raise StateMachineError(
                "final_review_required -> developer_processing requires "
                "final_review_status == rejected",
            )

        if state.current_status == TaskStatus.BLOCKED:
            raise StateMachineError("blocked recovery must use recover_from_blocked")

    def transition(
        self,
        state: State,
        target_status: TaskStatus,
        *,
        actor: Role | str = Role.CONTROLLER,
        reason: str = "state transition",
        review_valid: bool = False,
        final_review_valid: bool = False,
    ) -> StateTransitionResult:
        actor_role = self._actor(actor)
        self.validate_transition(
            state,
            target_status,
            review_valid=review_valid,
            final_review_valid=final_review_valid,
        )

        next_state = self._replace_for_status(
            state,
            target_status,
            previous_status=state.current_status,
        )
        return self._result(state, next_state, actor_role, reason)

    def approve_architect_review_step_1(
        self,
        state: State,
        *,
        actor: Role | str = Role.CONTROLLER,
        reason: str = "approve architect review step 1",
    ) -> StateTransitionResult:
        if state.current_status != TaskStatus.HUMAN_REVIEW_REQUIRED:
            raise StateMachineError("architect review step 1 requires human_review_required")
        next_state = replace(
            state,
            human_review_status=ReviewStatus.APPROVED,
            updated_at=self.clock.now_iso(),
        )
        return self._result(state, next_state, self._actor(actor), reason)

    def approve_architect_review_step_2(
        self,
        state: State,
        *,
        review_valid: bool,
        actor: Role | str = Role.CONTROLLER,
        reason: str = "approve architect review step 2",
    ) -> StateTransitionResult:
        return self.transition(
            state,
            TaskStatus.DEVELOPER_PROCESSING,
            actor=actor,
            reason=reason,
            review_valid=review_valid,
        )

    def approve_final_review_step_1(
        self,
        state: State,
        *,
        actor: Role | str = Role.CONTROLLER,
        reason: str = "approve final review step 1",
    ) -> StateTransitionResult:
        if state.current_status != TaskStatus.FINAL_REVIEW_REQUIRED:
            raise StateMachineError("final review step 1 requires final_review_required")
        next_state = replace(
            state,
            final_review_status=ReviewStatus.APPROVED,
            updated_at=self.clock.now_iso(),
        )
        return self._result(state, next_state, self._actor(actor), reason)

    def approve_final_review_step_2(
        self,
        state: State,
        *,
        final_review_valid: bool,
        actor: Role | str = Role.CONTROLLER,
        reason: str = "approve final review step 2",
    ) -> StateTransitionResult:
        return self.transition(
            state,
            TaskStatus.COMPLETED,
            actor=actor,
            reason=reason,
            final_review_valid=final_review_valid,
        )

    def controller_startup_recovery_check(
        self,
        state: State,
        *,
        architect_review_valid: bool = False,
        final_review_valid: bool = False,
        actor: Role | str = Role.CONTROLLER,
    ) -> StateTransitionResult:
        if (
            state.current_status == TaskStatus.HUMAN_REVIEW_REQUIRED
            and state.human_review_status == ReviewStatus.APPROVED
        ):
            if not architect_review_valid:
                raise StateMachineError("cannot recover architect review middle state without valid review")
            result = self.approve_architect_review_step_2(
                state,
                review_valid=True,
                actor=actor,
                reason="startup recovery: architect review step 2",
            )
            return replace(result, recovery=True)

        if (
            state.current_status == TaskStatus.FINAL_REVIEW_REQUIRED
            and state.final_review_status == ReviewStatus.APPROVED
        ):
            if not final_review_valid:
                raise StateMachineError("cannot recover final review middle state without valid review")
            result = self.approve_final_review_step_2(
                state,
                final_review_valid=True,
                actor=actor,
                reason="startup recovery: final review step 2",
            )
            return replace(result, recovery=True)

        return StateTransitionResult(
            previous_state=state,
            state=state,
            actor=self._actor(actor),
            reason="startup recovery: no middle state",
            at=self.clock.now_iso(),
            changed=False,
            recovery=False,
        )

    def recover_from_blocked(
        self,
        state: State,
        resume_to_status: TaskStatus,
        resume_to_agent: Role | str,
        *,
        missing_artifacts_resolved: bool,
        actor: Role | str = Role.CONTROLLER,
        reason: str = "recover from blocked",
    ) -> StateTransitionResult:
        if state.current_status != TaskStatus.BLOCKED:
            raise StateMachineError("recover_from_blocked requires current_status == blocked")
        if state.blocked_context is None:
            raise StateMachineError("blocked state must include blocked_context")
        if not missing_artifacts_resolved:
            raise StateMachineError("cannot recover blocked state before missing artifacts are resolved")

        normalized_agent = self._actor(resume_to_agent)
        if resume_to_status != state.blocked_context.resume_to_status:
            raise StateMachineError("resume_to_status does not match blocked_context")
        if normalized_agent != state.blocked_context.resume_to_agent:
            raise StateMachineError("resume_to_agent does not match blocked_context")
        if resume_to_status not in ALLOWED_TASK_TRANSITIONS[TaskStatus.BLOCKED]:
            raise StateMachineError(f"blocked cannot resume to {resume_to_status.value}")

        next_state = self._replace_for_status(
            state,
            resume_to_status,
            previous_status=TaskStatus.BLOCKED,
            current_agent=normalized_agent,
            active_blocker=None,
            blocked_context=None,
        )
        return self._result(state, next_state, self._actor(actor), reason)

    def _replace_for_status(
        self,
        state: State,
        target_status: TaskStatus,
        *,
        previous_status: TaskStatus,
        current_agent: Role | None | object = _SENTINEL,
        active_blocker: str | None | object = _SENTINEL,
        blocked_context: object = _SENTINEL,
    ) -> State:
        defaults = self._status_defaults(target_status)
        selected_agent = defaults["current_agent"] if current_agent is _SENTINEL else current_agent
        selected_blocked_context = (
            state.blocked_context if blocked_context is _SENTINEL else blocked_context
        )
        selected_active_blocker = (
            state.active_blocker if active_blocker is _SENTINEL else active_blocker
        )
        return replace(
            state,
            previous_status=previous_status,
            current_status=target_status,
            current_agent=selected_agent,
            next_agent=defaults["next_agent"],
            allowed_next_statuses=self.allowed_next_statuses(target_status),
            active_blocker=selected_active_blocker,
            blocked_context=selected_blocked_context,
            human_review_status=defaults.get("human_review_status", state.human_review_status),
            final_review_status=defaults.get("final_review_status", state.final_review_status),
            updated_at=self.clock.now_iso(),
        )

    def _status_defaults(self, status: TaskStatus) -> dict[str, Role | ReviewStatus | None]:
        defaults: dict[TaskStatus, dict[str, Role | ReviewStatus | None]] = {
            TaskStatus.CREATED: {
                "current_agent": Role.CONTROLLER,
                "next_agent": Role.PM,
            },
            TaskStatus.PM_PROCESSING: {
                "current_agent": Role.PM,
                "next_agent": Role.ARCHITECT,
            },
            TaskStatus.PM_COMPLETED: {
                "current_agent": Role.CONTROLLER,
                "next_agent": Role.ARCHITECT,
            },
            TaskStatus.ARCHITECT_PROCESSING: {
                "current_agent": Role.ARCHITECT,
                "next_agent": Role.HUMAN,
            },
            TaskStatus.ARCHITECT_COMPLETED: {
                "current_agent": Role.CONTROLLER,
                "next_agent": Role.HUMAN,
            },
            TaskStatus.HUMAN_REVIEW_REQUIRED: {
                "current_agent": Role.HUMAN,
                "next_agent": Role.DEVELOPER,
                "human_review_status": ReviewStatus.PENDING,
            },
            TaskStatus.DEVELOPER_PROCESSING: {
                "current_agent": Role.DEVELOPER,
                "next_agent": Role.QA,
            },
            TaskStatus.DEVELOPER_COMPLETED: {
                "current_agent": Role.CONTROLLER,
                "next_agent": Role.QA,
            },
            TaskStatus.QA_PROCESSING: {
                "current_agent": Role.QA,
                "next_agent": Role.HUMAN,
            },
            TaskStatus.QA_COMPLETED: {
                "current_agent": Role.CONTROLLER,
                "next_agent": Role.HUMAN,
            },
            TaskStatus.FINAL_REVIEW_REQUIRED: {
                "current_agent": Role.HUMAN,
                "next_agent": Role.CONTROLLER,
                "final_review_status": ReviewStatus.PENDING,
            },
            TaskStatus.COMPLETED: {
                "current_agent": Role.CONTROLLER,
                "next_agent": None,
            },
            TaskStatus.BLOCKED: {
                "current_agent": Role.CONTROLLER,
                "next_agent": None,
            },
            TaskStatus.CANCELLED: {
                "current_agent": Role.CONTROLLER,
                "next_agent": None,
            },
        }
        return defaults[status]

    def _result(
        self,
        previous_state: State,
        state: State,
        actor: Role,
        reason: str,
    ) -> StateTransitionResult:
        return StateTransitionResult(
            previous_state=previous_state,
            state=state,
            actor=actor,
            reason=reason,
            at=state.updated_at,
        )

    def _actor(self, actor: Role | str) -> Role:
        normalized = normalize_role(actor, field_name="actor")
        if normalized is None:
            raise StateMachineError("actor cannot be none")
        return normalized
