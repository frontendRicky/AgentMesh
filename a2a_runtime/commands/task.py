"""Task CLI commands."""

from __future__ import annotations

from a2a_runtime.core.errors import RepositoryError, SchemaError
from a2a_runtime.core.ids import validate_task_id
from a2a_runtime.commands.base import (
    CLIContext,
    CLIResult,
    EXIT_INVALID_ARGS,
    EXIT_TASK_NOT_FOUND,
    EXIT_USER_DECISION_REQUIRED,
    EXIT_VALIDATION_FAILED,
    error_result,
    require_write_confirmation,
    project_markers,
    read_optional_task_state,
)
from a2a_runtime.services.task_service import TaskService


def run_task_list(ctx: CLIContext) -> CLIResult:
    active = ctx.workspace_repo.read_active_task_id()
    items = []
    for task_id in ctx.workspace_repo.list_task_ids():
        task, state, warnings = read_optional_task_state(ctx, task_id)
        items.append(
            {
                "task_id": task_id,
                "title": task.task_title if task else None,
                "current_status": state.current_status.value if state else None,
                "active": task_id == active,
                "warnings": warnings,
            },
        )
    text_lines = ["[A2A CLI]", "Command: task list"]
    for item in items:
        marker = "*" if item["active"] else "-"
        text_lines.append(
            f"{marker} {item['task_id']} {item['current_status'] or 'unknown'} {item['title'] or ''}".rstrip(),
        )
    return CLIResult(
        ok=True,
        command="task list",
        task_id=active,
        data={"tasks": items},
        text="\n".join(text_lines) + "\n",
    )


def run_task_active(ctx: CLIContext) -> CLIResult:
    active = ctx.workspace_repo.read_active_task_id()
    if active is None:
        return error_result("task active", "active task is not set", EXIT_TASK_NOT_FOUND)
    text = f"[A2A CLI]\nCommand: task active\nActive Task: {active}\n"
    return CLIResult(
        ok=True,
        command="task active",
        task_id=active,
        data={"active_task_id": active},
        text=text,
    )


def run_task_use(ctx: CLIContext, task_id: str, *, yes: bool = False, dry_run: bool = False) -> CLIResult:
    command = "task use"
    try:
        validate_task_id(task_id)
    except SchemaError as exc:
        return error_result(command, str(exc), EXIT_TASK_NOT_FOUND, task_id=task_id)
    if not ctx.workspace_repo.task_exists(task_id):
        return error_result(command, f"task not found: {task_id}", EXIT_TASK_NOT_FOUND, task_id=task_id)
    try:
        ctx.task_repo.read(task_id)
        ctx.state_repo.read(task_id)
    except (RepositoryError, SchemaError) as exc:
        return error_result(command, str(exc), EXIT_TASK_NOT_FOUND, task_id=task_id)
    confirmation = require_write_confirmation(command, yes=yes, dry_run=dry_run, task_id=task_id)
    if confirmation is not None:
        return confirmation
    if dry_run:
        return CLIResult(
            ok=True,
            command=command,
            task_id=task_id,
            data={"active_task_id": task_id, "dry_run": True, "planned_writes": [str(ctx.paths.active_task_path)]},
            text=f"[A2A CLI]\nCommand: task use\nDry Run: true\nActive Task: {task_id}\n",
        )
    ctx.workspace_repo.write_active_task_id(task_id)
    text = f"[A2A CLI]\nCommand: task use\nActive Task: {task_id}\n"
    return CLIResult(
        ok=True,
        command=command,
        task_id=task_id,
        data={"active_task_id": task_id, "dry_run": False},
        written_files=[str(ctx.paths.active_task_path)],
        text=text,
    )


def run_task_create(
    ctx: CLIContext,
    *,
    task_type: str,
    title: str,
    priority: str,
    owner: str,
    task_id: str | None,
    no_active: bool,
    yes: bool,
    dry_run: bool,
) -> CLIResult:
    command = "task create"
    confirmation = require_write_confirmation(command, yes=yes, dry_run=dry_run, task_id=task_id)
    if confirmation is not None:
        return confirmation
    service = TaskService(
        workspace_repo=ctx.workspace_repo,
        task_repo=ctx.task_repo,
        state_repo=ctx.state_repo,
        message_repo=ctx.message_repo,
    )
    try:
        plan = service.plan_create_task(
            task_type=task_type,
            title=title,
            priority=priority,
            owner=owner,
            task_id=task_id,
            set_active=not no_active,
        )
    except SchemaError as exc:
        return error_result(command, str(exc), EXIT_INVALID_ARGS, task_id=task_id)
    except RepositoryError as exc:
        return error_result(command, str(exc), EXIT_VALIDATION_FAILED, task_id=task_id)
    markers = project_markers(ctx.project_root)
    existing_tasks = len(ctx.workspace_repo.list_task_ids())
    root_data = {
        "project_root": str(ctx.project_root),
        "project_markers": markers,
        "existing_tasks": existing_tasks,
        "planned_task_id": plan.task_id,
    }
    if dry_run:
        text = _task_create_text(plan.task_id, plan.planned_files, dry_run=True, root_data=root_data)
        return CLIResult(
            ok=True,
            command=command,
            task_id=plan.task_id,
            data={"dry_run": True, "planned_files": plan.planned_files, **root_data},
            written_files=[],
            warnings=list(ctx.root_warnings),
            text=text,
        )
    result = service.create_task(plan)
    written = [str(path) for path in result.written_files]
    text = _task_create_text(result.task_id, written, dry_run=False, root_data=root_data)
    return CLIResult(
        ok=True,
        command=command,
        task_id=result.task_id,
        data={"dry_run": False, "active": not no_active, **root_data},
        written_files=written,
        warnings=list(ctx.root_warnings),
        text=text,
    )


def _task_create_text(
    task_id: str,
    files: list[str],
    *,
    dry_run: bool,
    root_data: dict[str, object],
) -> str:
    markers = root_data["project_markers"]
    assert isinstance(markers, dict)
    return "\n".join(
        [
            "[A2A CLI]",
            "Command: task create",
            f"Project Root: {root_data['project_root']}",
            "Project Markers:",
            f"- .ai-agents: {'yes' if markers.get('.ai-agents') else 'no'}",
            f"- .git: {'yes' if markers.get('.git') else 'no'}",
            f"- pyproject.toml: {'yes' if markers.get('pyproject.toml') else 'no'}",
            f"- package.json: {'yes' if markers.get('package.json') else 'no'}",
            f"Existing Tasks: {root_data['existing_tasks']}",
            f"Will Create Task: {root_data['planned_task_id']}",
            f"Task: {task_id}",
            f"Dry Run: {str(dry_run).lower()}",
            "Files:",
            *[f"- {path}" for path in files],
            "",
        ],
    )
