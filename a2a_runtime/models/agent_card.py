"""Agent card model."""

from __future__ import annotations

from dataclasses import dataclass, field

from a2a_runtime.core.constants import SCHEMA_VERSION, Role, role_to_wire
from a2a_runtime.models._coerce import (
    as_optional_str,
    as_role,
    as_str,
    as_str_list,
    ensure_schema_version,
    require,
)


@dataclass(frozen=True)
class AgentCard:
    agent_id: str
    agent_name: str
    role: Role
    version: str
    description: str = ""
    capabilities: list[str] = field(default_factory=list)
    input_artifacts: list[str] = field(default_factory=list)
    output_artifacts: list[str] = field(default_factory=list)
    readable_paths: list[str] = field(default_factory=list)
    writable_paths: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    upstream_agents: list[str] = field(default_factory=list)
    downstream_agents: list[str] = field(default_factory=list)
    handoff_contracts: list[str] = field(default_factory=list)
    validation_checklist: list[str] = field(default_factory=list)
    stop_conditions: list[str] = field(default_factory=list)
    model: str | None = None
    schema_version: str = SCHEMA_VERSION

    @classmethod
    def from_frontmatter(
        cls,
        data: dict[str, object],
        *,
        sections: dict[str, list[str]] | None = None,
    ) -> "AgentCard":
        ensure_schema_version(data)
        sections = sections or {}
        return cls(
            agent_id=as_str(require(data, "agent_id"), "agent_id"),
            agent_name=as_str(require(data, "agent_name"), "agent_name"),
            role=as_role(require(data, "role"), "role"),
            version=as_str(require(data, "version"), "version"),
            description="\n".join(sections.get("description", [])),
            capabilities=list(sections.get("capabilities", [])),
            input_artifacts=list(sections.get("input_artifacts", [])),
            output_artifacts=list(sections.get("output_artifacts", [])),
            readable_paths=list(sections.get("readable_paths", [])),
            writable_paths=list(sections.get("writable_paths", [])),
            allowed_actions=list(sections.get("allowed_actions", [])),
            forbidden_actions=list(sections.get("forbidden_actions", [])),
            upstream_agents=list(sections.get("upstream_agents", [])),
            downstream_agents=list(sections.get("downstream_agents", [])),
            handoff_contracts=list(sections.get("handoff_contracts", [])),
            validation_checklist=list(sections.get("validation_checklist", [])),
            stop_conditions=list(sections.get("stop_conditions", [])),
            model=_parse_optional_model(data.get("model")),
            schema_version=SCHEMA_VERSION,
        )

    def to_frontmatter(self) -> dict[str, str]:
        payload: dict[str, str] = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "role": role_to_wire(self.role),
            "version": self.version,
            "schema_version": self.schema_version,
        }
        if self.model:
            payload["model"] = self.model
        return payload


def _parse_optional_model(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return as_optional_str(value, "model")
    trimmed = value.strip()
    return trimmed or None


def parse_markdown_sections(body: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current = line.removeprefix("## ").strip()
            sections[current] = []
        elif current is not None and line:
            sections[current].append(line.removeprefix("- ").strip())
    return sections
