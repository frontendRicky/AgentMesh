"""Path helpers for the frozen file-based A2A workspace layout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from a2a_runtime.core.ids import validate_task_id


@dataclass(frozen=True)
class A2APaths:
    root: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root).expanduser().resolve())

    @classmethod
    def discover(cls, start: Path | str | None = None) -> "A2APaths":
        current = Path(start or ".").expanduser().resolve()
        candidates = [current, *current.parents]
        for candidate in candidates:
            if (candidate / ".ai-agents").is_dir():
                return cls(candidate)
        return cls(current)

    @property
    def ai_agents_dir(self) -> Path:
        return self.root / ".ai-agents"

    @property
    def workspace_dir(self) -> Path:
        return self.ai_agents_dir / "workspace"

    @property
    def active_task_path(self) -> Path:
        return self.workspace_dir / "active-task.md"

    @property
    def agent_cards_dir(self) -> Path:
        return self.ai_agents_dir / "agent-cards"

    @property
    def handoffs_dir(self) -> Path:
        return self.ai_agents_dir / "handoffs"

    @property
    def templates_dir(self) -> Path:
        return self.ai_agents_dir / "templates"

    def task_dir(self, task_id: str) -> Path:
        validate_task_id(task_id)
        return self.workspace_dir / task_id

    def task_md(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "task.md"

    def state_md(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "state.md"

    def messages_dir(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "messages"

    def artifacts_dir(self, task_id: str, role: str | None = None) -> Path:
        base = self.task_dir(task_id) / "artifacts"
        return base / role if role else base

    def blockers_dir(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "blockers"

    def human_reviews_dir(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "human-reviews"

    def archive_dir(self, task_id: str) -> Path:
        return self.task_dir(task_id) / "archive"
