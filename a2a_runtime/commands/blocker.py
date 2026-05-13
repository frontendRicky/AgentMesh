"""Blocker mutating CLI commands."""

from __future__ import annotations

from a2a_runtime.core.constants import Role, TaskStatus, normalize_role, parse_enum
from a2a_runtime.core.errors import A2ARuntimeError, BlockerError, SchemaError
from a2a_runtime.repositories.blocker_repo import BlockerRepo
from a2a_runtime.commands.base import (
    CLIContext,
    CLIResult,
    EXIT_INVALID_ARGS,
    EXIT_USER_DECISION_REQUIRED,
    error_result,
    require_write_confirmation,
    task_error_result,
)
from a2a_runtime.services.blocker_service import BlockerService


def run_blocker_request(
    ctx: CLIContext,
    *,
    from_agent: str,
    reason: str,
    resume_to_agent: str,
    resume_to_status: str,
    missing_artifacts: list[str],
    required_fix: str,
    yes: bool,
    dry_run: bool,
) -> CLIResult:
    command = "blocker request"
    try:
        task_id = ctx.resolve_task_id()
        state = ctx.state_repo.read(task_id)
    except Exception as exc:
        return task_error_result(command, exc)
    try:
        parsed_from = normalize_role(from_agent, field_name="from")
        parsed_resume_agent = normalize_role(resume_to_agent, field_name="resume_to_agent")
        parsed_resume_status = parse_enum(TaskStatus, resume_to_status, "resume_to_status")
        if parsed_from == Role.CONTROLLER or parsed_from == Role.HUMAN or parsed_from is None:
            return error_result(command, "--from must be pm, architect, developer, or qa", EXIT_INVALID_ARGS, task_id=task_id)
        if parsed_resume_agent is None:
            return error_result(command, "resume_to_agent cannot be none", EXIT_INVALID_ARGS, task_id=task_id)
    except SchemaError as exc:
        return error_result(command, str(exc), EXIT_INVALID_ARGS, task_id=task_id)
    confirmation = require_write_confirmation(command, yes=yes, dry_run=dry_run, task_id=task_id)
    if confirmation is not None:
        return confirmation
    planned = [f"{ctx.paths.messages_dir(task_id)}/from-{parsed_from.value}-*-blocker-request.md"]
    if dry_run:
        return CLIResult(
            ok=True,
            command=command,
            task_id=task_id,
            data={"dry_run": True, "planned_files": planned},
            text=_text(command, task_id, planned, dry_run=True),
        )
    service = _service(ctx)
    try:
        message = service.create_blocker_request(
            task_id=task_id,
            from_agent=parsed_from,
            blocked_from_status=state.current_status,
            resume_to_agent=parsed_resume_agent,
            resume_to_status=parsed_resume_status,
            blocking_reason=reason,
            missing_artifacts=missing_artifacts,
            required_fix=required_fix,
        )
    except A2ARuntimeError as exc:
        return error_result(command, str(exc), EXIT_INVALID_ARGS, task_id=task_id)
    written_path = _message_path_by_id(ctx, task_id, message.message_id)
    written = [str(written_path)] if written_path is not None else []
    return CLIResult(
        ok=True,
        command=command,
        task_id=task_id,
        data={"message_id": message.message_id, "dry_run": False},
        written_files=written,
        text=_text(command, task_id, written, dry_run=False),
    )


def run_blocker_create(
    ctx: CLIContext,
    *,
    from_request: str,
    yes: bool,
    dry_run: bool,
) -> CLIResult:
    command = "blocker create"
    try:
        task_id = ctx.resolve_task_id()
    except Exception as exc:
        return task_error_result(command, exc)
    confirmation = require_write_confirmation(command, yes=yes, dry_run=dry_run, task_id=task_id)
    if confirmation is not None:
        return confirmation
    path = _find_message_path(ctx, task_id, from_request)
    if path is None:
        return error_result(command, f"request message not found: {from_request}", EXIT_INVALID_ARGS, task_id=task_id)
    planned = [f"{ctx.paths.blockers_dir(task_id)}/B-*.md", str(ctx.paths.state_md(task_id)), f"{ctx.paths.messages_dir(task_id)}/from-controller-*-blocker.md"]
    if dry_run:
        return CLIResult(ok=True, command=command, task_id=task_id, data={"dry_run": True, "planned_files": planned}, text=_text(command, task_id, planned, dry_run=True))
    try:
        result = _service(ctx).create_formal_blocker_from_request(path)
    except A2ARuntimeError as exc:
        return error_result(command, str(exc), EXIT_VALIDATION_OR_ARG(exc), task_id=task_id)
    written = [
        str(result.blocker_path),
        str(ctx.paths.state_md(task_id)),
        str(_message_path_by_id(ctx, task_id, result.notification_message.message_id) or ""),
    ]
    return CLIResult(ok=True, command=command, task_id=task_id, data={"blocker_id": result.blocker.blocker_id, "dry_run": False}, written_files=[item for item in written if item], text=_text(command, task_id, [item for item in written if item], dry_run=False))


