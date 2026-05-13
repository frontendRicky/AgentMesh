"""Artifact model for content records produced by agents."""

from __future__ import annotations

from dataclasses import dataclass, field

from a2a_runtime.core.constants import (
    SCHEMA_VERSION,
    ArtifactStatus,
    ArtifactType,
    Role,
    ValidationOutcome,
    role_to_wire,
)
from a2a_runtime.core.ids import validate_artifact_id, validate_task_id
from a2a_runtime.models._coerce import (
    as_enum,
    as_int,
    as_optional_str,
    as_role,
    as_role_list,
    as_str,
    as_str_list,
    ensure_schema_version,
    require,
    roles_to_wire,
)


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    task_id: str
    artifact_type: ArtifactType
    produced_by: Role
    consumed_by: list[Role]
    file_path: str
    version: int
    status: ArtifactStatus
    summary: str
    validation_result: ValidationOutcome
    created_at: str
    dependencies: list[str] = field(default_factory=list)
    validation_notes: str | None = None
    schema_version: str = SCHEMA_VERSION

    @classmethod
    def from_frontmatter(cls, data: dict[str, object]) -> "Artifact":
        ensure_schema_version(data)
        return cls(
            artifact_id=validate_artifact_id(as_str(require(data, "artifact_id"), "artifact_id")),
            task_id=validate_task_id(as_str(require(data, "task_id"), "task_id")),
            artifact_type=as_enum(require(data, "artifact_type"), ArtifactType, "artifact_type"),
            produced_by=as_role(require(data, "produced_by"), "produced_by"),
            consumed_by=as_role_list(require(data, "consumed_by"), "consumed_by"),
            file_path=as_str(require(data, "file_path"), "file_path"),
            version=as_int(require(data, "version"), "version"),
            status=as_enum(require(data, "status"), ArtifactStatus, "status"),
            summary=as_str(require(data, "summary"), "summary"),
            dependencies=as_str_list(data.get("dependencies", []), "dependencies"),
            validation_result=as_enum(
                require(data, "validation_result"),
                ValidationOutcome,
                "validation_result",
            ),
            validation_notes=as_optional_str(data.get("validation_notes"), "validation_notes"),
            created_at=as_str(require(data, "created_at"), "created_at"),
            schema_version=SCHEMA_VERSION,
        )

    def to_frontmatter(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "task_id": self.task_id,
            "artifact_type": self.artifact_type.value,
            "produced_by": role_to_wire(self.produced_by),
            "consumed_by": roles_to_wire(self.consumed_by),
            "file_path": self.file_path,
            "version": self.version,
            "status": self.status.value,
            "summary": self.summary,
            "dependencies": list(self.dependencies),
            "validation_result": self.validation_result.value,
            "validation_notes": self.validation_notes,
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }
