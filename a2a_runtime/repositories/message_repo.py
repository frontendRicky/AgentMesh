"""Repository for task-scoped message bus files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from a2a_runtime.core import frontmatter
from a2a_runtime.core.constants import Role, normalize_role, role_to_wire
from a2a_runtime.core.errors import RepositoryError, SchemaError
from a2a_runtime.core.ids import validate_message_id, validate_task_id
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.message import Message

_MESSAGE_SEQ_RE = re.compile(r"from-[a-z-]+-(\d{3})-")


@dataclass(frozen=True)
class MessageRepo:
    paths: A2APaths

    def list_messages(self, task_id: str) -> list[Path]:
        validate_task_id(task_id)
        messages_dir = self.paths.messages_dir(task_id)
        if not messages_dir.exists():
            return []
        return sorted(path for path in messages_dir.glob("*.md") if path.is_file())

    def next_sequence(self, task_id: str) -> int:
        sequences: list[int] = []
        for path in self.list_messages(task_id):
            match = _MESSAGE_SEQ_RE.search(path.name)
            if match:
                sequences.append(int(match.group(1)))
                continue
            try:
                message = self.read_message(path)
            except (RepositoryError, SchemaError):
                continue
            sequences.append(int(message.message_id.rsplit("-", 1)[1]))
        return max(sequences, default=0) + 1

    def build_message_path(
        self,
        task_id: str,
        from_agent: Role | str,
        seq: int,
        intent: str,
    ) -> Path:
        validate_task_id(task_id)
        role = normalize_role(from_agent, field_name="from_agent")
        if role is None:
            raise SchemaError("from_agent cannot be none")
        safe_intent = intent.strip().replace("_", "-")
        if not safe_intent:
            raise SchemaError("intent cannot be empty")
        filename = f"from-{role_to_wire(role)}-{seq:03d}-{safe_intent}.md"
        return self.paths.messages_dir(task_id) / filename

    def read_message(self, path: Path) -> Message:
        if not path.exists():
            raise RepositoryError(f"message not found: {path}")
        document = frontmatter.load(path)
        message = Message.from_frontmatter(document.data)
        expected_prefix = f"from-{role_to_wire(message.from_agent)}-"
        if not path.name.startswith(expected_prefix):
            raise SchemaError("message from_agent must match file name")
        return message

    def write_message(self, message: Message, body: str = "") -> Path:
        validate_message_id(message.message_id)
        seq = int(message.message_id.rsplit("-", 1)[1])
        path = self.build_message_path(message.task_id, message.from_agent, seq, message.intent)
        frontmatter.write(path, message.to_frontmatter(), body)
        return path
