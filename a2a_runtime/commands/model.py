"""Model recommendation CLI commands."""

from __future__ import annotations

from a2a_runtime.commands.base import CLIContext, CLIResult, EXIT_INVALID_ARGS, error_result
from a2a_runtime.core.errors import RepositoryError, SchemaError
from a2a_runtime.repositories.agent_card_repo import AgentCardRepo
from a2a_runtime.services.model_selection_service import ModelSelectionService


def run_model_list(ctx: CLIContext) -> CLIResult:
    command = "model list"
    service = ModelSelectionService()
    policies = [preference.to_dict() for preference in service.default_preferences().values()]
    overrides_file: dict[str, str] = {}
    overrides_warnings: list[str] = []
    try:
        overrides_file, overrides_warnings = AgentCardRepo(ctx.paths).read_model_overrides()
    except (RepositoryError, SchemaError) as exc:
        overrides_warnings = [str(exc)]
    lines = ["[A2A CLI]", "Command: model list", f"Project Root: {ctx.project_root}", "Model Policies:"]
    for item in policies:
        override = overrides_file.get(item["role"])
        marker = f" [override: {override}]" if override else ""
        lines.append(
            f"- {item['role']}: {item['primary_model']} "
            f"({item['reasoning_effort']} reasoning, {item['cost_tier']} cost){marker}",
        )
    if overrides_file:
        lines.append("")
        lines.append("Active Overrides (.ai-agents/agent-cards/model-overrides.md):")
        for role_key in sorted(overrides_file):
            lines.append(f"- {role_key}: {overrides_file[role_key]}")
    return CLIResult(
        ok=True,
        command=command,
        data={"policies": policies, "overrides": overrides_file},
        warnings=overrides_warnings,
        text="\n".join(lines) + "\n",
    )


def run_model_policy(ctx: CLIContext) -> CLIResult:
    command = "model policy"
    service = ModelSelectionService()
    text = f"""[A2A CLI]
Command: model policy
Project Root: {ctx.project_root}

{service.render_policy_text()}
Safety:
- Runtime 只推荐模型。
- Runtime 不调用真实 LLM。
- Runtime 不自动切换 Cursor 模型。
- Runtime 不自动执行 Codex。
- Runtime 不自动执行 Cursor Prompt。
"""
    return CLIResult(
        ok=True,
        command=command,
        data={"policy": service.render_policy_text()},
        text=text,
    )


def run_model_recommend(
    ctx: CLIContext,
    *,
    agent: str,
    tool_context: str = "generic",
    risk_level: str | None = None,
    model_override: str | None = None,
) -> CLIResult:
    command = "model recommend"
    service = ModelSelectionService()
    overrides_file_value: str | None = None
    agent_card_value: str | None = None
    overrides_warnings: list[str] = []
    try:
        repo = AgentCardRepo(ctx.paths)
        overrides_file, overrides_warnings = repo.read_model_overrides()
        try:
            from a2a_runtime.models.model_policy import normalize_model_policy_role
            canonical = normalize_model_policy_role(agent)
            overrides_file_value = overrides_file.get(canonical)
        except SchemaError:
            overrides_file_value = None
        try:
            card, _ = repo.try_read_agent_card(agent)
            if card is not None:
                agent_card_value = card.model
        except (RepositoryError, SchemaError):
            agent_card_value = None
    except (RepositoryError, SchemaError) as exc:
        overrides_warnings = [str(exc)]
    try:
        result = service.recommend_for_role(
            agent,
            tool_context=tool_context,
            risk_level=risk_level,
            cli_override=model_override,
            overrides_file_value=overrides_file_value,
            agent_card_value=agent_card_value,
        )
    except SchemaError as exc:
        return error_result(command, str(exc), EXIT_INVALID_ARGS)
    data = result.to_dict()
    data["role"] = result.role_value
    lines = [
        "[A2A CLI]",
        "Command: model recommend",
        f"Project Root: {ctx.project_root}",
        "Recommended Model:",
        f"- Role: {result.role_value}",
        f"- Tool Context: {result.tool_context}",
        f"- Primary Model: {result.selected_model}",
        f"- Fallback Models: [{', '.join(result.fallback_models)}]",
        f"- Reasoning Effort: {result.reasoning_effort}",
        f"- Cost Tier: {result.cost_tier}",
        f"- Override Source: {result.override_source}",
        f"- User Action Required: {'yes' if result.user_action_required else 'no'}",
        f"- Runtime Auto Apply: {'yes' if result.may_auto_apply else 'no'}",
    ]
    if result.tool_context == "codex":
        lines.append(f"- Command Hint: {result.command_hint}")
        lines.append("- Note: Runtime 不会自动执行该命令。")
    elif result.tool_context == "cursor":
        lines.append(f"- Cursor Action: 请在 Cursor 模型选择器中手动选择 {result.selected_model}")
        lines.append("- Note: Runtime 不会自动切换 Cursor 模型。")
    lines.append(f"- Reason: {result.rationale}")
    if result.warnings:
        lines.append(f"- Warnings: {'; '.join(result.warnings)}")
    return CLIResult(
        ok=True,
        command=command,
        data=data,
        warnings=overrides_warnings,
        text="\n".join(lines) + "\n",
    )
