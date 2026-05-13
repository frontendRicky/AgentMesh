"""Minimal safe argparse CLI for the local A2A runtime."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from a2a_runtime.commands.base import (
    CLIContext,
    CLIResult,
    EXIT_INTERNAL_ERROR,
    EXIT_INVALID_ARGS,
    error_result,
    format_error_text,
    normalize_error,
    validate_project_root_safety,
)
from a2a_runtime.commands.blocker import run_blocker_create, run_blocker_request, run_blocker_resolve
from a2a_runtime.commands.finalize import run_finalize
from a2a_runtime.commands.gate import run_gate_developer
from a2a_runtime.commands.model import run_model_list, run_model_policy, run_model_recommend
from a2a_runtime.commands.prompt import run_prompt
from a2a_runtime.commands.report import run_report
from a2a_runtime.commands.review import run_review
from a2a_runtime.commands.risk import (
    run_risk_decide,
    run_risk_list,
    run_risk_prompt,
    run_risk_review,
    run_risk_show,
)
from a2a_runtime.commands.status import run_status
from a2a_runtime.commands.task import run_task_active, run_task_create, run_task_list, run_task_use
from a2a_runtime.commands.validate import run_validate
from a2a_runtime.core.errors import A2ARuntimeError


class CLIArgumentError(Exception):
    pass


class A2AArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise CLIArgumentError(message)


def main(argv: Sequence[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    global_options, command_argv = _extract_global_options(raw_argv)
    parser = build_parser()
    try:
        args = parser.parse_args(command_argv)
    except CLIArgumentError as exc:
        result = error_result(" ".join(command_argv) or "a2a-agent", str(exc), EXIT_INVALID_ARGS)
        _emit(result, json_output=bool(global_options["json"]))
        return result.exit_code
    except SystemExit as exc:
        code = int(exc.code) if isinstance(exc.code, int) else EXIT_INVALID_ARGS
        return 0 if code == 0 else EXIT_INVALID_ARGS

    if not hasattr(args, "handler"):
        parser.print_help()
        return 0

    project_root = Path(global_options["project_root"]).expanduser().resolve()
    try:
        root_warnings = validate_project_root_safety(
            project_root,
            allow_non_project_root=bool(global_options["allow_non_project_root"]),
        )
    except A2ARuntimeError as exc:
        result = error_result(" ".join(command_argv), str(exc), EXIT_INVALID_ARGS)
        _emit(result, json_output=bool(global_options["json"]))
        return result.exit_code
    ctx = CLIContext(
        project_root=project_root,
        task_id=global_options["task_id"],
        json_output=global_options["json"],
        verbose=global_options["verbose"],
        root_warnings=root_warnings,
    )
    try:
        result = args.handler(ctx, args)
    except A2ARuntimeError as exc:
        result = error_result(" ".join(command_argv), str(exc), EXIT_INTERNAL_ERROR)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        result = error_result(" ".join(command_argv), str(exc), EXIT_INTERNAL_ERROR)
    if ctx.root_warnings:
        result.warnings.extend(ctx.root_warnings)
    _emit(result, json_output=ctx.json_output)
    return result.exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = A2AArgumentParser(
        prog="a2a-agent",
        description=(
            "Local Python A2A runtime CLI. It manages Markdown A2A task files, "
            "generates prompts, and enforces gates without calling an LLM."
        ),
        epilog=_help_epilog(
            "a2a-agent",
            writes="Only mutating subcommands write workspace files, and they require --yes or --dry-run.",
            dry_run="Mutating commands support --dry-run where applicable.",
            yes="Mutating commands require --yes to write.",
            example="python3.11 -m a2a_runtime.cli --project-root . status",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--project-root", help="Project root; defaults to the current directory.")
    parser.add_argument("--task-id", help="Explicit task id. Otherwise active-task.md or a single task is used.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--verbose", action="store_true", help="Reserved for more detailed diagnostics.")
    parser.add_argument(
        "--allow-non-project-root",
        action="store_true",
        help="Allow a root without project markers; emits a warning and is intended for tests only.",
    )
    subparsers = parser.add_subparsers(dest="command", parser_class=A2AArgumentParser)

    status = subparsers.add_parser(
        "status",
        help="Show active task runtime status",
        description="Show active task status, blockers, risks, and suggested next action.",
        epilog=_help_epilog(
            "status",
            writes="Read-only; does not write workspace files.",
            dry_run="Not needed.",
            yes="Not required.",
            example="python3.11 -m a2a_runtime.cli --project-root . status",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    status.set_defaults(handler=lambda ctx, args: run_status(ctx))

    validate = subparsers.add_parser(
        "validate",
        help="Run validation checks",
        description="Validate task identity, state, gate readiness, and unresolved blocking risks.",
        epilog=_help_epilog(
            "validate",
            writes="Read-only; does not write workspace files.",
            dry_run="Not needed.",
            yes="Not required.",
            example="python3.11 -m a2a_runtime.cli --project-root . validate identity",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    validate_sub = validate.add_subparsers(dest="validate_scope", parser_class=A2AArgumentParser)
    validate.set_defaults(handler=lambda ctx, args: run_validate(ctx, "all"))
    identity = validate_sub.add_parser("identity", help="Validate task identity")
    identity.set_defaults(handler=lambda ctx, args: run_validate(ctx, "identity"))
    gate = validate_sub.add_parser("gate", help="Validate developer gate")
    gate.add_argument("--path", dest="target_path")
    gate.add_argument("--operation", choices=["create", "modify", "delete"])
    gate.set_defaults(
        handler=lambda ctx, args: run_validate(
            ctx,
            "gate",
            target_path=args.target_path,
            operation=args.operation,
        ),
    )
    risk = validate_sub.add_parser("risk", help="Validate unresolved blocking risk")
    risk.set_defaults(handler=lambda ctx, args: run_validate(ctx, "risk"))

    task = subparsers.add_parser(
        "task",
        help="Task workspace commands",
        description="List, switch, or create A2A task workspaces.",
        epilog=_help_epilog(
            "task",
            writes="task list/active are read-only; task use and task create write workspace files.",
            dry_run="task use and task create support --dry-run.",
            yes="task use and task create require --yes to write.",
            example="python3.11 -m a2a_runtime.cli --project-root . task create --type feature --title \"新增设置页\" --priority P1 --owner zhangxia --yes",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    task_sub = task.add_subparsers(dest="task_command", required=True, parser_class=A2AArgumentParser)
    task_create = task_sub.add_parser(
        "create",
        help="Create a new task",
        description="Create a task workspace and initial controller handoff. Does not create business source files.",
        epilog=_help_epilog(
            "task create",
            writes="Writes only workspace/<task-id>/ runtime files and optionally active-task.md.",
            dry_run="Supported; previews planned task files.",
            yes="Required for actual writes.",
            example="python3.11 -m a2a_runtime.cli --project-root . task create --type feature --title \"新增设置页\" --priority P1 --owner zhangxia --yes",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    task_create.add_argument("--type", dest="task_type", required=True)
    task_create.add_argument("--title", required=True)
    task_create.add_argument("--priority", required=True)
    task_create.add_argument("--owner", required=True)
    task_create.add_argument("--task-id", dest="create_task_id")
    task_create.add_argument("--no-active", action="store_true")
    task_create.add_argument("--yes", action="store_true")
    task_create.add_argument("--dry-run", action="store_true")
    task_create.set_defaults(
        handler=lambda ctx, args: run_task_create(
            ctx,
            task_type=args.task_type,
            title=args.title,
            priority=args.priority,
            owner=args.owner,
            task_id=args.create_task_id or ctx.task_id,
            no_active=args.no_active,
            yes=args.yes,
            dry_run=args.dry_run,
        ),
    )
    task_list = task_sub.add_parser("list", help="List tasks")
    task_list.set_defaults(handler=lambda ctx, args: run_task_list(ctx))
    task_active = task_sub.add_parser("active", help="Show active task")
    task_active.set_defaults(handler=lambda ctx, args: run_task_active(ctx))
    task_use = task_sub.add_parser("use", help="Switch active task")
    task_use.add_argument("task_id")
    task_use.add_argument("--yes", action="store_true")
    task_use.add_argument("--dry-run", action="store_true")
    task_use.set_defaults(handler=lambda ctx, args: run_task_use(ctx, args.task_id, yes=args.yes, dry_run=args.dry_run))

    model = subparsers.add_parser(
        "model",
        help="Model recommendation commands",
        description=(
            "Show per-agent model recommendations. This CLI only recommends models; "
            "it never calls an LLM, switches Cursor models, or executes Codex."
        ),
        epilog=_help_epilog(
            "model",
            writes="Read-only; prints model policy and recommendations.",
            dry_run="Not needed.",
            yes="Not required.",
            example="python3.11 -m a2a_runtime.cli --project-root . model recommend --agent developer --tool codex",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    model_sub = model.add_subparsers(dest="model_command", required=True, parser_class=A2AArgumentParser)
    model_list = model_sub.add_parser("list", help="List default model policies")
    model_list.set_defaults(handler=lambda ctx, args: run_model_list(ctx))
    model_policy = model_sub.add_parser("policy", help="Show model policy safety rules")
    model_policy.set_defaults(handler=lambda ctx, args: run_model_policy(ctx))
    model_recommend = model_sub.add_parser("recommend", help="Recommend a model for one agent")
    model_recommend.add_argument("--agent", required=True, choices=["pm", "architect", "developer", "dev", "qa", "controller", "risk"])
    model_recommend.add_argument("--tool", default="generic", choices=["cursor", "codex", "generic"])
    model_recommend.add_argument("--risk", choices=["P0_BLOCKER", "P1_HIGH", "P2_MEDIUM", "P3_LOW", "INFO"])
    model_recommend.set_defaults(
        handler=lambda ctx, args: run_model_recommend(
            ctx,
            agent=args.agent,
            tool_context=args.tool,
            risk_level=args.risk,
        ),
    )

    prompt = subparsers.add_parser(
        "prompt",
        help="Generate an agent prompt",
        description="Generate Cursor-ready text prompts for PM, Architect, Developer, QA, or Controller.",
        epilog=_help_epilog(
            "prompt",
            writes="Read-only; generated prompts are printed to stdout.",
            dry_run="Not needed.",
            yes="Not required.",
            example="python3.11 -m a2a_runtime.cli --project-root . prompt developer --path src/pages/settings/index.tsx --operation modify",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    prompt.add_argument("role", choices=["pm", "architect", "developer", "qa", "controller", "dev"])
    prompt.add_argument("--path", dest="target_path")
    prompt.add_argument("--operation", choices=["create", "modify", "delete"])
    prompt.add_argument("--tool", default="cursor", choices=["cursor", "codex", "generic"])
    prompt.add_argument("--risk", choices=["P0_BLOCKER", "P1_HIGH", "P2_MEDIUM", "P3_LOW", "INFO"])
    prompt.set_defaults(
        handler=lambda ctx, args: run_prompt(
            ctx,
            args.role,
            target_path=args.target_path,
            operation=args.operation,
            tool_context=args.tool,
            risk_level=args.risk,
        ),
    )

    gate_cmd = subparsers.add_parser(
        "gate",
        help="Gate dry-run commands",
        description="Run read-only gate checks. Developer Gate never writes source, messages, or blockers from CLI.",
        epilog=_help_epilog(
            "gate",
            writes="Read-only dry-run checks.",
            dry_run="Always dry-run.",
            yes="Not required.",
            example="python3.11 -m a2a_runtime.cli --project-root . gate developer --path src/pages/settings/index.tsx --operation modify",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    gate_sub = gate_cmd.add_subparsers(dest="gate_command", required=True, parser_class=A2AArgumentParser)
    developer = gate_sub.add_parser("developer", help="Dry-run Developer Gate")
    developer.add_argument("--path", dest="target_path", required=True)
    developer.add_argument("--operation", choices=["create", "modify", "delete"], required=True)
    developer.set_defaults(
        handler=lambda ctx, args: run_gate_developer(
            ctx,
            target_path=args.target_path,
            operation=args.operation,
        ),
    )

    risk_cmd = subparsers.add_parser(
        "risk",
        help="Risk commands",
        description="Inspect risk findings, render human decision prompts, or record explicit human risk decisions.",
        epilog=_help_epilog(
            "risk",
            writes="risk list/show/review/prompt are read-only; risk decide writes decision messages and dispatch prompts.",
            dry_run="risk decide supports --dry-run.",
            yes="risk decide requires --yes to write.",
            example="python3.11 -m a2a_runtime.cli --project-root . risk review RISK-T-2026-001-001",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    risk_sub = risk_cmd.add_subparsers(dest="risk_command", required=True, parser_class=A2AArgumentParser)
    risk_list = risk_sub.add_parser("list", help="List risk findings")
    risk_list.set_defaults(handler=lambda ctx, args: run_risk_list(ctx))
    risk_show = risk_sub.add_parser("show", help="Show one risk finding")
    risk_show.add_argument("risk_id")
    risk_show.set_defaults(handler=lambda ctx, args: run_risk_show(ctx, args.risk_id))
    risk_review = risk_sub.add_parser("review", help="Show human decision options")
    risk_review.add_argument("risk_id")
    risk_review.set_defaults(handler=lambda ctx, args: run_risk_review(ctx, args.risk_id))
    risk_prompt = risk_sub.add_parser("prompt", help="Render read-only risk decision prompt")
    risk_prompt.add_argument("risk_id")
    risk_prompt.set_defaults(handler=lambda ctx, args: run_risk_prompt(ctx, args.risk_id))

    risk_decide = risk_sub.add_parser("decide", help="Record and apply a human risk decision")
    risk_decide.add_argument("risk_id")
    risk_decide.add_argument("--decision", required=True)
    risk_decide.add_argument("--reason", required=True)
    risk_decide.add_argument("--by", dest="decision_by", required=True)
    risk_decide.add_argument("--yes", action="store_true")
    risk_decide.add_argument("--dry-run", action="store_true")
    risk_decide.set_defaults(
        handler=lambda ctx, args: run_risk_decide(
            ctx,
            risk_id=args.risk_id,
            decision=args.decision,
            reason=args.reason,
            decision_by=args.decision_by,
            yes=args.yes,
            dry_run=args.dry_run,
        ),
    )

    review = subparsers.add_parser(
        "review",
        help="Human review proxy commands",
        description="Create human review records from an explicit reviewer handle and run review double-step flows.",
        epilog=_help_epilog(
            "review",
            writes="Writes human-reviews, state, and controller messages through ReviewService.",
            dry_run="Supported; previews planned review writes.",
            yes="Required for actual writes.",
            example="python3.11 -m a2a_runtime.cli --project-root . review approve --stage architect --step 1 --reviewer zhangxia --yes",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    review_sub = review.add_subparsers(dest="review_command", required=True, parser_class=A2AArgumentParser)
    for action in ["approve", "reject"]:
        review_cmd = review_sub.add_parser(
            action,
            help=f"{action} a review stage",
            description=f"{action.title()} an architect or final human review stage.",
            epilog=_help_epilog(
                f"review {action}",
                writes="Writes review records, state, and controller messages through ReviewService.",
                dry_run="Supported.",
                yes="Required for actual writes.",
                example=f"python3.11 -m a2a_runtime.cli --project-root . review {action} --stage architect --step 1 --reviewer zhangxia --yes",
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        review_cmd.add_argument("--stage", choices=["architect", "final"], required=True)
        review_cmd.add_argument("--step", choices=["1", "2"], help="Required for approve; Review double-step phase.")
        review_cmd.add_argument("--reviewer", required=True)
        review_cmd.add_argument("--reason")
        review_cmd.add_argument("--yes", action="store_true")
        review_cmd.add_argument("--dry-run", action="store_true")
        review_cmd.set_defaults(
            handler=lambda ctx, args, action=action: run_review(
                ctx,
                action=action,
                stage=args.stage,
                reviewer=args.reviewer,
                reason=args.reason,
                step=args.step,
                yes=args.yes,
                dry_run=args.dry_run,
            ),
        )

    blocker = subparsers.add_parser(
        "blocker",
        help="Blocker two-stage commands",
        description="Create blocker requests, Controller-only formal blockers, and resolve active blockers.",
        epilog=_help_epilog(
            "blocker",
            writes="request writes messages only; create/resolve write blockers/state/messages through BlockerService.",
            dry_run="All blocker mutating commands support --dry-run.",
            yes="Required for actual writes.",
            example="python3.11 -m a2a_runtime.cli --project-root . blocker request --from developer --reason \"missing artifact\" --resume-to-agent architect --resume-to-status architect_processing --required-fix \"update file-change-plan\" --yes",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    blocker_sub = blocker.add_subparsers(dest="blocker_command", required=True, parser_class=A2AArgumentParser)
    blocker_request = blocker_sub.add_parser(
        "request",
        help="Create a professional blocker_request message",
        description="Create a professional-agent blocker_request message. It does not create a formal blocker.",
        epilog=_help_epilog(
            "blocker request",
            writes="Writes only a blocker_request message.",
            dry_run="Supported.",
            yes="Required for actual writes.",
            example="python3.11 -m a2a_runtime.cli --project-root . blocker request --from developer --reason \"missing artifact\" --resume-to-agent architect --resume-to-status architect_processing --required-fix \"update file-change-plan\" --yes",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    blocker_request.add_argument("--from", dest="from_agent", required=True)
    blocker_request.add_argument("--reason", required=True)
    blocker_request.add_argument("--resume-to-agent", required=True)
    blocker_request.add_argument("--resume-to-status", required=True)
    blocker_request.add_argument("--missing-artifact", action="append", dest="missing_artifacts", default=[])
    blocker_request.add_argument("--required-fix", required=True)
    blocker_request.add_argument("--yes", action="store_true")
    blocker_request.add_argument("--dry-run", action="store_true")
    blocker_request.set_defaults(
        handler=lambda ctx, args: run_blocker_request(
            ctx,
            from_agent=args.from_agent,
            reason=args.reason,
            resume_to_agent=args.resume_to_agent,
            resume_to_status=args.resume_to_status,
            missing_artifacts=args.missing_artifacts,
            required_fix=args.required_fix,
            yes=args.yes,
            dry_run=args.dry_run,
        ),
    )
    blocker_create = blocker_sub.add_parser(
        "create",
        help="Create a formal blocker from blocker_request",
        description="Controller-only creation of a formal blocker from a blocker_request message.",
        epilog=_help_epilog(
            "blocker create",
            writes="Writes blockers, state, and controller messages through BlockerService.",
            dry_run="Supported.",
            yes="Required for actual writes.",
            example="python3.11 -m a2a_runtime.cli --project-root . blocker create --from-request M-T-2026-001-008 --yes",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    blocker_create.add_argument("--from-request", required=True)
    blocker_create.add_argument("--yes", action="store_true")
    blocker_create.add_argument("--dry-run", action="store_true")
    blocker_create.set_defaults(
        handler=lambda ctx, args: run_blocker_create(
            ctx,
            from_request=args.from_request,
            yes=args.yes,
            dry_run=args.dry_run,
        ),
    )
    blocker_resolve = blocker_sub.add_parser(
        "resolve",
        help="Resolve an active formal blocker",
        description="Resolve the active formal blocker after missing artifacts are confirmed resolved.",
        epilog=_help_epilog(
            "blocker resolve",
            writes="Writes state and controller handoff messages through BlockerService.",
            dry_run="Supported.",
            yes="Required for actual writes.",
            example="python3.11 -m a2a_runtime.cli --project-root . blocker resolve B-T-2026-001-001 --missing-artifacts-resolved --yes",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    blocker_resolve.add_argument("blocker_id")
    blocker_resolve.add_argument("--missing-artifacts-resolved", action="store_true")
    blocker_resolve.add_argument("--resume-to-agent")
    blocker_resolve.add_argument("--resume-to-status")
    blocker_resolve.add_argument("--yes", action="store_true")
    blocker_resolve.add_argument("--dry-run", action="store_true")
    blocker_resolve.set_defaults(
        handler=lambda ctx, args: run_blocker_resolve(
            ctx,
            blocker_id=args.blocker_id,
            missing_artifacts_resolved=args.missing_artifacts_resolved,
            resume_to_agent=args.resume_to_agent,
            resume_to_status=args.resume_to_status,
            yes=args.yes,
            dry_run=args.dry_run,
        ),
    )

    finalize = subparsers.add_parser(
        "finalize",
        help="Write final delivery when all gates pass",
        description="Validate final-delivery gates and write final-delivery only when safe.",
        epilog=_help_epilog(
            "finalize",
            writes="Writes only final-delivery and final controller message after FinalDeliveryService gates pass.",
            dry_run="Supported; previews gate result.",
            yes="Required for actual writes.",
            example="python3.11 -m a2a_runtime.cli --project-root . finalize --yes",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    finalize.add_argument("--yes", action="store_true")
    finalize.add_argument("--dry-run", action="store_true")
    finalize.set_defaults(handler=lambda ctx, args: run_finalize(ctx, yes=args.yes, dry_run=args.dry_run))

    report = subparsers.add_parser(
        "report",
        help="Print or export a runtime report",
        description="Print a read-only runtime report, or safely export it into the task archive.",
        epilog=_help_epilog(
            "report",
            writes="Read-only by default. With --output archive/<file>.md, writes only to the current task archive.",
            dry_run="Supported for --output.",
            yes="Required when --output writes a report file.",
            example="python3.11 -m a2a_runtime.cli --project-root . report --output archive/runtime-report.md --yes",
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    report.add_argument("--output", help="Optional archive-relative export path, e.g. archive/runtime-report.md")
    report.add_argument("--yes", action="store_true")
    report.add_argument("--dry-run", action="store_true")
    report.set_defaults(handler=lambda ctx, args: run_report(ctx, output=args.output, yes=args.yes, dry_run=args.dry_run))
    return parser


def _help_epilog(command: str, *, writes: str, dry_run: str, yes: str, example: str) -> str:
    return f"""Safety:
  - A2A Runtime does not automatically modify business source code.
  - A2A Runtime does not call a real LLM.
  - Developer source edits still need Cursor execution and remain constrained by GateService.

