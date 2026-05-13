"""Formal blocker record model."""

from __future__ import annotations

from dataclasses import dataclass

from a2a_runtime.core.constants import SCHEMA_VERSION, Role, TaskStatus, role_to_wire
from a2a_runtime.core.ids import validate_blocker_id, validate_message_id, validate_task_id
from a2a_runtime.core.errors import SchemaError
from a2a_runtime.models._coerce import (
    as_enum,
    as_optional_str,
    as_role,
    as_str,
    as_str_list,
    ensure_schema_version,
    require,
)


@dataclass(frozen=True)
class Blocker:
    blocker_id: str
    task_id: str
    blocked_from_agent: Role
    blocked_from_status: TaskStatus
    resume_to_agent: Role
    resume_to_status: TaskStatus
    blocking_reason: str
    missing_artifacts: list[str]
    required_fix: str
    created_by: str
    source_request_message: str | None
    created_at: str
    schema_version: str = SCHEMA_VERSION

    @classmethod
    def from_frontmatter(cls, data: dict[str, object]) -> "Blocker":
        ensure_schema_version(data)
        created_by = as_str(require(data, "created_by"), "created_by")
        if created_by != Role.CONTROLLER.value:
            raise SchemaError("blocker created_by must be controller")
        source_request_message = as_optional_str(
            require(data, "source_request_message"),
            "source_request_message",
        )
        if source_request_message is not None:
            source_request_message = validate_message_id(source_request_message)
        return cls(
            blocker_id=validate_blocker_id(as_str(require(data, "blocker_id"), "blocker_id")),
            task_id=validate_task_id(as_str(require(data, "task_id"), "task_id")),
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
            created_by=created_by,
            source_request_message=source_request_message,
            created_at=as_str(require(data, "created_at"), "created_at"),
            schema_version=SCHEMA_VERSION,
        )

    def to_frontmatter(self) -> dict[str, object]:
        return {
            "blocker_id": self.blocker_id,
            "task_id": self.task_id,
            "blocked_from_agent": role_to_wire(self.blocked_from_agent),
            "blocked_from_status": self.blocked_from_status.value,
            "resume_to_agent": role_to_wire(self.resume_to_agent),
            "resume_to_status": self.resume_to_status.value,
            "blocking_reason": self.blocking_reason,
            "missing_artifacts": list(self.missing_artifacts),
            "required_fix": self.required_fix,
            "created_by": self.created_by,
            "source_request_message": self.source_request_message,
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }
