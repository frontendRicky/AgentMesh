"""Risk read-only CLI commands."""

from __future__ import annotations

import getpass
import os

from a2a_runtime.core.constants import RiskDecisionAction, RiskSeverity, Role, TaskStatus
from a2a_runtime.core.errors import A2ARuntimeError, RiskDecisionError
from a2a_runtime.models.risk import RuntimeRiskFinding
from a2a_runtime.commands.base import (
    CLIContext,
    CLIResult,
    EXIT_INVALID_ARGS,
    EXIT_TASK_NOT_FOUND,
    EXIT_USER_DECISION_REQUIRED,
    error_result,
    require_write_confirmation,
    task_error_result,
)
from a2a_runtime.services.risk_decision_service import RiskDecisionService


def run_risk_list(ctx: CLIContext) -> CLIResult:
    command = "risk list"
    try:
        task_id = ctx.resolve_task_id()
    except Exception as exc:
        return task_error_result(command, exc)
    risks = ctx.risk_repo.list_risks(task_id)
    decisions = {decision.risk_id: decision for decision in ctx.risk_repo.list_decisions(task_id)}
    items = [
        {
            "risk_id": risk.risk_id,
            "severity": risk.severity.value,
            "category": risk.category.value,
            "status": risk.status.value,
            "title": risk.title,
            "has_decision": risk.risk_id in decisions,
        }
        for risk in risks
    ]
    lines = ["[A2A CLI]", "Command: risk list", f"Task: {task_id}"]
    lines.extend(f"- {item['risk_id']} {item['severity']} {item['status']} {item['title']}" for item in items)
    return CLIResult(ok=True, command=command, task_id=task_id, data={"risks": items}, text="\n".join(lines) + "\n")


def run_risk_show(ctx: CLIContext, risk_id: str) -> CLIResult:
    command = "risk show"
    risk_result = _find_risk_result(ctx, command, risk_id)
    if isinstance(risk_result, CLIResult):
        return risk_result
    task_id, risk = risk_result
    data = risk.to_frontmatter()
    text = f"""[A2A CLI]
Command: risk show
Task: {task_id}
Risk ID: {risk.risk_id}
Severity: {risk.severity.value}
Category: {risk.category.value}
Status: {risk.status.value}
Title: {risk.title}
Description: {risk.description}
Evidence: {risk.evidence}
"""
    return CLIResult(ok=True, command=command, task_id=task_id, data={"risk": data}, text=text)


def run_risk_review(ctx: CLIContext, risk_id: str) -> CLIResult:
    command = "risk review"
    risk_result = _find_risk_result(ctx, command, risk_id)
    if isinstance(risk_result, CLIResult):
        return risk_result
    task_id, risk = risk_result
    options = [_option_payload(option) for option in risk.recommended_options]
    text = f"""[A2A CLI]
Command: risk review
Task: {task_id}
Risk ID: {risk.risk_id}
Options:
{chr(10).join(f"- {option['decision']}: {option['description']}" for option in options) if options else "- none"}

This command is read-only. Use Phase 8B risk decide to record a decision.
"""
    return CLIResult(
        ok=True,
        command=command,
        task_id=task_id,
        data={"risk_id": risk.risk_id, "options": options},
        text=text,
    )


def run_risk_prompt(ctx: CLIContext, risk_id: str) -> CLIResult:
    command = "risk prompt"
    risk_result = _find_risk_result(ctx, command, risk_id)
    if isinstance(risk_result, CLIResult):
        return risk_result
    task_id, risk = risk_result
    options = [_option_payload(option) for option in risk.recommended_options]
    prompt = f"""[A2A Risk Decision Required]
Current Agent: controller
Current Task: {task_id}
Risk ID: {risk.risk_id}
Severity: {risk.severity.value}
Category: {risk.category.value}
Status: {risk.status.value}

## Evidence
{risk.evidence}

## Human Options
{chr(10).join(f"- {option['decision']}: {option['description']}" for option in options) if options else "- none"}

## Rules
- This prompt is read-only.
- Do not decide on behalf of the user.
- Do not automatically accept risk.
- Phase 8A does not write risk decisions.
"""
    return CLIResult(
        ok=True,
        command=command,
        task_id=task_id,
        data={"risk_id": risk.risk_id, "prompt": prompt},
        text=prompt,
    )


