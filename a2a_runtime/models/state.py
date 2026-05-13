"""State model. ``state.md`` is the only dynamic state source."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from a2a_runtime.core.constants import SCHEMA_VERSION, ReviewStatus, Role, TaskStatus, role_to_wire
from a2a_runtime.core.ids import validate_blocker_id, validate_task_id
from a2a_runtime.models._coerce import (
    as_dict,
    as_enum,
    as_enum_list,
    as_optional_str,
    as_role,
    as_str,
    as_str_list,
    ensure_schema_version,
    require,
)


@dataclass(frozen=True)
class BlockedContext:
    blocker_id: str
    blocked_from_agent: Role
    blocked_from_status: TaskStatus
    resume_to_agent: Role
    resume_to_status: TaskStatus
    blocking_reason: str
    missing_artifacts: list[str]
    required_fix: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BlockedContext":
        return cls(
            blocker_id=validate_blocker_id(as_str(require(data, "blocker_id"), "blocker_id")),
            blocked_from_agent=as_role(require(data, "blocked_from_agent"), "blocked_from_agent"),
            blocked_from_status=as_enum(
                require(data, "blocked_from_status"),
                TaskStatus,
                "blocked_from_status",
            ),
            resume_to_agent=as_role(require(data, "resume_to_agent"), "resume_to_agent"),
            resume_to_status=as_enum(
                require(data, "resume_to_status"),
                TaskStatus,
                "resume_to_status",
            ),
            blocking_reason=as_str(require(data, "blocking_reason"), "blocking_reason"),
            missing_artifacts=as_str_list(
                require(data, "missing_artifacts"),
                "missing_artifacts",
            ),
            required_fix=as_str(require(data, "required_fix"), "required_fix"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "blocker_id": self.blocker_id,
            "blocked_from_agent": role_to_wire(self.blocked_from_agent),
            "blocked_from_status": self.blocked_from_status.value,
            "resume_to_agent": role_to_wire(self.resume_to_agent),
            "resume_to_status": self.resume_to_status.value,
            "blocking_reason": self.blocking_reason,
            "missing_artifacts": list(self.missing_artifacts),
            "required_fix": self.required_fix,
        }


@dataclass(frozen=True)
class State:
    task_id: str
    current_status: TaskStatus
    previous_status: TaskStatus
    current_agent: Role | None
    next_agent: Role | None
    allowed_next_statuses: list[TaskStatus]
    human_review_status: ReviewStatus
    final_review_status: ReviewStatus
    updated_at: str
    produced_artifacts: list[str] = field(default_factory=list)
    active_blocker: str | None = None
    blockers_history: list[str] = field(default_factory=list)
    blocked_context: BlockedContext | None = None
    schema_version: str = SCHEMA_VERSION

    @classmethod
    def from_frontmatter(cls, data: dict[str, Any]) -> "State":
        ensure_schema_version(data)
        blocked_context_data = data.get("blocked_context")
        return cls(
            task_id=validate_task_id(as_str(require(data, "task_id"), "task_id")),
            current_status=as_enum(require(data, "current_status"), TaskStatus, "current_status"),
            previous_status=as_enum(require(data, "previous_status"), TaskStatus, "previous_status"),
            current_agent=as_role(require(data, "current_agent"), "current_agent", allow_none=True),
            next_agent=as_role(require(data, "next_agent"), "next_agent", allow_none=True),
            allowed_next_statuses=as_enum_list(
                require(data, "allowed_next_statuses"),
                TaskStatus,
                "allowed_next_statuses",
            ),
            human_review_status=as_enum(
                require(data, "human_review_status"),
                ReviewStatus,
                "human_review_status",
            ),
            final_review_status=as_enum(
                require(data, "final_review_status"),
                ReviewStatus,
                "final_review_status",
            ),
            produced_artifacts=as_str_list(data.get("produced_artifacts", []), "produced_artifacts"),
            active_blocker=as_optional_str(data.get("active_blocker"), "active_blocker"),
            blockers_history=as_str_list(data.get("blockers_history", []), "blockers_history"),
            blocked_context=BlockedContext.from_dict(as_dict(blocked_context_data, "blocked_context"))
            if blocked_context_data is not None
            else None,
            updated_at=as_str(require(data, "updated_at"), "updated_at"),
            schema_version=SCHEMA_VERSION,
        )

    def to_frontmatter(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "current_status": self.current_status.value,
            "previous_status": self.previous_status.value,
            "current_agent": role_to_wire(self.current_agent),
            "next_agent": role_to_wire(self.next_agent),
            "allowed_next_statuses": [status.value for status in self.allowed_next_statuses],
            "human_review_status": self.human_review_status.value,
            "final_review_status": self.final_review_status.value,
            "produced_artifacts": list(self.produced_artifacts),
            "active_blocker": self.active_blocker,
            "blockers_history": list(self.blockers_history),
            "blocked_context": self.blocked_context.to_dict() if self.blocked_context else None,
            "updated_at": self.updated_at,
            "schema_version": self.schema_version,
        }
