"""Workspace-level repository helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from a2a_runtime.core import frontmatter
from a2a_runtime.core.clock import Clock
from a2a_runtime.core.constants import SCHEMA_VERSION
from a2a_runtime.core.ids import is_task_id, validate_task_id
from a2a_runtime.core.paths import A2APaths


@dataclass(frozen=True)
class WorkspaceRepo:
    paths: A2APaths

    @classmethod
    def from_root(cls, root: Path | str) -> "WorkspaceRepo":
        return cls(A2APaths(Path(root)))

    def read_active_task_id(self) -> str | None:
        path = self.paths.active_task_path
        if not path.exists():
            return None
        document = frontmatter.load(path)
        active_task_id = document.data.get("active_task_id")
        if active_task_id is None or active_task_id == "null":
            return None
        return validate_task_id(str(active_task_id))

    def list_task_ids(self) -> list[str]:
        workspace = self.paths.workspace_dir
        if not workspace.exists():
            return []
        task_ids: list[str] = []
        for path in workspace.iterdir():
            if path.is_dir() and is_task_id(path.name):
                task_ids.append(path.name)
        return sorted(task_ids)

    def task_dir(self, task_id: str) -> Path:
        validate_task_id(task_id)
        return self.paths.task_dir(task_id)

    def task_exists(self, task_id: str) -> bool:
        return self.task_dir(task_id).is_dir()

    def write_active_task_id(self, task_id: str, *, clock: Clock | None = None) -> None:
        validate_task_id(task_id)
        previous = self.read_active_task_id()
        now = (clock or Clock()).now_iso()
        path = self.paths.active_task_path
        body = self._active_task_body(task_id, previous, now)
        frontmatter.write(
            path,
            {
                "active_task_id": task_id,
                "last_switched_at": now,
                "schema_version": SCHEMA_VERSION,
            },
            body,
        )

    def _active_task_body(self, task_id: str, previous: str | None, switched_at: str) -> str:
        previous_text = previous or "null"
        return f"""# Active Task

## Current

`active_task_id`: {task_id}

## Runtime Switch History

| time | previous | current | operation |
|---|---|---|---|
| {switched_at} | {previous_text} | {task_id} | task use |
"""
