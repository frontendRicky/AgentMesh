"""Agent model recommendation and routing hints."""

from __future__ import annotations

from dataclasses import dataclass

from a2a_runtime.core.constants import RiskSeverity, Role, parse_enum
from a2a_runtime.core.errors import SchemaError
from a2a_runtime.models.model_policy import (
    AgentModelPreference,
    ModelSelectionResult,
    ToolContext,
    normalize_model_policy_role,
    normalize_tool_context,
)

HIGH_REASONING_MODEL = "claude-opus-4-7-thinking-high"
CODEX_DEVELOPER_MODEL = "gpt-5.5"
LOW_COST_MODELS = {
    "gpt-5.5-mini",
    "gpt-5.4-mini",
    "gpt-4.1-mini",
}


@dataclass(frozen=True)
class ModelSelectionService:
    def default_preferences(self) -> dict[str, AgentModelPreference]:
        return DEFAULT_MODEL_PREFERENCES

    def recommend_for_role(
        self,
        role: Role | str,
        *,
        tool_context: str = "generic",
        risk_level: RiskSeverity | str | None = None,
    ) -> ModelSelectionResult:
        canonical_role = normalize_model_policy_role(role)
        context = normalize_tool_context(tool_context)
        try:
            preference = DEFAULT_MODEL_PREFERENCES[canonical_role]
        except KeyError as exc:
            raise SchemaError(f"model policy role is not supported: {canonical_role}") from exc
        risk = parse_enum(RiskSeverity, risk_level, "risk_level") if risk_level else None
        warnings: list[str] = []
        if context == "codex":
            if preference.codex_model:
                selected_model = preference.codex_model
            else:
                selected_model = CODEX_DEVELOPER_MODEL
                if preference.primary_model != CODEX_DEVELOPER_MODEL:
                    warnings.append(
                        "Codex does not support the primary non-OpenAI model; use gpt-5.5 or run this prompt in Cursor with the recommended model.",
                    )
        else:
            selected_model = preference.primary_model
        reasoning = preference.reasoning_effort
        cost = preference.cost_tier
        rationale = preference.rationale
        if risk in {RiskSeverity.P0_BLOCKER, RiskSeverity.P1_HIGH}:
            if context == "codex":
                selected_model = CODEX_DEVELOPER_MODEL
                reasoning = "high"
                cost = "high"
            elif reasoning != "high" or _is_low_cost_model(selected_model) or preference.cost_tier == "low":
                selected_model = (
                    CODEX_DEVELOPER_MODEL
                    if canonical_role == Role.DEVELOPER.value and context == "codex"
                    else HIGH_REASONING_MODEL
                )
                reasoning = "high"
                cost = "high"
            warnings.append("高风险任务需要高推理模型；Runtime 只推荐，不会自动切换或执行模型。")
            rationale = f"{rationale} 高风险任务需要高推理模型。"
        command_hint = self.render_codex_command_for_model(selected_model) if context == "codex" else None
        return ModelSelectionResult(
            role=canonical_role,
            selected_model=selected_model,
            fallback_models=list(preference.fallback_models),
            tool_context=context,
            reasoning_effort=reasoning,
            cost_tier=cost,
            may_auto_apply=False,
            command_hint=command_hint,
            user_action_required=True,
            rationale=rationale,
            warnings=warnings,
        )

    def recommend_for_task(
        self,
        task_type: str,
        current_agent: Role | str,
        *,
        risk_level: RiskSeverity | str | None = None,
        tool_context: str = "generic",
    ) -> ModelSelectionResult:
        return self.recommend_for_role(
            current_agent,
            tool_context=tool_context,
            risk_level=risk_level,
        )

    def render_prompt_section(self, result: ModelSelectionResult) -> str:
        lines = [
            "Recommended Model:",
            f"- Tool Context: {result.tool_context}",
            f"- Primary Model: {result.selected_model}",
            f"- Fallback Models: [{', '.join(result.fallback_models)}]",
            f"- Reasoning Effort: {result.reasoning_effort}",
            f"- Cost Tier: {result.cost_tier}",
            "- User Action Required: yes",
            "- Runtime Auto Apply: no",
        ]
        if result.tool_context == "cursor":
            lines.append(
                f"- Cursor Action: 请在 Cursor 模型选择器中手动选择 {result.selected_model}；Runtime 不会自动切换模型。",
            )
        elif result.tool_context == "codex":
            lines.append(f"- Command Hint: {result.command_hint}")
            lines.append("- Note: Runtime 不会自动执行该命令。")
        lines.append(f"- Reason: {result.rationale}")
        if result.warnings:
            lines.append(f"- Warnings: {'; '.join(result.warnings)}")
        return "\n".join(lines)

    def render_codex_command(self, result: ModelSelectionResult) -> str:
        if result.tool_context != "codex":
            return ""
        return result.command_hint or self.render_codex_command_for_model(result.selected_model)

    def render_codex_command_for_model(self, model: str) -> str:
        return f"codex --model {model}"

    def render_cursor_instruction(self, result: ModelSelectionResult) -> str:
        if result.tool_context != "cursor":
            return ""
        return (
            f"请在 Cursor 模型选择器中手动选择 {result.selected_model} 后再执行该 Agent Prompt。"
            "Runtime 不会自动切换 Cursor 模型。"
        )

    def render_policy_text(self) -> str:
        return """Model Policy

Runtime 只推荐模型，不调用真实 LLM。
Runtime 不自动切换 Cursor 模型。
Runtime 不自动执行 Codex。
Runtime 不自动执行 Cursor Prompt。
用户需要手动选择模型或手动执行命令提示。
"""


