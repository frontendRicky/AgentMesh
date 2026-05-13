"""Read-only repository for behavior definitions, rules, flows, and colleague personas."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from a2a_runtime.core.constants import Role
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.agent_profile import normalize_profile_role
from a2a_runtime.repositories.agent_card_repo import ROLE_CARD_FILES


ROLE_AGENT_FILES = {
    Role.PM: "product-manager.agent.md",
    Role.ARCHITECT: "architect.agent.md",
    Role.DEVELOPER: "senior-frontend-developer.agent.md",
    Role.QA: "qa-tester.agent.md",
    Role.CONTROLLER: "flow-controller.agent.md",
}

ROLE_PERSONA_FILES = {
    Role.PM: "planner.md",
    Role.ARCHITECT: "architect.md",
    Role.DEVELOPER: "implementer.md",
    Role.QA: "verifier.md",
    Role.CONTROLLER: "a-to-a-workflow.mdc",
}


@dataclass(frozen=True)
class ReferenceDocument:
    path: Path
    content: str


@dataclass(frozen=True)
class ReferenceRepo:
    paths: A2APaths
    colleague_reference_dir: Path | None = None

    def __post_init__(self) -> None:
        if self.colleague_reference_dir is None:
            object.__setattr__(self, "colleague_reference_dir", self.paths.root / "归档")

    def read_agent_behavior(self, role: Role | str) -> ReferenceDocument | None:
        parsed = normalize_profile_role(role)
        filename = ROLE_AGENT_FILES.get(parsed, f"{parsed.value}.agent.md")
        return self._read_optional(self.paths.ai_agents_dir / "agents" / filename)

    def read_colleague_persona(self, role: Role | str) -> ReferenceDocument | None:
        parsed = normalize_profile_role(role)
        filename = ROLE_PERSONA_FILES.get(parsed)
        if filename is None or self.colleague_reference_dir is None:
            return None
        return self._read_optional(self.colleague_reference_dir / filename)

    def read_cursor_ai_agents_rule(self) -> ReferenceDocument | None:
        return self._read_optional(self.paths.root / ".cursor" / "rules" / "ai-agents.mdc")

    def list_flow_documents(self) -> list[ReferenceDocument]:
        return self._list_markdown_documents(self.paths.ai_agents_dir / "flows")

    def list_rule_documents(self) -> list[ReferenceDocument]:
        return self._list_markdown_documents(self.paths.ai_agents_dir / "rules")

    def list_card_paths(self) -> list[Path]:
        root = self.paths.agent_cards_dir
        if not root.exists():
            return []
        names = set(ROLE_CARD_FILES.values())
        return sorted(path for path in root.glob("*.md") if path.name in names or path.is_file())

    def _list_markdown_documents(self, root: Path) -> list[ReferenceDocument]:
        if not root.exists():
            return []
        documents: list[ReferenceDocument] = []
        for path in sorted(root.glob("*.md")):
            doc = self._read_optional(path)
            if doc is not None:
                documents.append(doc)
        return documents

    def _read_optional(self, path: Path) -> ReferenceDocument | None:
        if not path.exists() or not path.is_file():
            return None
        return ReferenceDocument(path=path, content=path.read_text(encoding="utf-8"))
