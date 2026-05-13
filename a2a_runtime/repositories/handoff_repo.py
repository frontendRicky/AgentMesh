"""Read-only repository for A2A handoff contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from a2a_runtime.core import frontmatter
from a2a_runtime.core.constants import Role
from a2a_runtime.core.errors import RepositoryError, SchemaError
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.agent_card import parse_markdown_sections
from a2a_runtime.models.agent_profile import normalize_profile_role
from a2a_runtime.models.handoff import HandoffContract


@dataclass(frozen=True)
class HandoffRepo:
    paths: A2APaths

    def list_handoff_paths(self) -> list[Path]:
        root = self.paths.handoffs_dir
        if not root.exists():
            return []
        return sorted(path for path in root.glob("*.md") if path.is_file())

    def read_handoff(self, path: Path) -> HandoffContract:
        if not path.exists():
            raise RepositoryError(f"handoff not found: {path}")
        document = frontmatter.load(path)
        return HandoffContract.from_frontmatter(
            document.data,
            sections=parse_markdown_sections(document.body),
        )

    def list_handoffs(self, role: Role | str | None = None) -> list[HandoffContract]:
        parsed = normalize_profile_role(role) if role is not None else None
        contracts: list[HandoffContract] = []
        for path in self.list_handoff_paths():
            try:
                contract = self.read_handoff(path)
            except (RepositoryError, SchemaError):
                continue
            if parsed is None or contract.from_agent == parsed or contract.to_agent == parsed:
                contracts.append(contract)
        return contracts
