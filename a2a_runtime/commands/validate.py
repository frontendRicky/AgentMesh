"""Validation CLI commands."""

from __future__ import annotations

from a2a_runtime.core.constants import RiskSeverity, TaskStatus
from a2a_runtime.core.errors import RepositoryError, SchemaError, TaskIdentityError
from a2a_runtime.commands.base import (
    CLIContext,
    CLIResult,
    EXIT_SUCCESS,
    EXIT_USER_DECISION_REQUIRED,
    EXIT_VALIDATION_FAILED,
    error_result,
    load_file_change_plan,
    task_error_result,
)
from a2a_runtime.services.gate_service import GateService
from a2a_runtime.services.validation_service import ValidationService


def run_validate(ctx: CLIContext, scope: str = "all", *, target_path: str | None = None, operation: str | None = None) -> CLIResult:
    if scope == "identity":
        return run_validate_identity(ctx)
    if scope == "gate":
        return run_validate_gate(ctx, target_path=target_path, operation=operation)
    if scope == "risk":
        return run_validate_risk(ctx)
    return run_validate_all(ctx)


def run_validate_all(ctx: CLIContext) -> CLIResult:
    command = "validate"
    errors: list[str] = []
    warnings: list[str] = []
    task_id: str | None = None
    try:
        task_id = ctx.resolve_task_id()
    except Exception as exc:
        return task_error_result(command, exc)
    identity = _identity_errors(ctx, task_id)
    errors.extend(identity)
    try:
        state = ctx.state_repo.read(task_id)
        result = ValidationService().validate_state_frontmatter(state.to_frontmatter())
        errors.extend(result.errors)
        warnings.extend(result.warnings)
        if state.active_blocker:
            warnings.append(f"active blocker present: {state.active_blocker}")
    except (RepositoryError, SchemaError) as exc:
        errors.append(str(exc))
    for risk in ctx.risk_repo.list_open_risks(task_id):
        if risk.severity in {RiskSeverity.P0_BLOCKER, RiskSeverity.P1_HIGH}:
            warnings.append(f"unresolved blocking risk: {risk.risk_id}")
    data = {"errors_count": len(errors), "warnings_count": len(warnings)}
    text = _validation_text(command, task_id, errors, warnings)
    return CLIResult(
        ok=not errors,
        command=command,
        exit_code=EXIT_SUCCESS if not errors else EXIT_VALIDATION_FAILED,
        task_id=task_id,
        data=data,
        errors=errors,
        warnings=warnings,
        text=text,
    )


def run_validate_identity(ctx: CLIContext) -> CLIResult:
    command = "validate identity"
    try:
        task_id = ctx.resolve_task_id()
    except Exception as exc:
        return task_error_result(command, exc)
    errors = _identity_errors(ctx, task_id)
    text = _validation_text(command, task_id, errors, [])
    return CLIResult(
        ok=not errors,
        command=command,
        task_id=task_id,
        exit_code=EXIT_SUCCESS if not errors else EXIT_VALIDATION_FAILED,
        data={"errors_count": len(errors)},
        errors=errors,
        text=text,
    )


def run_validate_gate(ctx: CLIContext, *, target_path: str | None, operation: str | None) -> CLIResult:
    command = "validate gate"
    try:
        task_id = ctx.resolve_task_id()
        state = ctx.state_repo.read(task_id)
    except Exception as exc:
        return task_error_result(command, exc)
    if target_path is None or operation is None:
        if state.current_status != TaskStatus.DEVELOPER_PROCESSING:
            message = "developer gate is not available unless current_status == developer_processing"
        else:
            message = "gate check requires --path and --operation for a concrete GateService dry-run"
        return CLIResult(
            ok=False,
            command=command,
            exit_code=EXIT_VALIDATION_FAILED,
            task_id=task_id,
            errors=[message],
            data={"gate_available": False},
            text=_validation_text(command, task_id, [message], []),
        )
    gate = GateService().check_developer_write(
        state=state,
        target_path=target_path,
        operation=operation,
        file_change_plan=load_file_change_plan(ctx, task_id),
    )
    ok = gate.allowed
    data = {
        "allowed": gate.allowed,
        "failure_type": gate.failure_type.value,
        "failed_conditions": list(gate.failed_conditions),
        "reason": gate.reason,
    }
    errors = [] if ok else [gate.reason]
    text = _validation_text(command, task_id, errors, [])
    return CLIResult(
        ok=ok,
        command=command,
        exit_code=EXIT_SUCCESS if ok else EXIT_VALIDATION_FAILED,
        task_id=task_id,
        data=data,
        errors=errors,
        text=text,
    )


def run_validate_risk(ctx: CLIContext) -> CLIResult:
    command = "validate risk"
    try:
        task_id = ctx.resolve_task_id()
    except Exception as exc:
        return task_error_result(command, exc)
    blocking = [
        risk
        for risk in ctx.risk_repo.list_open_risks(task_id)
        if risk.severity in {RiskSeverity.P0_BLOCKER, RiskSeverity.P1_HIGH}
    ]
    errors = [f"unresolved P0/P1 risk: {risk.risk_id}" for risk in blocking]
    exit_code = EXIT_USER_DECISION_REQUIRED if errors else EXIT_SUCCESS
    text = _validation_text(command, task_id, errors, [])
    return CLIResult(
        ok=not errors,
        command=command,
        exit_code=exit_code,
        task_id=task_id,
        errors=errors,
        data={"unresolved_blocking_risks": [risk.risk_id for risk in blocking]},
        text=text,
    )


def _identity_errors(ctx: CLIContext, task_id: str) -> list[str]:
    errors: list[str] = []
    try:
        task = ctx.task_repo.read(task_id)
        state = ctx.state_repo.read(task_id)
    except (RepositoryError, SchemaError) as exc:
        return [str(exc)]
    if task.task_id != state.task_id:
        errors.append("task.md.task_id must equal state.md.task_id")
    active = ctx.workspace_repo.read_active_task_id()
    if active is not None and not ctx.workspace_repo.task_exists(active):
        errors.append("active-task points to missing workspace directory")
    return errors


def _validation_text(command: str, task_id: str | None, errors: list[str], warnings: list[str]) -> str:
    lines = ["[A2A CLI]", f"Command: {command}"]
    if task_id:
        lines.append(f"Task: {task_id}")
    lines.append(f"OK: {str(not errors).lower()}")
    if errors:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in errors)
    if warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines) + "\n"