def run_risk_decide(
    ctx: CLIContext,
    *,
    risk_id: str,
    decision: str,
    reason: str,
    decision_by: str,
    yes: bool,
    dry_run: bool,
) -> CLIResult:
    command = "risk decide"
    if not reason.strip():
        return error_result(command, "--reason is required", EXIT_INVALID_ARGS)
    try:
        task_id = ctx.resolve_task_id()
        risk = ctx.risk_repo.find_risk(task_id, risk_id)
    except KeyError:
        return error_result(command, f"risk not found: {risk_id}", EXIT_TASK_NOT_FOUND)
    except Exception as exc:
        return task_error_result(command, exc)
    confirmation = require_write_confirmation(command, yes=yes, dry_run=dry_run, task_id=task_id)
    if confirmation is not None:
        return confirmation
    planned = [
        f"{ctx.paths.messages_dir(task_id)}/from-human-*-risk-decision.md",
        f"{ctx.paths.messages_dir(task_id)}/from-controller-*-risk-decision-dispatch.md",
        str(ctx.paths.state_md(task_id)),
    ]
    if dry_run:
        warnings = _decision_by_warnings(decision_by)
        return CLIResult(
            ok=True,
            command=command,
            task_id=task_id,
            data={"dry_run": True, "risk_id": risk_id, "planned_files": planned},
            warnings=warnings,
            text=_decision_text(command, task_id, planned, dry_run=True, warnings=warnings),
        )
    before_messages = set(ctx.message_repo.list_messages(task_id))
    service = RiskDecisionService(risk_repo=ctx.risk_repo, state_repo=ctx.state_repo)
    local_user = _local_user()
    mismatch = bool(local_user and decision_by != local_user)
    warnings = _decision_by_warnings(decision_by, local_user=local_user)
    try:
        record = service.record_decision(
            task_id=task_id,
            risk_id=risk_id,
            decision_by=decision_by,
            selected_option=decision,
            decision=decision,
            reason=reason,
            local_user=local_user,
            user_mismatch_warning=mismatch,
        )
        updated_risk = service.apply_decision(task_id=task_id, decision=record)
    except A2ARuntimeError as exc:
        code = EXIT_USER_DECISION_REQUIRED if isinstance(exc, RiskDecisionError) else EXIT_INVALID_ARGS
        return error_result(command, str(exc), code, task_id=task_id)
    after_messages = set(ctx.message_repo.list_messages(task_id))
    written = [str(path) for path in sorted(after_messages - before_messages)]
    if record.decision == RiskDecisionAction.CANCEL_TASK:
        written.append(str(ctx.paths.state_md(task_id)))
    return CLIResult(
        ok=True,
        command=command,
        task_id=task_id,
        data={
            "risk_id": risk.risk_id,
            "decision_id": record.decision_id,
            "risk_status": updated_risk.status.value,
            "dry_run": False,
            "decision_by": decision_by,
            "local_user": local_user,
            "user_mismatch_warning": mismatch,
        },
        warnings=warnings,
        written_files=written,
        text=_decision_text(command, task_id, written, dry_run=False, warnings=warnings),
    )


def _find_risk_result(
    ctx: CLIContext,
    command: str,
    risk_id: str,
) -> tuple[str, RuntimeRiskFinding] | CLIResult:
    try:
        task_id = ctx.resolve_task_id()
        return task_id, ctx.risk_repo.find_risk(task_id, risk_id)
    except KeyError:
        return error_result(command, f"risk not found: {risk_id}", EXIT_TASK_NOT_FOUND)
    except Exception as exc:
        return task_error_result(command, exc)


def _option_payload(option: str) -> dict[str, str | bool | None]:
    try:
        decision = RiskDecisionAction(option)
    except ValueError:
        return {"decision": option, "description": "custom option", "target_agent": None, "target_status": None}
    target_agent, target_status, requires_regeneration = _target_for(decision)
    return {
        "decision": decision.value,
        "description": decision.value.replace("_", " "),
        "target_agent": target_agent.value if target_agent else None,
        "target_status": target_status.value if target_status else None,
        "requires_regeneration": requires_regeneration,
    }


def _decision_text(command: str, task_id: str, files: list[str], *, dry_run: bool, warnings: list[str] | None = None) -> str:
    return "\n".join(
        [
            "[A2A CLI]",
            f"Command: {command}",
            f"Task: {task_id}",
            f"Dry Run: {str(dry_run).lower()}",
            *[f"Warning: {warning}" for warning in (warnings or [])],
            "Files:",
            *[f"- {path}" for path in files],
            "",
        ],
    )


def _local_user() -> str:
    return os.environ.get("USER") or getpass.getuser()


def _decision_by_warnings(decision_by: str, *, local_user: str | None = None) -> list[str]:
    actual = local_user or _local_user()
    if actual and decision_by != actual:
        return [
            (
                f"decision_by '{decision_by}' does not match local user '{actual}'. "
                "--by is an audit field, not strong authentication."
            ),
        ]
    return []


def _target_for(decision: RiskDecisionAction) -> tuple[Role | None, TaskStatus | None, bool]:
    mapping = {
        RiskDecisionAction.REJECT_AND_REPLAN: (Role.ARCHITECT, TaskStatus.ARCHITECT_PROCESSING, True),
        RiskDecisionAction.SEND_TO_PM: (Role.PM, TaskStatus.PM_PROCESSING, True),
        RiskDecisionAction.SEND_TO_ARCHITECT: (Role.ARCHITECT, TaskStatus.ARCHITECT_PROCESSING, True),
        RiskDecisionAction.SEND_TO_DEVELOPER: (Role.DEVELOPER, TaskStatus.DEVELOPER_PROCESSING, True),
        RiskDecisionAction.SEND_TO_QA: (Role.QA, TaskStatus.QA_PROCESSING, True),
        RiskDecisionAction.CONVERT_TO_BLOCKER: (Role.CONTROLLER, TaskStatus.BLOCKED, True),
        RiskDecisionAction.MARK_MANUAL_REQUIRED: (Role.QA, TaskStatus.QA_PROCESSING, True),
        RiskDecisionAction.CANCEL_TASK: (Role.CONTROLLER, TaskStatus.CANCELLED, False),
    }
    return mapping.get(decision, (None, None, False))
