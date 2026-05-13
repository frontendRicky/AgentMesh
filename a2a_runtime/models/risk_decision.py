"""Human Risk Decision Gate models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from a2a_runtime.core.constants import (
    SCHEMA_VERSION,
    RiskDecisionAction,
    Role,
    TaskStatus,
    role_to_wire,
)
from a2a_runtime.core.ids import validate_risk_decision_id, validate_risk_id, validate_task_id
from a2a_runtime.core.errors import SchemaError
from a2a_runtime.models.review import ROLE_REVIEWER_VALUES
from a2a_runtime.models._coerce import (
    as_bool,
    as_enum,
    as_optional_str,
    as_role,
    as_str,
    ensure_schema_version,
    require,
)


@dataclass(frozen=True)
class RiskOption:
    option_id: str
    label: str
    decision: RiskDecisionAction
    requires_regeneration: bool
    target_agent: Role | None = None
    target_status: TaskStatus | None = None
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RiskOption":
        target_status = data.get("target_status")
        return cls(
            option_id=as_str(require(data, "option_id"), "option_id"),
            label=as_str(require(data, "label"), "label"),
            decision=as_enum(require(data, "decision"), RiskDecisionAction, "decision"),
            target_agent=as_role(data.get("target_agent"), "target_agent", allow_none=True)
            if data.get("target_agent") is not None
            else None,
            target_status=as_enum(target_status, TaskStatus, "target_status")
            if target_status is not None
            else None,
            requires_regeneration=as_bool(
                require(data, "requires_regeneration"),
                "requires_regeneration",
            ),
            description=as_str(data.get("description", ""), "description")
            if data.get("description", "") != ""
            else "",
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "option_id": self.option_id,
            "label": self.label,
            "decision": self.decision.value,
            "target_agent": role_to_wire(self.target_agent) if self.target_agent else None,
            "target_status": self.target_status.value if self.target_status else None,
            "requires_regeneration": self.requires_regeneration,
            "description": self.description,
        }


@dataclass(frozen=True)
class RiskDecision:
    decision_id: str
    risk_id: str
    task_id: str
    decision_by: str
    decision_at: str
    decision: RiskDecisionAction
    selected_option: str
    reason: str
    allowed_next_action: str
    requires_regeneration: bool
    target_agent: Role | None = None
    target_status: TaskStatus | None = None
    generated_cursor_prompt_path: str | None = None
    review_record_path: str | None = None
    local_user: str | None = None
    user_mismatch_warning: bool = False
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        validate_risk_decision_id(self.decision_id)
        validate_risk_id(self.risk_id)
        validate_task_id(self.task_id)
        if f"RD-{self.task_id}-" not in self.decision_id:
            raise SchemaError("decision_id task_id segment must match task_id")
        if f"RISK-{self.task_id}-" not in self.risk_id:
            raise SchemaError("risk_id task_id segment must match task_id")
        if self.decision_by in ROLE_REVIEWER_VALUES:
            raise SchemaError("decision_by must be a real user handle, not an agent role")
        if not self.reason.strip():
            raise SchemaError("reason is required")
        if self.requires_regeneration and self.target_agent is None:
            raise SchemaError("target_agent is required when requires_regeneration is true")
        if (
            self.decision == RiskDecisionAction.SEND_TO_DEVELOPER
            and self.target_status != TaskStatus.DEVELOPER_PROCESSING
        ):
            raise SchemaError("send_to_developer requires target_status == developer_processing")
        if self.decision == RiskDecisionAction.CANCEL_TASK and self.target_status not in {
            None,
            TaskStatus.CANCELLED,
        }:
            raise SchemaError("cancel_task only allows target_status == cancelled")

    @classmethod
    def from_frontmatter(cls, data: dict[str, Any]) -> "RiskDecision":
        ensure_schema_version(data)
        target_status = data.get("target_status")
        return cls(
            decision_id=validate_risk_decision_id(as_str(require(data, "decision_id"), "decision_id")),
            risk_id=validate_risk_id(as_str(require(data, "risk_id"), "risk_id")),
            task_id=validate_task_id(as_str(require(data, "task_id"), "task_id")),
            decision_by=as_str(require(data, "decision_by"), "decision_by"),
            decision_at=as_str(require(data, "decision_at"), "decision_at"),
            decision=as_enum(require(data, "decision"), RiskDecisionAction, "decision"),
            selected_option=as_str(require(data, "selected_option"), "selected_option"),
            reason=as_str(require(data, "reason"), "reason"),
            allowed_next_action=as_str(
                require(data, "allowed_next_action"),
                "allowed_next_action",
            ),
            requires_regeneration=as_bool(
                require(data, "requires_regeneration"),
                "requires_regeneration",
            ),
            target_agent=as_role(data.get("target_agent"), "target_agent", allow_none=True)
            if data.get("target_agent") is not None
            else None,
            target_status=as_enum(target_status, TaskStatus, "target_status")
            if target_status is not None
            else None,
            generated_cursor_prompt_path=as_optional_str(
                data.get("generated_cursor_prompt_path"),
                "generated_cursor_prompt_path",
            ),
            review_record_path=as_optional_str(data.get("review_record_path"), "review_record_path"),
            local_user=as_optional_str(data.get("local_user"), "local_user"),
            user_mismatch_warning=as_bool(data.get("user_mismatch_warning", False), "user_mismatch_warning"),
            schema_version=SCHEMA_VERSION,
        )

    def to_frontmatter(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "risk_id": self.risk_id,
            "task_id": self.task_id,
            "decision_by": self.decision_by,
            "decision_at": self.decision_at,
            "decision": self.decision.value,
            "selected_option": self.selected_option,
            "reason": self.reason,
            "allowed_next_action": self.allowed_next_action,
            "requires_regeneration": self.requires_regeneration,
            "target_agent": role_to_wire(self.target_agent) if self.target_agent else None,
            "target_status": self.target_status.value if self.target_status else None,
            "generated_cursor_prompt_path": self.generated_cursor_prompt_path,
            "review_record_path": self.review_record_path,
            "local_user": self.local_user,
            "user_mismatch_warning": self.user_mismatch_warning,
            "schema_version": self.schema_version,
        }
