"""Validation service for Phase 1/2 runtime records."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from a2a_runtime.core.constants import (
    ALLOWED_TASK_TRANSITIONS,
    ReviewStatus,
    TaskStatus,
)
from a2a_runtime.core.errors import SchemaError
from a2a_runtime.core.ids import validate_task_id
from a2a_runtime.models.artifact import Artifact
from a2a_runtime.models.message import Message
from a2a_runtime.models.review import ReviewRecord
from a2a_runtime.models.state import State
from a2a_runtime.models.task import Task


@dataclass
class ValidationResult:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.ok = False
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        if not other.ok:
            self.ok = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.hints.extend(other.hints)
        return self


class ValidationService:
    def validate_task_id(self, task_id: str) -> ValidationResult:
        return self._capture(lambda: validate_task_id(task_id))

    def validate_workspace_task_dir(self, task_id: str, task_dir: Path) -> ValidationResult:
        result = self.validate_task_id(task_id)
        if task_dir.name != task_id:
            result.add_error("workspace task directory name must equal task_id")
        if not task_dir.exists():
            result.add_error(f"workspace task directory does not exist: {task_dir}")
        elif not task_dir.is_dir():
            result.add_error(f"workspace task path is not a directory: {task_dir}")
        return result

    def validate_task_frontmatter(self, data: dict[str, object]) -> ValidationResult:
        return self._capture(lambda: Task.from_frontmatter(data))

    def validate_state_frontmatter(self, data: dict[str, object]) -> ValidationResult:
        result = self._capture(lambda: State.from_frontmatter(data))
        if not result.ok:
            return result

        state = State.from_frontmatter(data)
        if state.current_status == TaskStatus.BLOCKED and state.blocked_context is None:
            result.add_error("blocked state must include blocked_context")
        if state.current_status != TaskStatus.BLOCKED and state.blocked_context is not None:
            result.add_error("blocked_context must be null unless current_status is blocked")
        if (
            state.current_status == TaskStatus.DEVELOPER_PROCESSING
            and state.human_review_status != ReviewStatus.APPROVED
        ):
            result.add_error(
                "developer_processing requires human_review_status == approved",
            )

        allowed = ALLOWED_TASK_TRANSITIONS.get(state.current_status, set())
        unexpected = [status for status in state.allowed_next_statuses if status not in allowed]
        if unexpected:
            values = ", ".join(status.value for status in unexpected)
            result.add_error(f"allowed_next_statuses contains invalid transitions: {values}")
        return result

    def validate_message_frontmatter(self, data: dict[str, object]) -> ValidationResult:
        return self._capture(lambda: Message.from_frontmatter(data))

    def validate_artifact_frontmatter(self, data: dict[str, object]) -> ValidationResult:
        return self._capture(lambda: Artifact.from_frontmatter(data))

    def validate_review_frontmatter(self, data: dict[str, object]) -> ValidationResult:
        return self._capture(lambda: ReviewRecord.from_frontmatter(data))

    def _capture(self, action: Callable[[], object]) -> ValidationResult:
        result = ValidationResult()
        try:
            action()
        except SchemaError as exc:
            result.add_error(str(exc))
        return result
