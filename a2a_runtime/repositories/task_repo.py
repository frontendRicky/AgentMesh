"""Repository for ``task.md`` records."""

from __future__ import annotations

from dataclasses import dataclass

from a2a_runtime.core import frontmatter
from a2a_runtime.core.errors import RepositoryError, SchemaError
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.task import Task


@dataclass(frozen=True)
class TaskRepo:
    paths: A2APaths

    def read(self, task_id: str) -> Task:
        path = self.paths.task_md(task_id)
        if not path.exists():
            raise RepositoryError(f"task.md not found for {task_id}")
        document = frontmatter.load(path)
        task = Task.from_frontmatter(document.data)
        if task.task_id != task_id:
            raise SchemaError("task.md task_id must match workspace directory name")
        return task

    def create(self, task: Task, body: str = "") -> None:
        path = self.paths.task_md(task.task_id)
        if path.parent.name != task.task_id:
            raise SchemaError("workspace task directory must equal task_id")
        if path.exists():
            raise RepositoryError("task.md already exists; task static metadata is immutable")
        frontmatter.write(path, task.to_frontmatter(), body)
