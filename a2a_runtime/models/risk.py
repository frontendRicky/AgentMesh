"""Runtime-internal risk finding model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from a2a_runtime.core.constants import (
    SCHEMA_VERSION,
    RiskCategory,
    RiskSeverity,
    RiskStatus,
    Role,
    role_to_wire,
)
from a2a_runtime.core.ids import validate_risk_id, validate_task_id
from a2a_runtime.core.errors import SchemaError
from a2a_runtime.models._coerce import (
    as_bool,
    as_enum,
    as_optional_str,
    as_role,
    as_str,
    as_str_list,
    ensure_schema_version,
    require,
)


@dataclass(frozen=True)
class RuntimeRiskFinding:
    risk_id: str
    task_id: str
    source_agent: Role
    category: RiskCategory
    severity: RiskSeverity
    title: str
    description: str
    evidence: str
    detected_at: str
    requires_human_decision: bool
    status: RiskStatus = RiskStatus.OPEN
    source_file: str | None = None
    source_artifact: str | None = None
    affected_files: list[str] = field(default_factory=list)
    affected_artifacts: list[str] = field(default_factory=list)
    recommended_options: list[str] = field(default_factory=list)
    default_recommendation: str | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        validate_risk_id(self.risk_id)
        validate_task_id(self.task_id)
        if f"RISK-{self.task_id}-" not in self.risk_id:
            raise SchemaError("risk_id task_id segment must match task_id")
        if self.severity in {RiskSeverity.P0_BLOCKER, RiskSeverity.P1_HIGH}:
            if not self.requires_human_decision:
                raise SchemaError("P0/P1 risk must require human decision")
            if self.status not in {
                RiskStatus.WAITING_HUMAN_DECISION,
                RiskStatus.PENDING_MANUAL_REVIEW,
                RiskStatus.ACCEPTED,
                RiskStatus.REJECTED,
                RiskStatus.CONVERTED_TO_BLOCKER,
                RiskStatus.SENT_TO_REPLAN,
                RiskStatus.RESOLVED,
                RiskStatus.DISMISSED,
            }:
                raise SchemaError("P0/P1 risk must start waiting for human decision")
        if self.requires_human_decision and not self.recommended_options:
            raise SchemaError("recommended_options cannot be empty when human decision is required")

    @classmethod
    def from_frontmatter(cls, data: dict[str, Any]) -> "RuntimeRiskFinding":
        ensure_schema_version(data)
        return cls(
            risk_id=validate_risk_id(as_str(require(data, "risk_id"), "risk_id")),
            task_id=validate_task_id(as_str(require(data, "task_id"), "task_id")),
            source_agent=as_role(require(data, "source_agent"), "source_agent"),
            source_file=as_optional_str(data.get("source_file"), "source_file"),
            source_artifact=as_optional_str(data.get("source_artifact"), "source_artifact"),
            category=as_enum(require(data, "category"), RiskCategory, "category"),
            severity=as_enum(require(data, "severity"), RiskSeverity, "severity"),
            title=as_str(require(data, "title"), "title"),
            description=as_str(require(data, "description"), "description"),
            evidence=as_str(require(data, "evidence"), "evidence"),
            affected_files=as_str_list(data.get("affected_files", []), "affected_files"),
            affected_artifacts=as_str_list(
                data.get("affected_artifacts", []),
                "affected_artifacts",
            ),
            detected_at=as_str(require(data, "detected_at"), "detected_at"),
            requires_human_decision=as_bool(
                require(data, "requires_human_decision"),
                "requires_human_decision",
            ),
            recommended_options=as_str_list(
                data.get("recommended_options", []),
                "recommended_options",
            ),
            default_recommendation=as_optional_str(
                data.get("default_recommendation"),
                "default_recommendation",
            ),
            status=as_enum(data.get("status", RiskStatus.OPEN.value), RiskStatus, "status"),
            schema_version=SCHEMA_VERSION,
        )

    def to_frontmatter(self) -> dict[str, object]:
        return {
            "risk_id": self.risk_id,
            "task_id": self.task_id,
            "source_agent": role_to_wire(self.source_agent),
            "source_file": self.source_file,
            "source_artifact": self.source_artifact,
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "affected_files": list(self.affected_files),
            "affected_artifacts": list(self.affected_artifacts),
            "detected_at": self.detected_at,
            "requires_human_decision": self.requires_human_decision,
            "recommended_options": list(self.recommended_options),
            "default_recommendation": self.default_recommendation,
            "status": self.status.value,
            "schema_version": self.schema_version,
        }
