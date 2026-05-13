"""Repository for formal blocker files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from a2a_runtime.core import frontmatter
from a2a_runtime.core.constants import Role
from a2a_runtime.core.errors import GateError, RepositoryError, SchemaError
from a2a_runtime.core.ids import validate_blocker_id, validate_task_id
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.blocker import Blocker
from a2a_runtime.models.state import State

_BLOCKER_SEQ_RE = re.compile(r"^B-T-\d{4}-\d{3}-(\d{3})\.md$")


@dataclass(frozen=True)
class BlockerRepo:
    paths: A2APaths

    def list_blockers(self, task_id: str) -> list[Path]:
        validate_task_id(task_id)
        blockers_dir = self.paths.blockers_dir(task_id)
        if not blockers_dir.exists():
            return []
        return sorted(path for path in blockers_dir.glob("B-*.md") if path.is_file())

    def next_sequence(self, task_id: str) -> int:
        sequences: list[int] = []
        for path in self.list_blockers(task_id):
            match = _BLOCKER_SEQ_RE.fullmatch(path.name)
            if match:
                sequences.append(int(match.group(1)))
                continue
            try:
                blocker = self.read_blocker(path)
            except (RepositoryError, SchemaError):
                continue
            sequences.append(int(blocker.blocker_id.rsplit("-", 1)[1]))
        return max(sequences, default=0) + 1

    def build_blocker_path(self, task_id: str, seq: int) -> Path:
        validate_task_id(task_id)
        blocker_id = validate_blocker_id(f"B-{task_id}-{seq:03d}")
        return self.paths.blockers_dir(task_id) / f"{blocker_id}.md"

    def read_blocker(self, path: Path) -> Blocker:
        if not path.exists():
            raise RepositoryError(f"blocker not found: {path}")
        document = frontmatter.load(path)
        blocker = Blocker.from_frontmatter(document.data)
        if path.name != f"{blocker.blocker_id}.md":
            raise SchemaError("blocker_id must match blocker filename")
        return blocker

    def write_blocker(self, blocker: Blocker, body: str = "") -> Path:
        if blocker.created_by != Role.CONTROLLER.value:
            raise GateError("formal blocker can only be written by controller")
        validate_blocker_id(blocker.blocker_id)
        seq = int(blocker.blocker_id.rsplit("-", 1)[1])
        path = self.build_blocker_path(blocker.task_id, seq)
        frontmatter.write(path, blocker.to_frontmatter(), body)
        return path

    def find_active_blocker(self, task_id: str, state: State) -> Blocker | None:
        if state.active_blocker is None:
            return None
        expected_path = self.paths.blockers_dir(task_id) / f"{state.active_blocker}.md"
        return self.read_blocker(expected_path)
