"""Read-only repository for A2A agent cards."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from a2a_runtime.core import frontmatter
from a2a_runtime.core.constants import Role
from a2a_runtime.core.errors import RepositoryError
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.agent_card import AgentCard, parse_markdown_sections
from a2a_runtime.models.agent_profile import normalize_profile_role


ROLE_CARD_FILES = {
    Role.PM: "product-manager.card.md",
    Role.ARCHITECT: "architect.card.md",
    Role.DEVELOPER: "senior-frontend-developer.card.md",
    Role.QA: "qa-tester.card.md",
    Role.CONTROLLER: "flow-controller.card.md",
}


@dataclass(frozen=True)
class AgentCardRepo:
    paths: A2APaths

    def build_card_path(self, role: Role | str) -> Path:
        parsed = normalize_profile_role(role)
        filename = ROLE_CARD_FILES.get(parsed, f"{parsed.value}.card.md")
        return self.paths.agent_cards_dir / filename

    def read_agent_card(self, role: Role | str) -> AgentCard:
        path = self.build_card_path(role)
        if not path.exists():
            raise RepositoryError(f"agent card not found: {path}")
        document = frontmatter.load(path)
        return AgentCard.from_frontmatter(
            document.data,
            sections=parse_markdown_sections(document.body),
        )

    def try_read_agent_card(self, role: Role | str) -> tuple[AgentCard | None, Path]:
        path = self.build_card_path(role)
        if not path.exists():
            return None, path
        return self.read_agent_card(role), path
