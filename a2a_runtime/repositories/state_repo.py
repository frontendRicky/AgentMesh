"""Repository for ``state.md`` records."""

from __future__ import annotations

from dataclasses import dataclass, field
from dataclasses import replace
from typing import Any

from a2a_runtime.core import frontmatter
from a2a_runtime.core.clock import Clock
from a2a_runtime.core.constants import Role, normalize_role
from a2a_runtime.core.errors import GateError, RepositoryError, SchemaError
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.state import State


@dataclass(frozen=True)
class StateRepo:
    paths: A2APaths
    clock: Clock = field(default_factory=Clock)

    history_archive_threshold: int = 50

    def read(self, task_id: str) -> State:
        state, _ = self.read_with_body(task_id)
        return state

    def read_with_body(self, task_id: str) -> tuple[State, str]:
        path = self.paths.state_md(task_id)
        if not path.exists():
            raise RepositoryError(f"state.md not found for {task_id}")
        document = frontmatter.load(path)
        state = State.from_frontmatter(document.data)
        if state.task_id != task_id:
            raise SchemaError("state.md task_id must match workspace directory name")
        return state, document.body

    def write(self, task_id: str, state: State, *, actor: Role | str, body: str = "") -> None:
        writer = normalize_role(actor, field_name="actor")
        if writer != Role.CONTROLLER:
            raise GateError("state.md is the only dynamic state source and only controller may write it")
        if state.task_id != task_id:
            raise SchemaError("state.task_id must match write task_id")
        path = self.paths.state_md(task_id)
        frontmatter.write(path, state.to_frontmatter(), body)

    def write_with_history(
        self,
        task_id: str,
        state: State,
        history_entry: dict[str, Any],
        *,
        actor: Role | str = Role.CONTROLLER,
        body: str | None = None,
    ) -> None:
        if body is None:
            _, body = self.read_with_body(task_id)
        next_body = self.append_write_history(body, history_entry)
        archived_body = self._archive_write_history_if_needed(task_id, next_body)
        next_state = self._archive_blockers_history_if_needed(task_id, state)
        self.write(task_id, next_state, actor=actor, body=archived_body)

    def append_write_history(self, body: str, entry: dict[str, Any]) -> str:
        line = (
            f"| {entry.get('at', '')} | {entry.get('previous_status', '')} | "
            f"{entry.get('current_status', '')} | {entry.get('actor', '')} | "
            f"{entry.get('reason', '')} |"
        )
        stripped = body.rstrip()
        if "## Runtime Write History" not in stripped:
            section = "\n".join(
                [
                    "## Runtime Write History",
                    "",
                    "| at | previous_status | current_status | actor | reason |",
                    "|---|---|---|---|---|",
                    line,
                ],
            )
            return f"{stripped}\n\n{section}\n" if stripped else f"{section}\n"
        return f"{stripped}\n{line}\n"

    def count_runtime_write_history(self, body: str) -> int:
        if "## Runtime Write History" not in body:
            return 0
        in_section = False
        count = 0
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if line == "## Runtime Write History":
                in_section = True
                continue
            if in_section and line.startswith("## "):
                break
            if in_section and line.startswith("|") and not line.startswith("|---") and " at " not in line:
                count += 1
        return count

    def should_archive_history(self, body: str) -> bool:
        return self.count_runtime_write_history(body) > self.history_archive_threshold

    def archive_history_suggestion(self, task_id: str, body: str) -> str | None:
        if not self.should_archive_history(body):
            return None
        archive_path = self.paths.archive_dir(task_id) / "state-history-next.md"
        return (
            f"Runtime write history exceeds {self.history_archive_threshold} entries; "
            f"next phase should roll older entries into {archive_path}"
        )

    def _archive_write_history_if_needed(self, task_id: str, body: str) -> str:
        count = self.count_runtime_write_history(body)
        has_archive = any(self.paths.archive_dir(task_id).glob("state-history-*.md"))
        if count <= self.history_archive_threshold and not (has_archive and count > 20):
            return body
        lines = body.splitlines()
        start = next((index for index, line in enumerate(lines) if line.strip() == "## Runtime Write History"), None)
        if start is None:
            return body
        end = len(lines)
        for index in range(start + 1, len(lines)):
            if lines[index].startswith("## "):
                end = index
                break
        section = lines[start:end]
        history_lines = [
            line
            for line in section
            if line.strip().startswith("|")
            and not line.strip().startswith("|---")
            and " at " not in line
        ]
        if len(history_lines) <= self.history_archive_threshold and not (has_archive and len(history_lines) > 20):
            return body
        archive_lines = history_lines[:-20]
        keep_lines = history_lines[-20:]
        archive_path = self._archive_path(task_id, "state-history")
        archive_path.write_text(
            "\n".join(
                [
                    "# Archived Runtime Write History",
                    "",
                    "| at | previous_status | current_status | actor | reason |",
                    "|---|---|---|---|---|",
                    *archive_lines,
                    "",
                ],
            ),
            encoding="utf-8",
        )
        new_section = [
            "## Runtime Write History",
            "",
            "| at | previous_status | current_status | actor | reason |",
            "|---|---|---|---|---|",
            *keep_lines,
        ]
        return "\n".join([*lines[:start], *new_section, *lines[end:]]).rstrip() + "\n"

    def _archive_blockers_history_if_needed(self, task_id: str, state: State) -> State:
        if len(state.blockers_history) <= self.history_archive_threshold:
            return state
        archived = state.blockers_history[:-50]
        if archived:
            archive_path = self._archive_path(task_id, "blockers-history")
            archive_path.write_text(
                "\n".join(["# Archived Blockers History", "", *[f"- {item}" for item in archived], ""]),
                encoding="utf-8",
            )
        return replace(state, blockers_history=state.blockers_history[-50:])

    def _archive_path(self, task_id: str, prefix: str):
        archive_dir = self.paths.archive_dir(task_id)
        archive_dir.mkdir(parents=True, exist_ok=True)
        stamp = self.clock.now().strftime("%Y%m%dT%H%M%S%fZ")
        return archive_dir / f"{prefix}-{stamp}.md"
