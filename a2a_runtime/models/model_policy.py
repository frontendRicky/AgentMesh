"""Model recommendation policy models.

These models only describe recommendations. They never authorize runtime model
execution, Cursor model switching, or Codex command execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from a2a_runtime.core.constants import Role, normalize_role
from a2a_runtime.core.errors import SchemaError

ToolContext = Literal["cursor", "codex", "generic"]

VALID_TOOL_CONTEXTS = {"cursor", "codex", "generic"}
VALID_REASONING_EFFORTS = {"low", "medium", "high"}
VALID_COST_TIERS = {"low", "medium", "high"}
MODEL_POLICY_ROLES = {"pm", "architect", "developer", "qa", "controller", "human", "risk"}


def normalize_model_policy_role(value: Role | str) -> Role | str:
    raw = value.value if isinstance(value, Role) else str(value)
    if raw == "risk":
        return "risk"
    normalized = normalize_role(value, field_name="role")
    if normalized is None:
        raise SchemaError("role is required")
    return normalized


def normalize_tool_context(value: str) -> ToolContext:
    if value not in VALID_TOOL_CONTEXTS:
        raise SchemaError("tool_context must be cursor, codex, or generic")
    return value  # type: ignore[return-value]


@dataclass(frozen=True)
class AgentModelPreference:
    role: Role | str
    primary_model: str
    fallback_models: list[str]
    reasoning_effort: str
    cost_tier: str
    use_cases: list[str]
    avoid_for: list[str]
    rationale: str
    codex_model: str | None = None
    cursor_model_hint: str | None = None

    def __post_init__(self) -> None:
        role = normalize_model_policy_role(self.role)
        if role not in MODEL_POLICY_ROLES:
            raise SchemaError(f"model policy role is not supported: {role}")
        if not self.primary_model.strip():
            raise SchemaError("primary_model is required")
        if self.reasoning_effort not in VALID_REASONING_EFFORTS:
            raise SchemaError("reasoning_effort must be low, medium, or high")
        if self.cost_tier not in VALID_COST_TIERS:
            raise SchemaError("cost_tier must be low, medium, or high")

    @property
    def role_value(self) -> str:
        return normalize_model_policy_role(self.role)

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role_value,
            "primary_model": self.primary_model,
            "fallback_models": list(self.fallback_models),
            "codex_model": self.codex_model,
            "cursor_model_hint": self.cursor_model_hint,
            "reasoning_effort": self.reasoning_effort,
            "cost_tier": self.cost_tier,
            "use_cases": list(self.use_cases),
            "avoid_for": list(self.avoid_for),
            "rationale": self.rationale,
        }


VALID_OVERRIDE_SOURCES = {"default", "agent_card", "overrides_file", "cli", "policy"}


@dataclass(frozen=True)
class ModelSelectionResult:
    role: Role | str
    selected_model: str
    fallback_models: list[str]
    tool_context: ToolContext
    reasoning_effort: str
    cost_tier: str
    rationale: str
    command_hint: str | None = None
    warnings: list[str] = field(default_factory=list)
    may_auto_apply: bool = False
    user_action_required: bool = True
    override_source: str = "default"

    def __post_init__(self) -> None:
        normalize_model_policy_role(self.role)
        normalize_tool_context(self.tool_context)
        if self.may_auto_apply is not False:
            raise SchemaError("model recommendation may_auto_apply must always be False")
        if self.user_action_required is not True:
            raise SchemaError("model recommendation user_action_required must always be True")
        if self.reasoning_effort not in VALID_REASONING_EFFORTS:
            raise SchemaError("reasoning_effort must be low, medium, or high")
        if self.cost_tier not in VALID_COST_TIERS:
            raise SchemaError("cost_tier must be low, medium, or high")
        if self.override_source not in VALID_OVERRIDE_SOURCES:
            raise SchemaError(
                f"override_source must be one of: {', '.join(sorted(VALID_OVERRIDE_SOURCES))}",
            )

    @property
    def role_value(self) -> str:
        return normalize_model_policy_role(self.role)

    def to_dict(self) -> dict[str, object]:
        return {
            "role": self.role_value,
            "selected_model": self.selected_model,
            "fallback_models": list(self.fallback_models),
            "tool_context": self.tool_context,
            "reasoning_effort": self.reasoning_effort,
            "cost_tier": self.cost_tier,
            "may_auto_apply": self.may_auto_apply,
            "command_hint": self.command_hint,
            "user_action_required": self.user_action_required,
            "rationale": self.rationale,
            "warnings": list(self.warnings),
            "override_source": self.override_source,
        }
