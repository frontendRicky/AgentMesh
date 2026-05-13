"""Shared prompt rendering sections for runtime prompt services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from a2a_runtime.core.constants import ReviewStatus, Role, TaskStatus, role_to_wire
from a2a_runtime.models.state import State


@dataclass(frozen=True)
class MayWriteCodeDecision:
    allowed: bool
    reason: str

    def render(self) -> str:
        return f"{'yes' if self.allowed else 'no'}, {self.reason}"


DEFAULT_FORBIDDEN_ACTIONS = [
    "Do not modify .ai-agents protocol files.",
    "Do not modify .cursor.",
    "Do not write state.md unless you are Flow Controller.",
    "Do not write blockers/** unless Controller creates a formal blocker from a valid request.",
    "Do not write human-reviews/** or impersonate the human reviewer.",
    "Do not bypass GateService, Review double-step, Blocker two-stage flow, or Risk Gate.",
    "Do not commit, push, or create merge requests unless the user explicitly asks.",
]

DEFAULT_FORBIDDEN_PATHS = [
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lock",
    "bun.lockb",
    ".github/**",
    ".gitlab-ci.yml",
    ".circleci/**",
    ".buildkite/**",
    "Dockerfile",
]

DEFAULT_RISK_TRIGGERS = [
    "P0/P1 risk",
    "方案冲突 or multiple reasonable recovery paths",
    "范围扩大",
    "file-change-plan 与实际改动不一致",
    "需要改 package.json / lock / CI/CD",
    "QA fail / blocked",
]


def render_a2a_header(
    *,
    role: Role,
    task_id: str,
    state: State,
    reading_artifacts: Iterable[str],
    producing_artifacts: Iterable[str],
    may_write_code: MayWriteCodeDecision,
) -> str:
    return render_a2a_header_v1(
        role=role,
        task_id=task_id,
        state=state,
        reading_artifacts=reading_artifacts,
        producing_artifacts=producing_artifacts,
        may_write_code=may_write_code,
    )


def render_a2a_header_v1(
    *,
    role: Role,
    task_id: str,
    state: State,
    reading_artifacts: Iterable[str],
    producing_artifacts: Iterable[str],
    may_write_code: MayWriteCodeDecision,
) -> str:
    return "\n".join(
        [
            "[A2A]",
            f"- Current Agent: {role_to_wire(role)}",
            f"- Current Task: {task_id}",
            f"- Current Status: {state.current_status.value}",
            f"- Human Review Status: {state.human_review_status.value}",
            f"- Reading Artifacts: [{', '.join(reading_artifacts)}]",
            f"- Producing Artifacts: [{', '.join(producing_artifacts)}]",
            f"- May Write Code: {may_write_code.render()}",
        ],
    )


def render_forbidden_actions(extra: Iterable[str] = ()) -> str:
    return render_forbidden_paths_or_actions(extra)


def render_forbidden_paths_or_actions(extra: Iterable[str] = ()) -> str:
    return render_bullets([*DEFAULT_FORBIDDEN_ACTIONS, *DEFAULT_FORBIDDEN_PATHS, *extra])


def render_expected_outputs(artifacts: Iterable[str], messages: Iterable[str]) -> str:
    return "\n".join(
        [
            "expected_output_artifacts:",
            render_bullets(artifacts),
            "",
            "expected_output_messages:",
            render_bullets(messages),
        ],
    )


def render_risk_triggers(extra: Iterable[str] = ()) -> str:
    triggers = [*DEFAULT_RISK_TRIGGERS, *extra]
    return "\n".join(
        [
            "If any of the following appears, stop the current phase and trigger Human Risk Decision Gate:",
            render_bullets(triggers),
            "Do not decide on behalf of the user.",
        ],
    )


def render_state_machine_requirements(role: Role) -> str:
    role_text = role_to_wire(role)
    return "\n".join(
        [
            f"- Current role must remain {role_text}.",
            "- State transitions must follow the 14-status state machine.",
            "- Human Review and Final Review are two-step flows.",
            "- Gate failures do not become formal blockers.",
            "- Formal blockers require the two-stage blocker flow.",
        ],
    )


def render_bullets(values: Iterable[str]) -> str:
    items = [str(value).strip() for value in values if str(value).strip()]
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)


def inert_state(task_id: str) -> State:
    return State(
        task_id=task_id,
        current_status=TaskStatus.CREATED,
        previous_status=TaskStatus.CREATED,
        current_agent=Role.CONTROLLER,
        next_agent=None,
        allowed_next_statuses=[],
        human_review_status=ReviewStatus.NOT_REQUIRED,
        final_review_status=ReviewStatus.NOT_REQUIRED,
        updated_at="unknown",
    )