def _is_low_cost_model(model: str) -> bool:
    return model in LOW_COST_MODELS


DEFAULT_MODEL_PREFERENCES: dict[str, AgentModelPreference] = {
    Role.PM.value: AgentModelPreference(
        role=Role.PM,
        primary_model="claude-4.6-sonnet-medium-thinking",
        fallback_models=["gpt-5.5", "claude-opus-4-7-thinking-high"],
        codex_model=None,
        cursor_model_hint="claude-4.6-sonnet-medium-thinking",
        reasoning_effort="medium",
        cost_tier="medium",
        use_cases=["需求澄清", "范围界定", "验收标准", "边界条件拆解"],
        avoid_for=["P0/P1 风险最终裁决", "复杂架构取舍"],
        rationale="PM Agent 需要稳定推理来拆需求和验收标准，通常不需要最高成本模型。",
    ),
    Role.ARCHITECT.value: AgentModelPreference(
        role=Role.ARCHITECT,
        primary_model="claude-opus-4-7-thinking-high",
        fallback_models=["gpt-5.5", "claude-4.6-sonnet-medium-thinking"],
        codex_model=None,
        cursor_model_hint="claude-opus-4-7-thinking-high",
        reasoning_effort="high",
        cost_tier="high",
        use_cases=["方案设计", "备选取舍", "影响范围", "风险识别", "回滚方案"],
        avoid_for=["简单状态报告", "低风险格式整理"],
        rationale="Architect Agent 负责方案设计和风险判断，需要更强长推理能力。",
    ),
    Role.DEVELOPER.value: AgentModelPreference(
        role=Role.DEVELOPER,
        primary_model="gpt-5.5",
        fallback_models=["claude-4.6-sonnet-medium-thinking", "claude-opus-4-7-thinking-high"],
        codex_model="gpt-5.5",
        cursor_model_hint="gpt-5.5",
        reasoning_effort="high",
        cost_tier="high",
        use_cases=["代码实现", "复杂重构", "多文件修改", "测试修复"],
        avoid_for=["未通过 GateService 的源码写入", "未获 Human Review 的实现"],
        rationale="Developer Agent 负责实现和修复，Codex 场景优先推荐 gpt-5.5。",
    ),
    Role.QA.value: AgentModelPreference(
        role=Role.QA,
        primary_model="claude-opus-4-7-thinking-high",
        fallback_models=["gpt-5.5", "claude-4.6-sonnet-medium-thinking"],
        codex_model=None,
        cursor_model_hint="claude-opus-4-7-thinking-high",
        reasoning_effort="high",
        cost_tier="high",
        use_cases=["验收验证", "遗漏识别", "回归风险", "P0/P1 风险识别"],
        avoid_for=["低风险摘要", "无需推理的格式整理"],
        rationale="QA / Verifier Agent 需要保持怀疑并识别高风险遗漏，优先使用高推理模型。",
    ),
    Role.CONTROLLER.value: AgentModelPreference(
        role=Role.CONTROLLER,
        primary_model="gpt-5.5-mini",
        fallback_models=["gpt-5.5"],
        codex_model=None,
        cursor_model_hint="gpt-5.5-mini",
        reasoning_effort="low",
        cost_tier="low",
        use_cases=["状态解释", "报告摘要", "下一步提示", "人工可读说明"],
        avoid_for=["P0/P1 风险决策", "复杂架构取舍"],
        rationale="Flow Controller 的核心判断由 Python Runtime 执行，默认不需要高成本模型。",
    ),
    "risk": AgentModelPreference(
        role="risk",
        primary_model="claude-opus-4-7-thinking-high",
        fallback_models=["gpt-5.5"],
        codex_model=None,
        cursor_model_hint="claude-opus-4-7-thinking-high",
        reasoning_effort="high",
        cost_tier="high",
        use_cases=["风险分级", "方案冲突判断", "人工选项生成", "P0/P1 风险审查"],
        avoid_for=["轻量状态说明", "普通任务摘要"],
        rationale="Risk Decision Gate 需要风险分级和冲突判断，P0/P1 场景不能使用 lightweight primary。",
    ),
}
