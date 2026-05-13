"""Finalize mutating CLI command."""

from __future__ import annotations

from a2a_runtime.core.errors import A2ARuntimeError, FinalDeliveryError
from a2a_runtime.repositories.review_repo import ReviewRepo
from a2a_runtime.commands.base import (
    CLIContext,
    CLIResult,
    EXIT_USER_DECISION_REQUIRED,
    EXIT_VALIDATION_FAILED,
    error_result,
    require_write_confirmation,
    task_error_result,
)
from a2a_runtime.services.final_delivery_service import FinalDeliveryService


def run_finalize(ctx: CLIContext, *, yes: bool, dry_run: bool) -> CLIResult:
    command = "finalize"
    try:
        task_id = ctx.resolve_task_id()
    except Exception as exc:
        return task_error_result(command, exc)
    confirmation = require_write_confirmation(command, yes=yes, dry_run=dry_run, task_id=task_id)
    if confirmation is not None:
        return confirmation
    service = _service(ctx)
    gate = service.validate_final_delivery_gate(task_id)
    planned = [
        str(ctx.paths.task_dir(task_id) / "artifacts/final/final-delivery.md"),
        f"{ctx.paths.messages_dir(task_id)}/from-controller-*-final.md",
    ]
    if dry_run:
        return CLIResult(
            ok=gate.ok,
            command=command,
            task_id=task_id,
            exit_code=0 if gate.ok else _gate_error_code(gate.errors),
            errors=list(gate.errors),
            data={"dry_run": True, "gate_ok": gate.ok, "planned_files": planned},
            text=_text(command, task_id, planned, dry_run=True, errors=gate.errors),
        )
    if not gate.ok:
        return error_result(command, "; ".join(gate.errors), _gate_error_code(gate.errors), task_id=task_id)
    before_messages = set(ctx.message_repo.list_messages(task_id))
    try:
        path = service.write_final_delivery(task_id)
    except (A2ARuntimeError, FinalDeliveryError) as exc:
        return error_result(command, str(exc), EXIT_VALIDATION_FAILED, task_id=task_id)
    after_messages = set(ctx.message_repo.list_messages(task_id))
    written = [str(path), *[str(item) for item in sorted(after_messages - before_messages)]]
    return CLIResult(
        ok=True,
        command=command,
        task_id=task_id,
        data={"final_delivery_path": str(path), "gate_ok": True, "dry_run": False},
        written_files=written,
        text=_text(command, task_id, written, dry_run=False, errors=[]),
    )


def _service(ctx: CLIContext) -> FinalDeliveryService:
    return FinalDeliveryService(
        state_repo=ctx.state_repo,
        task_repo=ctx.task_repo,
        artifact_repo=ctx.artifact_repo,
        review_repo=ReviewRepo(ctx.paths),
        risk_repo=ctx.risk_repo,
        message_repo=ctx.message_repo,
    )


def _gate_error_code(errors: list[str]) -> int:
    if any("unresolved blocking risk" in error for error in errors):
        return EXIT_USER_DECISION_REQUIRED
    return EXIT_VALIDATION_FAILED


def _text(command: str, task_id: str, files: list[str], *, dry_run: bool, errors: list[str]) -> str:
    lines = [
        "[A2A CLI]",
        f"Command: {command}",
        f"Task: {task_id}",
        f"Dry Run: {str(dry_run).lower()}",
    ]
    if errors:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in errors)
    lines.append("Files:")
    lines.extend(f"- {path}" for path in files)
    lines.append("")
    return "\n".join(lines)
