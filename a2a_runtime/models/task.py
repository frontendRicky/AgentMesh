"""Task model. ``task.md`` stores static fields only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from a2a_runtime.core.constants import (
    SCHEMA_VERSION,
    TASK_DYNAMIC_FIELDS,
    TaskPriority,
    TaskType,
)
from a2a_runtime.core.ids import validate_task_id
from a2a_runtime.core.errors import SchemaError
from a2a_runtime.models._coerce import (
    as_dict,
    as_enum,
    as_str,
    as_str_list,
    ensure_schema_version,
    require,
)


@dataclass(frozen=True)
class TaskScope:
    in_scope: list[str]
    out_of_scope: list[str]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskScope":
        return cls(
            in_scope=as_str_list(require(data, "in_scope"), "scope.in_scope"),
            out_of_scope=as_str_list(require(data, "out_of_scope"), "scope.out_of_scope"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"in_scope": list(self.in_scope), "out_of_scope": list(self.out_of_scope)}


@dataclass(frozen=True)
class Task:
    task_id: str
    task_type: TaskType
    task_title: str
    created_by: str
    human_owner: str
    priority: TaskPriority
    scope: TaskScope
    constraints: list[str]
    required_artifacts: list[str]
    created_at: str
    initial_input_messages: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION

    @classmethod
    def from_frontmatter(cls, data: dict[str, Any]) -> "Task":
        dynamic_fields = sorted(TASK_DYNAMIC_FIELDS.intersection(data))
        if dynamic_fields:
            raise SchemaError(f"task.md cannot contain dynamic fields: {', '.join(dynamic_fields)}")
        ensure_schema_version(data)
        return cls(
            task_id=validate_task_id(as_str(require(data, "task_id"), "task_id")),
            task_type=as_enum(require(data, "task_type"), TaskType, "task_type"),
            task_title=as_str(require(data, "task_title"), "task_title"),
            created_by=as_str(require(data, "created_by"), "created_by"),
            human_owner=as_str(require(data, "human_owner"), "human_owner"),
            priority=as_enum(require(data, "priority"), TaskPriority, "priority"),
            scope=TaskScope.from_dict(as_dict(require(data, "scope"), "scope")),
            constraints=as_str_list(require(data, "constraints"), "constraints"),
            required_artifacts=as_str_list(
                require(data, "required_artifacts"),
                "required_artifacts",
            ),
            created_at=as_str(require(data, "created_at"), "created_at"),
            initial_input_messages=as_str_list(
                data.get("initial_input_messages", []),
                "initial_input_messages",
            ),
            schema_version=SCHEMA_VERSION,
        )

    def to_frontmatter(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "task_title": self.task_title,
            "created_by": self.created_by,
            "human_owner": self.human_owner,
            "priority": self.priority.value,
            "scope": self.scope.to_dict(),
            "constraints": list(self.constraints),
            "initial_input_messages": list(self.initial_input_messages),
            "required_artifacts": list(self.required_artifacts),
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }
