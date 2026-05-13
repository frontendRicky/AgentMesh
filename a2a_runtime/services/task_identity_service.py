"""Task identity resolution using the A2A four-step priority order."""

from __future__ import annotations

from dataclasses import dataclass, field

from a2a_runtime.core.errors import SchemaError, TaskIdentityAmbiguousError, TaskIdentityError
from a2a_runtime.repositories.workspace_repo import WorkspaceRepo
from a2a_runtime.services.validation_service import ValidationService


@dataclass(frozen=True)
class TaskIdentityService:
    workspace_repo: WorkspaceRepo
    validation_service: ValidationService = field(default_factory=ValidationService)

    def resolve_task_id(self, explicit_task_id: str | None = None) -> str:
        if explicit_task_id:
            return self._ensure_usable_task_id(explicit_task_id)

        active_task_id = self.workspace_repo.read_active_task_id()
        if active_task_id:
            return self._ensure_usable_task_id(active_task_id)

        task_ids = self.workspace_repo.list_task_ids()
        if len(task_ids) == 1:
            return self._ensure_usable_task_id(task_ids[0])
        if not task_ids:
            raise TaskIdentityError("no A2A task found")
        raise TaskIdentityAmbiguousError(
            "multiple A2A tasks found and active_task_id is null; ask the user to choose",
        )

    def _ensure_usable_task_id(self, task_id: str) -> str:
        try:
            task_dir = self.workspace_repo.task_dir(task_id)
        except SchemaError as exc:
            raise TaskIdentityError(str(exc)) from exc
        result = self.validation_service.validate_workspace_task_dir(task_id, task_dir)
        if not result.ok:
            raise TaskIdentityError("; ".join(result.errors))
        return task_id
