"""Merged runtime profile for prompt generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from a2a_runtime.core.constants import Role, normalize_role, role_to_wire


@dataclass(frozen=True)
class ProfileConflict:
    field_name: str
    high_priority_source: str
    low_priority_source: str
    high_priority_value: str
    low_priority_value: str
    needs_human_decision: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "field_name": self.field_name,
            "high_priority_source": self.high_priority_source,
            "low_priority_source": self.low_priority_source,
            "high_priority_value": self.high_priority_value,
            "low_priority_value": self.low_priority_value,
            "needs_human_decision": self.needs_human_decision,
        }


@dataclass(frozen=True)
class AgentProfile:
    role: Role
    agent_id: str
    agent_name: str
    system_prompt: str
    persona_summary: str
    output_contract: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    validation_checklist: list[str] = field(default_factory=list)
    required_artifacts: list[str] = field(default_factory=list)
    produced_artifacts: list[str] = field(default_factory=list)
    readable_paths: list[str] = field(default_factory=list)
    writable_paths: list[str] = field(default_factory=list)
    handoff_contracts: list[str] = field(default_factory=list)
    stop_conditions: list[str] = field(default_factory=list)
    risk_triggers: list[str] = field(default_factory=list)
    human_decision_rules: list[str] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)
    conflict_matrix: list[ProfileConflict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": role_to_wire(self.role),
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "system_prompt": self.system_prompt,
            "persona_summary": self.persona_summary,
            "output_contract": list(self.output_contract),
            "forbidden_actions": list(self.forbidden_actions),
            "allowed_actions": list(self.allowed_actions),
            "validation_checklist": list(self.validation_checklist),
            "required_artifacts": list(self.required_artifacts),
            "produced_artifacts": list(self.produced_artifacts),
            "readable_paths": list(self.readable_paths),
            "writable_paths": list(self.writable_paths),
            "handoff_contracts": list(self.handoff_contracts),
            "stop_conditions": list(self.stop_conditions),
            "risk_triggers": list(self.risk_triggers),
            "human_decision_rules": list(self.human_decision_rules),
            "source_files": list(self.source_files),
            "conflict_matrix": [conflict.to_dict() for conflict in self.conflict_matrix],
            "warnings": list(self.warnings),
        }


def normalize_profile_role(role: Role | str) -> Role:
    parsed = normalize_role(role, field_name="role")
    if parsed is None:
        raise ValueError("profile role cannot be none")
    return parsed
