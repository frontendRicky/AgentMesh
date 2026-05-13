"""Message model for file-message-bus records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from a2a_runtime.core.constants import SCHEMA_VERSION, MessageType, Role, role_to_wire
from a2a_runtime.core.ids import validate_message_id, validate_task_id
from a2a_runtime.core.errors import SchemaError
from a2a_runtime.models._coerce import (
    as_bool,
    as_dict,
    as_enum,
    as_role,
    as_str,
    as_str_list,
    ensure_schema_version,
    require,
)


@dataclass(frozen=True)
class Message:
    message_id: str
    task_id: str
    from_agent: Role
    to_agent: Role
    message_type: MessageType
    intent: str
    summary: str
    payload: dict[str, Any]
    required_response: bool
    created_at: str
    referenced_artifacts: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION

    @classmethod
    def from_frontmatter(cls, data: dict[str, Any]) -> "Message":
        ensure_schema_version(data)
        payload = as_dict(require(data, "payload"), "payload")
        if not payload:
            raise SchemaError("payload must be non-empty")
        return cls(
            message_id=validate_message_id(as_str(require(data, "message_id"), "message_id")),
            task_id=validate_task_id(as_str(require(data, "task_id"), "task_id")),
            from_agent=as_role(require(data, "from_agent"), "from_agent"),
            to_agent=as_role(require(data, "to_agent"), "to_agent"),
            message_type=as_enum(require(data, "message_type"), MessageType, "message_type"),
            intent=as_str(require(data, "intent"), "intent"),
            summary=as_str(require(data, "summary"), "summary"),
            payload=payload,
            referenced_artifacts=as_str_list(
                data.get("referenced_artifacts", []),
                "referenced_artifacts",
            ),
            required_response=as_bool(require(data, "required_response"), "required_response"),
            blockers=as_str_list(data.get("blockers", []), "blockers"),
            created_at=as_str(require(data, "created_at"), "created_at"),
            schema_version=SCHEMA_VERSION,
        )

    def to_frontmatter(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "task_id": self.task_id,
            "from_agent": role_to_wire(self.from_agent),
            "to_agent": role_to_wire(self.to_agent),
            "message_type": self.message_type.value,
            "intent": self.intent,
            "summary": self.summary,
            "payload": dict(self.payload),
            "referenced_artifacts": list(self.referenced_artifacts),
            "required_response": self.required_response,
            "blockers": list(self.blockers),
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }
