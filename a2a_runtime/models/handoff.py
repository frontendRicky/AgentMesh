"""Handoff contract model."""

from __future__ import annotations

from dataclasses import dataclass, field

from a2a_runtime.core.constants import SCHEMA_VERSION, Role, role_to_wire
from a2a_runtime.core.ids import validate_handoff_contract_id
from a2a_runtime.models._coerce import as_role, as_str, ensure_schema_version, require


@dataclass(frozen=True)
class HandoffContract:
    contract_id: str
    from_agent: Role
    to_agent: Role
    required_input_artifacts: list[str] = field(default_factory=list)
    required_output_artifacts: list[str] = field(default_factory=list)
    required_input_messages: list[str] = field(default_factory=list)
    required_output_messages: list[str] = field(default_factory=list)
    required_input_review_records: list[str] = field(default_factory=list)
    required_output_review_records: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    validation_questions: list[str] = field(default_factory=list)
    allowed_next_actions: list[str] = field(default_factory=list)
    forbidden_next_actions: list[str] = field(default_factory=list)
    blocker_conditions: list[str] = field(default_factory=list)
    flow_variants: list[str] = field(default_factory=list)
    schema_version: str = SCHEMA_VERSION

    @classmethod
    def from_frontmatter(
        cls,
        data: dict[str, object],
        *,
        sections: dict[str, list[str]] | None = None,
    ) -> "HandoffContract":
        ensure_schema_version(data)
        sections = sections or {}
        return cls(
            contract_id=validate_handoff_contract_id(
                as_str(require(data, "contract_id"), "contract_id")
            ),
            from_agent=as_role(require(data, "from_agent"), "from_agent"),
            to_agent=as_role(require(data, "to_agent"), "to_agent"),
            required_input_artifacts=list(sections.get("required_input_artifacts", [])),
            required_output_artifacts=list(sections.get("required_output_artifacts", [])),
            required_input_messages=list(sections.get("required_input_messages", [])),
            required_output_messages=list(sections.get("required_output_messages", [])),
            required_input_review_records=list(sections.get("required_input_review_records", [])),
            required_output_review_records=list(sections.get("required_output_review_records", [])),
            acceptance_criteria=list(sections.get("acceptance_criteria", [])),
            validation_questions=list(sections.get("validation_questions", [])),
            allowed_next_actions=list(sections.get("allowed_next_actions", [])),
            forbidden_next_actions=list(sections.get("forbidden_next_actions", [])),
            blocker_conditions=list(sections.get("blocker_conditions", [])),
            flow_variants=list(sections.get("flow_variants", [])),
            schema_version=SCHEMA_VERSION,
        )

    def to_frontmatter(self) -> dict[str, str]:
        return {
            "contract_id": self.contract_id,
            "from_agent": role_to_wire(self.from_agent),
            "to_agent": role_to_wire(self.to_agent),
            "schema_version": self.schema_version,
        }
