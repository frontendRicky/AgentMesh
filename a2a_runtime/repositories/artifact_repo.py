"""Repository for task-scoped artifact files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from a2a_runtime.core import frontmatter
from a2a_runtime.core.constants import ArtifactType, Role, normalize_role, parse_enum
from a2a_runtime.core.errors import RepositoryError, SchemaError
from a2a_runtime.core.ids import validate_artifact_id, validate_task_id
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.artifact import Artifact


@dataclass(frozen=True)
class ArtifactRepo:
    paths: A2APaths

    def list_artifacts(self, task_id: str, role: Role | str | None = None) -> list[Path]:
        validate_task_id(task_id)
        if role is None:
            root = self.paths.artifacts_dir(task_id)
        else:
            normalized = normalize_role(role, field_name="role")
            if normalized is None:
                raise SchemaError("role cannot be none")
            root = self.paths.artifacts_dir(task_id, normalized.value)
        if not root.exists():
            return []
        return sorted(path for path in root.rglob("*.md") if path.is_file())

    def find_artifact(self, task_id: str, artifact_type: ArtifactType | str) -> Artifact | None:
        target = parse_enum(ArtifactType, artifact_type, "artifact_type")
        for path in self.list_artifacts(task_id):
            try:
                artifact = self.read_artifact(path)
            except (RepositoryError, SchemaError):
                continue
            if artifact.artifact_type == target:
                return artifact
        return None

    def read_artifact(self, path: Path) -> Artifact:
        if not path.exists():
            raise RepositoryError(f"artifact not found: {path}")
        document = frontmatter.load(path)
        artifact = Artifact.from_frontmatter(document.data)
        validate_artifact_id(artifact.artifact_id)
        return artifact

    def write_artifact(self, artifact: Artifact, body: str = "") -> Path:
        validate_artifact_id(artifact.artifact_id)
        path = self.paths.task_dir(artifact.task_id) / artifact.file_path
        frontmatter.write(path, artifact.to_frontmatter(), body)
        return path