def run_blocker_resolve(
    ctx: CLIContext,
    *,
    blocker_id: str,
    missing_artifacts_resolved: bool,
    resume_to_agent: str | None,
    resume_to_status: str | None,
    yes: bool,
    dry_run: bool,
) -> CLIResult:
    command = "blocker resolve"
    try:
        task_id = ctx.resolve_task_id()
        state = ctx.state_repo.read(task_id)
    except Exception as exc:
        return task_error_result(command, exc)
    if not missing_artifacts_resolved:
        return error_result(command, "--missing-artifacts-resolved is required", EXIT_INVALID_ARGS, task_id=task_id)
    if state.active_blocker != blocker_id:
        return error_result(command, "blocker_id must match state.active_blocker", EXIT_INVALID_ARGS, task_id=task_id)
    if state.blocked_context is None:
        return error_result(command, "blocked_context is required", EXIT_INVALID_ARGS, task_id=task_id)
    try:
        parsed_agent = normalize_role(resume_to_agent, field_name="resume_to_agent") if resume_to_agent else state.blocked_context.resume_to_agent
        parsed_status = parse_enum(TaskStatus, resume_to_status, "resume_to_status") if resume_to_status else state.blocked_context.resume_to_status
        if parsed_agent is None:
            raise SchemaError("resume_to_agent cannot be none")
    except SchemaError as exc:
        return error_result(command, str(exc), EXIT_INVALID_ARGS, task_id=task_id)
    confirmation = require_write_confirmation(command, yes=yes, dry_run=dry_run, task_id=task_id)
    if confirmation is not None:
        return confirmation
    planned = [str(ctx.paths.state_md(task_id)), f"{ctx.paths.messages_dir(task_id)}/from-controller-*-handoff.md"]
    if dry_run:
        return CLIResult(ok=True, command=command, task_id=task_id, data={"dry_run": True, "planned_files": planned}, text=_text(command, task_id, planned, dry_run=True))
    try:
        result = _service(ctx).resolve_blocker(
            task_id=task_id,
            resume_to_status=parsed_status,
            resume_to_agent=parsed_agent,
            missing_artifacts_resolved=True,
        )
    except A2ARuntimeError as exc:
        return error_result(command, str(exc), EXIT_INVALID_ARGS, task_id=task_id)
    written = [
        str(ctx.paths.state_md(task_id)),
        str(_message_path_by_id(ctx, task_id, result.handoff_message.message_id) or ""),
    ]
    return CLIResult(ok=True, command=command, task_id=task_id, data={"current_status": result.transition.state.current_status.value, "dry_run": False}, written_files=[item for item in written if item], text=_text(command, task_id, [item for item in written if item], dry_run=False))


def _service(ctx: CLIContext) -> BlockerService:
    return BlockerService(
        message_repo=ctx.message_repo,
        blocker_repo=BlockerRepo(ctx.paths),
        state_repo=ctx.state_repo,
        risk_repo=ctx.risk_repo,
    )


def _find_message_path(ctx: CLIContext, task_id: str, message_id: str):
    for path in ctx.message_repo.list_messages(task_id):
        try:
            message = ctx.message_repo.read_message(path)
        except A2ARuntimeError:
            continue
        if message.message_id == message_id:
            return path
    return None


def _message_path_by_id(ctx: CLIContext, task_id: str, message_id: str):
    return _find_message_path(ctx, task_id, message_id)


def EXIT_VALIDATION_OR_ARG(exc: Exception) -> int:
    return EXIT_USER_DECISION_REQUIRED if isinstance(exc, BlockerError) else EXIT_INVALID_ARGS


def _text(command: str, task_id: str, files: list[str], *, dry_run: bool) -> str:
    return "\n".join(
        [
            "[A2A CLI]",
            f"Command: {command}",
            f"Task: {task_id}",
            f"Dry Run: {str(dry_run).lower()}",
            "Files:",
            *[f"- {path}" for path in files],
            "",
        ],
    )
