"""Report CLI command."""

from __future__ import annotations

from pathlib import Path

from a2a_runtime.repositories.blocker_repo import BlockerRepo
from a2a_runtime.repositories.review_repo import ReviewRepo
from a2a_runtime.commands.base import (
    CLIContext,
    CLIResult,
    EXIT_INVALID_ARGS,
    error_result,
    require_write_confirmation,
    task_error_result,
)
from a2a_runtime.services.report_service import ReportService


def run_report(
    ctx: CLIContext,
    *,
    output: str | None = None,
    yes: bool = False,
    dry_run: bool = False,
) -> CLIResult:
    command = "report"
    try:
        task_id = ctx.resolve_task_id()
        report = ReportService(
            task_repo=ctx.task_repo,
            state_repo=ctx.state_repo,
            artifact_repo=ctx.artifact_repo,
            message_repo=ctx.message_repo,
            blocker_repo=BlockerRepo(ctx.paths),
            review_repo=ReviewRepo(ctx.paths),
            risk_repo=ctx.risk_repo,
        ).build_report(task_id)
    except Exception as exc:
        return task_error_result(command, exc)
    if output is None:
        return CLIResult(
            ok=True,
            command=command,
            task_id=task_id,
            data=report.data,
            text=report.render_text(),
        )

    confirmation = require_write_confirmation(command, yes=yes, dry_run=dry_run, task_id=task_id)
    if confirmation is not None:
        return confirmation
    target_result = _safe_archive_output(ctx, task_id, output)
    if isinstance(target_result, CLIResult):
        return target_result
    target = target_result
    data = {
        **report.data,
        "dry_run": dry_run,
        "planned_writes": [str(target)],
    }
    if dry_run:
        return CLIResult(
            ok=True,
            command=command,
            task_id=task_id,
            data=data,
            text=_export_text(task_id, [str(target)], dry_run=True),
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report.render_text(), encoding="utf-8")
    return CLIResult(
        ok=True,
        command=command,
        task_id=task_id,
        data={**report.data, "dry_run": False},
        written_files=[str(target)],
        text=_export_text(task_id, [str(target)], dry_run=False),
    )


def _safe_archive_output(ctx: CLIContext, task_id: str, output: str) -> Path | CLIResult:
    candidate = Path(output)
    if candidate.is_absolute():
        return error_result("report", "report --output must be relative to the current task archive", EXIT_INVALID_ARGS, task_id=task_id)
    if ".." in candidate.parts:
        return error_result("report", "report --output cannot contain '..'", EXIT_INVALID_ARGS, task_id=task_id)
    if not candidate.parts or candidate.parts[0] != "archive":
        return error_result("report", "report --output must start with archive/", EXIT_INVALID_ARGS, task_id=task_id)
    archive_dir = ctx.paths.task_dir(task_id) / "archive"
    target = ctx.paths.task_dir(task_id) / candidate
    symlink_error = _symlink_error(ctx.paths.task_dir(task_id), target)
    if symlink_error:
        return error_result("report", symlink_error, EXIT_INVALID_ARGS, task_id=task_id)
    try:
        target.resolve().relative_to(archive_dir.resolve())
    except ValueError:
        return error_result("report", "report --output must stay inside the current task archive", EXIT_INVALID_ARGS, task_id=task_id)
    return target


def _symlink_error(task_dir: Path, target: Path) -> str | None:
    archive_dir = task_dir / "archive"
    if archive_dir.is_symlink():
        return "report archive directory must not be a symlink"
    current = task_dir
    for part in target.relative_to(task_dir).parts:
        current = current / part
        if current.exists() and current.is_symlink():
            return f"report --output path must not contain symlink: {current}"
    return None


def _export_text(task_id: str, files: list[str], *, dry_run: bool) -> str:
    return "\n".join(
        [
            "[A2A CLI]",
            "Command: report",
            f"Task: {task_id}",
            f"Dry Run: {str(dry_run).lower()}",
            "Files:",
            *[f"- {path}" for path in files],
            "",
        ],
    )
