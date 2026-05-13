"""Gate dry-run CLI command."""

from __future__ import annotations

from a2a_runtime.commands.base import CLIContext, CLIResult, EXIT_VALIDATION_FAILED, load_file_change_plan, task_error_result
from a2a_runtime.services.gate_service import GateService


def run_gate_developer(ctx: CLIContext, *, target_path: str, operation: str) -> CLIResult:
    command = "gate developer"
    try:
        task_id = ctx.resolve_task_id()
        state = ctx.state_repo.read(task_id)
    except Exception as exc:
        return task_error_result(command, exc)
    result = GateService().check_developer_write(
        state=state,
        target_path=target_path,
        operation=operation,
        file_change_plan=load_file_change_plan(ctx, task_id),
    )
    data = {
        "allowed": result.allowed,
        "failure_type": result.failure_type.value,
        "failed_conditions": list(result.failed_conditions),
        "reason": result.reason,
        "recommended_next_action": result.recommended_next_action,
        "dry_run": True,
    }
    text = f"""[A2A CLI]
Command: gate developer
Task: {task_id}
Path: {target_path}
Operation: {operation}
Allowed: {str(result.allowed).lower()}
Failure Type: {result.failure_type.value}
Failed Conditions: {', '.join(result.failed_conditions) if result.failed_conditions else 'none'}
Reason: {result.reason}
Recommended Next Action: {result.recommended_next_action}
Dry Run: true
"""
    return CLIResult(
        ok=True,
        command=command,
        task_id=task_id,
        exit_code=0 if result.allowed else EXIT_VALIDATION_FAILED,
        data=data,
        text=text,
    )
