"""Status command."""

from __future__ import annotations

from a2a_runtime.core.constants import RiskSeverity, Role, TaskStatus
from a2a_runtime.commands.base import CLIContext, CLIResult, read_optional_task_state, safe_count_paths, task_error_result


def run_status(ctx: CLIContext) -> CLIResult:
    command = "status"
    try:
        task_id = ctx.resolve_task_id()
    except Exception as exc:  # converted to readable CLI error
        return task_error_result(command, exc)

    task, state, warnings = read_optional_task_state(ctx, task_id)
    risks = ctx.risk_repo.list_open_risks(task_id)
    unresolved = [
        risk.risk_id
        for risk in risks
        if risk.severity in {RiskSeverity.P0_BLOCKER, RiskSeverity.P1_HIGH}
    ]
    may_write_code = False
    may_write_reason = "not developer_processing"
    if state is not None and state.current_status == TaskStatus.DEVELOPER_PROCESSING:
        may_write_reason = "target_path / operation required for GateService"
        may_write_code = False
    data = {
        "task_id": task_id,
        "task_title": task.task_title if task else None,
        "task_type": task.task_type.value if task else None,
        "current_status": state.current_status.value if state else None,
        "current_agent": state.current_agent.value if state and state.current_agent else None,
        "human_review_status": state.human_review_status.value if state else None,
        "final_review_status": state.final_review_status.value if state else None,
        "active_blocker": state.active_blocker if state else None,
        "unresolved_risks": unresolved,
        "messages_count": safe_count_paths(ctx.message_repo.list_messages(task_id)),
        "blockers_count": len(list(ctx.paths.blockers_dir(task_id).glob("*.md")))
        if ctx.paths.blockers_dir(task_id).exists()
        else 0,
        "artifacts_count": len(ctx.artifact_repo.list_artifacts(task_id)),
        "human_reviews_count": len(list(ctx.paths.human_reviews_dir(task_id).glob("*.md")))
        if ctx.paths.human_reviews_dir(task_id).exists()
        else 0,
        "may_write_code": may_write_code,
        "may_write_code_reason": may_write_reason,
        "next_action": _next_action(state, bool(unresolved)),
    }
    text = f"""[A2A CLI]
Command: status
Project Root: {ctx.project_root}
Active Task: {task_id}
Current Status: {data['current_status']}
Current Agent: {data['current_agent']}
Human Review Status: {data['human_review_status']}
Final Review Status: {data['final_review_status']}
Active Blocker: {data['active_blocker']}
Unresolved Risks: {', '.join(unresolved) if unresolved else 'none'}
May Write Code: {'yes' if may_write_code else 'no'}, {may_write_reason}
Next Action: {data['next_action']}
"""
    return CLIResult(ok=True, command=command, task_id=task_id, data=data, warnings=warnings, text=text)


def _next_action(state: object | None, has_unresolved_risk: bool) -> str:
    if has_unresolved_risk:
        return "Run a2a-agent risk review <risk_id>"
    if state is None:
        return "Run a2a-agent validate identity"
    current_status = getattr(state, "current_status", None)
    if current_status == TaskStatus.DEVELOPER_PROCESSING:
        return "Run a2a-agent prompt developer --path <path> --operation <operation>"
    if current_status == TaskStatus.FINAL_REVIEW_REQUIRED:
        return "Run final review in Phase 8B"
    if current_status == TaskStatus.COMPLETED:
        return "Task is completed"
    role = getattr(state, "current_agent", None)
    if role in {Role.PM, Role.ARCHITECT, Role.QA, Role.CONTROLLER}:
        return f"Run a2a-agent prompt {role.value}"
    return "Run a2a-agent validate"