Workspace writes: {writes}
Business source writes: never.
--dry-run: {dry_run}
--yes: {yes}

Example:
  {example}
"""


def _extract_global_options(argv: list[str]) -> tuple[dict[str, object], list[str]]:
    options: dict[str, object] = {
        "project_root": ".",
        "task_id": None,
        "json": False,
        "verbose": False,
        "allow_non_project_root": False,
    }
    stripped: list[str] = []
    index = 0
    while index < len(argv):
        item = argv[index]
        if item == "--project-root":
            if index + 1 >= len(argv):
                stripped.append(item)
            else:
                options["project_root"] = argv[index + 1]
                index += 1
        elif item.startswith("--project-root="):
            options["project_root"] = item.split("=", 1)[1]
        elif item == "--task-id":
            if index + 1 >= len(argv):
                stripped.append(item)
            else:
                options["task_id"] = argv[index + 1]
                index += 1
        elif item.startswith("--task-id="):
            options["task_id"] = item.split("=", 1)[1]
        elif item == "--json":
            options["json"] = True
        elif item == "--verbose":
            options["verbose"] = True
        elif item == "--allow-non-project-root":
            options["allow_non_project_root"] = True
        else:
            stripped.append(item)
        index += 1
    return options, stripped


def _emit(result: CLIResult, *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(result.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        return
    if not result.ok:
        error = normalize_error(result.errors[0] if result.errors else "command failed", result.exit_code, result.command)
        print(format_error_text(result.command, result.exit_code, error), end="")
        return
    text = result.text or f"[A2A CLI]\nCommand: {result.command}\nOK: {str(result.ok).lower()}\n"
    print(text, end="" if text.endswith("\n") else "\n")


if __name__ == "__main__":
    raise SystemExit(main())
