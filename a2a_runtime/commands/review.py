"""Review mutating CLI commands."""

from __future__ import annotations

from a2a_runtime.core.constants import ReviewIssueSeverity, ReviewVerdict, Role
from a2a_runtime.core.errors import A2ARuntimeError, ReviewError
from a2a_runtime.models.review import ReviewIssue
from a2a_runtime.repositories.review_repo import ReviewRepo
from a2a_runtime.commands.base import (
    CLIContext,
    CLIResult,
    EXIT_INVALID_ARGS,
    EXIT_USER_DECISION_REQUIRED,
    error_result,
    require_write_confirmation,
    task_error_result,
)
from a2a_runtime.services.review_service import ReviewService


def run_review(
    ctx: CLIContext,
    *,
    action: str,
    stage: str,
    reviewer: str,
    reason: str | None,
    step: str | None,
    yes: bool,
    dry_run: bool,
) -> CLIResult:
    command = f"review {action}"
    if stage not in {"architect", "final"}:
        return error_result(command, "stage must be architect or final", EXIT_INVALID_ARGS)
    if action == "reject" and not (reason or "").strip():
        return error_result(command, "reject requires --reason", EXIT_INVALID_ARGS)
    if action == "approve" and step not in {"1", "2"}:
        return error_result(command, "review approve requires explicit --step 1 or --step 2", EXIT_INVALID_ARGS)
    try:
        task_id = ctx.resolve_task_id()
    except Exception as exc:
        return task_error_result(command, exc)
    confirmation = require_write_confirmation(command, yes=yes, dry_run=dry_run, task_id=task_id)
    if confirmation is not None:
        return confirmation

    planned = _planned_review_files(ctx, task_id, stage, action, step)
    if dry_run:
        missing = _missing_ready_artifacts(ctx, task_id, stage) if action == "approve" else []
        return CLIResult(
            ok=True,
            command=command,
            task_id=task_id,
            data={"dry_run": True, "planned_files": planned, "missing_artifacts": missing, "step": step},
            warnings=[f"missing or not-ready reviewed artifacts: {', '.join(missing)}"] if missing else [],
            text=_text(command, task_id, planned, dry_run=True, step=step, missing=missing),
        )
    service = ReviewService(
        review_repo=ReviewRepo(ctx.paths),
        state_repo=ctx.state_repo,
        message_repo=ctx.message_repo,
        artifact_repo=ctx.artifact_repo,
    )
    try:
        if action == "approve":
            if stage == "architect":
                if step == "1":
                    if ReviewRepo(ctx.paths).find_architect_review(task_id) is None:
                        service.create_architect_review(
                            task_id=task_id,
                            reviewer=reviewer,
                            verdict=ReviewVerdict.APPROVED,
                            reviewed_artifacts=["tech_plan", "file_change_plan", "risk_plan"],
                            issues=[],
                            followup_required=False,
                        )
                    result = service.approve_architect_review_step_1(task_id)
                else:
                    result = service.approve_architect_review_step_2(task_id)
                message_ids = [result.message_id]
            else:
                if step == "1":
                    if ReviewRepo(ctx.paths).find_final_review(task_id) is None:
                        service.create_final_review(
                            task_id=task_id,
                            reviewer=reviewer,
                            verdict=ReviewVerdict.APPROVED,
                            reviewed_artifacts=["test_report", "acceptance_checklist"],
                            issues=[],
                            followup_required=False,
                        )
                    result = service.approve_final_review_step_1(task_id)
                else:
                    result = service.approve_final_review_step_2(task_id)
                message_ids = [result.message_id]
        else:
            issue = ReviewIssue(
                severity=ReviewIssueSeverity.MAJOR,
                description=reason or "",
                affected_artifact="tech_plan" if stage == "architect" else "test_report",
            )
            if stage == "architect":
                service.create_architect_review(
                    task_id=task_id,
                    reviewer=reviewer,
                    verdict=ReviewVerdict.REJECTED,
                    reviewed_artifacts=["tech_plan", "file_change_plan", "risk_plan"],
                    issues=[issue],
                    followup_required=True,
                )
                result = service.reject_architect_review(task_id)
            else:
                service.create_final_review(
                    task_id=task_id,
                    reviewer=reviewer,
                    verdict=ReviewVerdict.REJECTED,
                    reviewed_artifacts=["test_report", "acceptance_checklist"],
                    issues=[issue],
                    followup_required=True,
                )
                result = service.reject_final_review(task_id)
            message_ids = [result.message_id]
    except A2ARuntimeError as exc:
        return error_result(command, str(exc), EXIT_USER_DECISION_REQUIRED if isinstance(exc, ReviewError) else EXIT_INVALID_ARGS, task_id=task_id)
    written = _actual_review_files(ctx, task_id, stage)
    return CLIResult(
        ok=True,
        command=command,
        task_id=task_id,
        data={"stage": stage, "action": action, "step": step, "message_ids": message_ids, "dry_run": False},
        written_files=written,
        text=_text(command, task_id, written, dry_run=False, step=step),
    )


def _planned_review_files(ctx: CLIContext, task_id: str, stage: str, action: str, step: str | None) -> list[str]:
    review_file = "architect-review.md" if stage == "architect" else "final-review.md"
    planned = [str(ctx.paths.state_md(task_id)), f"{ctx.paths.messages_dir(task_id)}/from-controller-*-review.md"]
    if action == "reject" or step == "1":
        planned.insert(0, str(ctx.paths.human_reviews_dir(task_id) / review_file))
    if action == "reject" or step == "2":
        planned.append(f"{ctx.paths.messages_dir(task_id)}/from-controller-*-handoff-or-final.md")
    return planned


def _actual_review_files(ctx: CLIContext, task_id: str, stage: str) -> list[str]:
    review_file = "architect-review.md" if stage == "architect" else "final-review.md"
    return [
        str(ctx.paths.human_reviews_dir(task_id) / review_file),
        str(ctx.paths.state_md(task_id)),
        *[str(path) for path in ctx.message_repo.list_messages(task_id) if "from-controller" in path.name],
    ]


def _missing_ready_artifacts(ctx: CLIContext, task_id: str, stage: str) -> list[str]:
    from a2a_runtime.core.constants import ArtifactStatus, ArtifactType

    required = (
        [ArtifactType.TECH_PLAN, ArtifactType.FILE_CHANGE_PLAN, ArtifactType.RISK_PLAN]
        if stage == "architect"
        else [ArtifactType.TEST_REPORT, ArtifactType.ACCEPTANCE_CHECKLIST]
    )
    missing: list[str] = []
    for artifact_type in required:
        artifact = ctx.artifact_repo.find_artifact(task_id, artifact_type)
        if artifact is None or artifact.status != ArtifactStatus.READY:
            missing.append(artifact_type.value)
    return missing


def _text(
    command: str,
    task_id: str,
    files: list[str],
    *,
    dry_run: bool,
    step: str | None = None,
    missing: list[str] | None = None,
) -> str:
    return "\n".join(
        [
            "[A2A CLI]",
            f"Command: {command}",
            f"Task: {task_id}",
            f"Step: {step or 'n/a'}",
            f"Dry Run: {str(dry_run).lower()}",
            f"Missing Artifacts: {', '.join(missing or []) if missing else 'none'}",
            "Files:",
            *[f"- {path}" for path in files],
            "",
        ],
    )
