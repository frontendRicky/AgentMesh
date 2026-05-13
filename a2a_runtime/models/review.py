"""Human review record model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from a2a_runtime.core.constants import (
    SCHEMA_VERSION,
    ReviewIssueSeverity,
    ReviewType,
    ReviewVerdict,
)
from a2a_runtime.core.ids import validate_review_id, validate_task_id
from a2a_runtime.core.errors import SchemaError
from a2a_runtime.models._coerce import (
    as_bool,
    as_dict,
    as_enum,
    as_optional_str,
    as_str,
    as_str_list,
    ensure_schema_version,
    require,
)

ROLE_REVIEWER_VALUES = {"controller", "pm", "architect", "developer", "dev", "qa", "human"}


@dataclass(frozen=True)
class ReviewIssue:
    severity: ReviewIssueSeverity
    description: str
    affected_artifact: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReviewIssue":
        return cls(
            severity=as_enum(require(data, "severity"), ReviewIssueSeverity, "issues[].severity"),
            description=as_str(require(data, "description"), "issues[].description"),
            affected_artifact=as_str(require(data, "affected_artifact"), "issues[].affected_artifact"),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "severity": self.severity.value,
            "description": self.description,
            "affected_artifact": self.affected_artifact,
        }


@dataclass(frozen=True)
class ReviewRecord:
    review_id: str
    task_id: str
    review_type: ReviewType
    reviewed_artifacts: list[str]
    reviewer: str
    reviewed_at: str
    verdict: ReviewVerdict
    followup_required: bool
    issues: list[ReviewIssue] = field(default_factory=list)
    notes: str | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not str(self.reviewer).strip():
            raise SchemaError("reviewer must be a real user handle, not empty")
        if str(self.reviewer) in ROLE_REVIEWER_VALUES:
            raise SchemaError("reviewer must be a real user handle, not an agent role")

    @classmethod
    def from_frontmatter(cls, data: dict[str, Any]) -> "ReviewRecord":
        ensure_schema_version(data)
        reviewer = as_str(require(data, "reviewer"), "reviewer")
        verdict = as_enum(require(data, "verdict"), ReviewVerdict, "verdict")
        issues = [
            ReviewIssue.from_dict(as_dict(item, "issues[]"))
            for item in data.get("issues", [])
        ]
        if verdict in {ReviewVerdict.REJECTED, ReviewVerdict.NEEDS_CHANGES} and not issues:
            raise SchemaError("rejected or needs_changes review must include issues")
        return cls(
            review_id=validate_review_id(as_str(require(data, "review_id"), "review_id")),
            task_id=validate_task_id(as_str(require(data, "task_id"), "task_id")),
            review_type=as_enum(require(data, "review_type"), ReviewType, "review_type"),
            reviewed_artifacts=as_str_list(
                require(data, "reviewed_artifacts"),
                "reviewed_artifacts",
            ),
            reviewer=reviewer,
            reviewed_at=as_str(require(data, "reviewed_at"), "reviewed_at"),
            verdict=verdict,
            issues=issues,
            followup_required=as_bool(require(data, "followup_required"), "followup_required"),
            notes=as_optional_str(data.get("notes"), "notes"),
            schema_version=SCHEMA_VERSION,
        )

    def to_frontmatter(self) -> dict[str, object]:
        return {
            "review_id": self.review_id,
            "task_id": self.task_id,
            "review_type": self.review_type.value,
            "reviewed_artifacts": list(self.reviewed_artifacts),
            "reviewer": self.reviewer,
            "reviewed_at": self.reviewed_at,
            "verdict": self.verdict.value,
            "issues": [issue.to_dict() for issue in self.issues],
            "followup_required": self.followup_required,
            "notes": self.notes,
            "schema_version": self.schema_version,
        }
