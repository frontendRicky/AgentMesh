"""Prompt CLI commands."""

from __future__ import annotations

from a2a_runtime.core.constants import Role, normalize_role
from a2a_runtime.core.errors import SchemaError
from a2a_runtime.commands.base import CLIContext, CLIResult, EXIT_INVALID_ARGS, error_result, task_error_result
from a2a_runtime.services.prompt_service import PromptService


def run_prompt(
    ctx: CLIContext,
    role: str,
    *,
    target_path: str | None = None,
    operation: str | None = None,
    tool_context: str = "cursor",
    risk_level: str | None = None,
    model_override: str | None = None,
) -> CLIResult:
    command = f"prompt {role}"
    try:
        task_id = ctx.resolve_task_id()
        parsed = normalize_role(role, field_name="role")
        if parsed not in {Role.PM, Role.ARCHITECT, Role.DEVELOPER, Role.QA, Role.CONTROLLER}:
            return error_result(command, "prompt role must be pm, architect, developer, qa, or controller", EXIT_INVALID_ARGS)
    except SchemaError as exc:
        return error_result(command, str(exc), EXIT_INVALID_ARGS)
    except Exception as exc:
        return task_error_result(command, exc)

    service = PromptService(
        ctx.paths,
        state_repo=ctx.state_repo,
        artifact_repo=ctx.artifact_repo,
        message_repo=ctx.message_repo,
        risk_repo=ctx.risk_repo,
    )
    if parsed == Role.DEVELOPER:
        prompt = service.generate_developer_prompt(
            task_id,
            target_path=target_path,
            operation=operation,
            tool_context=tool_context,
            risk_level=risk_level,
            model_override=model_override,
        )
    else:
        prompt = service.generate(
            parsed,
            task_id,
            tool_context=tool_context,
            risk_level=risk_level,
            model_override=model_override,
        )
    return CLIResult(
        ok=True,
        command=command,
        task_id=task_id,
        data={
            "prompt": prompt,
            "tool_context": tool_context,
            "risk_level": risk_level,
            "model_override": model_override,
        },
        text=prompt,
    )
