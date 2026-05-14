"""Read-only repository for A2A agent cards."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from a2a_runtime.core import frontmatter
from a2a_runtime.core.constants import Role
from a2a_runtime.core.errors import FrontmatterError, RepositoryError, SchemaError
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.agent_card import AgentCard, parse_markdown_sections
from a2a_runtime.models.agent_profile import normalize_profile_role
from a2a_runtime.models.model_policy import normalize_model_policy_role


ROLE_CARD_FILES = {
    Role.PM: "product-manager.card.md",
    Role.ARCHITECT: "architect.card.md",
    Role.DEVELOPER: "senior-frontend-developer.card.md",
    Role.QA: "qa-tester.card.md",
    Role.CONTROLLER: "flow-controller.card.md",
}

MODEL_OVERRIDES_FILENAME = "model-overrides.md"

_CHECKLIST_PATTERN = re.compile(r"^\s*-\s*\[\s*([xX ])\s*\]\s*(.+?)\s*$")
_HEADING_PATTERN = re.compile(r"^\s*##\s+(.+?)\s*$")


def _extract_slug(rest: str) -> str | None:
    """Extract the model slug from the text after `- [x] `.

    Strips trailing markdown comments / inline notes (anything after the first
    whitespace-separated token, or after ` # `, or after ` <space>--` ).
    Backticks around the slug are stripped.
    """

    text = rest.strip()
    if not text:
        return None
    comment_index = text.find(" #")
    if comment_index >= 0:
        text = text[:comment_index].strip()
    dash_index = text.find(" --")
    if dash_index >= 0:
        text = text[:dash_index].strip()
    if not text:
        return None
    token = text.split()[0]
    return token.strip("`").strip() or None


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

    @property
    def model_overrides_path(self) -> Path:
        return self.paths.agent_cards_dir / MODEL_OVERRIDES_FILENAME

    def read_model_overrides(self) -> tuple[dict[str, str], list[str]]:
        """Read the optional `.ai-agents/agent-cards/model-overrides.md` file.

        Resolution order inside the file:
          1. Body checklist: `## <role>` sections with `- [x] <slug>` lines.
             Exactly one `[x]` per role section is selected; multiple `[x]` →
             warning, take first.
          2. Frontmatter `overrides:` mapping (legacy / fallback). Only used
             for roles that the body checklist did not select.

        Returns (overrides, warnings). Missing file → empty mapping. Malformed
        entries become warnings instead of hard errors so a broken override
        file never crashes prompt generation.
        """

        path = self.model_overrides_path
        warnings: list[str] = []
        if not path.exists():
            return {}, warnings
        try:
            document = frontmatter.load(path)
        except FrontmatterError as exc:
            warnings.append(f"model-overrides.md ignored: {exc}")
            return {}, warnings

        body_overrides, body_warnings = self._parse_checklist_body(document.body)
        warnings.extend(body_warnings)

        frontmatter_overrides, fm_warnings = self._parse_frontmatter_overrides(document.data)
        warnings.extend(fm_warnings)

        merged: dict[str, str] = {}
        merged.update(frontmatter_overrides)
        merged.update(body_overrides)
        return merged, warnings

    def _parse_checklist_body(self, body: str) -> tuple[dict[str, str], list[str]]:
        warnings: list[str] = []
        selections: dict[str, list[str]] = {}
        current_role: str | None = None

        for raw_line in body.splitlines():
            heading_match = _HEADING_PATTERN.match(raw_line)
            if heading_match:
                heading = heading_match.group(1).strip().lower()
                try:
                    current_role = normalize_model_policy_role(heading)
                except SchemaError:
                    current_role = None
                continue
            if current_role is None:
                continue
            checklist_match = _CHECKLIST_PATTERN.match(raw_line)
            if not checklist_match:
                continue
            mark, rest = checklist_match.group(1), checklist_match.group(2)
            if mark.lower() != "x":
                continue
            slug = _extract_slug(rest)
            if not slug:
                continue
            selections.setdefault(current_role, []).append(slug)

        result: dict[str, str] = {}
        for role_key, slugs in selections.items():
            if len(slugs) > 1:
                warnings.append(
                    f"model-overrides.md role `{role_key}` selected multiple models {slugs}; using first: {slugs[0]}",
                )
            result[role_key] = slugs[0]
        return result, warnings

    def _parse_frontmatter_overrides(
        self,
        data: dict[str, object],
    ) -> tuple[dict[str, str], list[str]]:
        warnings: list[str] = []
        raw = data.get("overrides")
        if raw is None:
            return {}, warnings
        if not isinstance(raw, dict):
            warnings.append("model-overrides.md `overrides` frontmatter must be a mapping; ignored")
            return {}, warnings

        result: dict[str, str] = {}
        for key, value in raw.items():
            try:
                role_key = normalize_model_policy_role(str(key))
            except SchemaError as exc:
                warnings.append(f"model-overrides.md role `{key}` ignored: {exc}")
                continue
            if value is None:
                continue
            if not isinstance(value, str):
                warnings.append(f"model-overrides.md `{role_key}` must be a string; ignored")
                continue
            trimmed = value.strip()
            if not trimmed:
                continue
            result[role_key] = trimmed
        return result, warnings
