"""Shared CLI helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
import tempfile
from pathlib import Path
from typing import Any

from a2a_runtime.core import frontmatter
from a2a_runtime.core.constants import ArtifactType
from a2a_runtime.core.errors import A2ARuntimeError, RepositoryError, SchemaError, TaskIdentityError
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.file_change_plan import FileChangePlan, FileChangePlanEntry
from a2a_runtime.repositories.artifact_repo import ArtifactRepo
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.risk_repo import RiskRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.repositories.task_repo import TaskRepo
from a2a_runtime.repositories.workspace_repo import WorkspaceRepo
from a2a_runtime.services.task_identity_service import TaskIdentityService

EXIT_SUCCESS = 0
EXIT_VALIDATION_FAILED = 1
EXIT_USER_DECISION_REQUIRED = 2
EXIT_TASK_NOT_FOUND = 3
EXIT_INVALID_ARGS = 4
EXIT_INTERNAL_ERROR = 5


@dataclass(frozen=True)
class CLIContext:
    project_root: Path
    task_id: str | None = None
    json_output: bool = False
    verbose: bool = False
    root_warnings: list[str] = field(default_factory=list)

    @property
    def paths(self) -> A2APaths:
        return A2APaths(self.project_root)

    @property
    def workspace_repo(self) -> WorkspaceRepo:
        return WorkspaceRepo(self.paths)

    @property
    def task_repo(self) -> TaskRepo:
        return TaskRepo(self.paths)

    @property
    def state_repo(self) -> StateRepo:
        return StateRepo(self.paths)

    @property
    def artifact_repo(self) -> ArtifactRepo:
        return ArtifactRepo(self.paths)

    @property
    def message_repo(self) -> MessageRepo:
        return MessageRepo(self.paths)

    @property
    def risk_repo(self) -> RiskRepo:
        return RiskRepo(self.message_repo)

    def resolve_task_id(self) -> str:
        return TaskIdentityService(self.workspace_repo).resolve_task_id(self.task_id)


@dataclass(frozen=True)
class CLIError:
    code: str
    message: str
    suggested_next_action: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "message": self.message,
            "suggested_next_action": self.suggested_next_action,
        }


@dataclass
class CLIResult:
    ok: bool
    command: str
    exit_code: int = EXIT_SUCCESS
    task_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str | CLIError | dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    written_files: list[str] = field(default_factory=list)
    text: str = ""

    def to_json_dict(self) -> dict[str, Any]:
        payload = {
            "ok": self.ok,
            "command": self.command,
            "task_id": self.task_id,
            "written_files": [] if self.data.get("dry_run") is True else list(self.written_files),
            "errors": [normalize_error(error, self.exit_code, self.command).to_dict() for error in self.errors],
            "warnings": list(self.warnings),
        }
        payload.update(self.data)
        if payload.get("dry_run") is True:
            payload["written_files"] = []
            if "planned_writes" not in payload and "planned_files" in payload:
                payload["planned_writes"] = payload["planned_files"]
        return payload


def error_result(command: str, message: str, exit_code: int, *, task_id: str | None = None) -> CLIResult:
    error = build_error(message, exit_code, command)
    return CLIResult(
        ok=False,
        command=command,
        exit_code=exit_code,
        task_id=task_id,
        errors=[error],
        text=format_error_text(command, exit_code, error),
    )


def require_write_confirmation(command: str, *, yes: bool, dry_run: bool, task_id: str | None = None) -> CLIResult | None:
    if yes or dry_run:
        return None
    return CLIResult(
        ok=False,
        command=command,
        exit_code=EXIT_USER_DECISION_REQUIRED,
        task_id=task_id,
        errors=[build_error("mutating command requires --yes or --dry-run", EXIT_USER_DECISION_REQUIRED, command)],
        data={"dry_run": False, "requires_yes": True},
        text=format_error_text(
            command,
            EXIT_USER_DECISION_REQUIRED,
            build_error("mutating command requires --yes or --dry-run", EXIT_USER_DECISION_REQUIRED, command),
        ),
    )


def task_error_result(command: str, exc: Exception) -> CLIResult:
    code = EXIT_TASK_NOT_FOUND if isinstance(exc, TaskIdentityError) else EXIT_INTERNAL_ERROR
    return error_result(command, str(exc), code)


def error_code_for_exit(exit_code: int) -> str:
    return {
        EXIT_VALIDATION_FAILED: "VALIDATION_FAILED",
        EXIT_USER_DECISION_REQUIRED: "USER_DECISION_REQUIRED",
        EXIT_TASK_NOT_FOUND: "TASK_NOT_FOUND",
        EXIT_INVALID_ARGS: "INVALID_ARGS",
        EXIT_INTERNAL_ERROR: "INTERNAL_ERROR",
    }.get(exit_code, "ERROR")


def project_markers(project_root: Path) -> dict[str, bool]:
    return {
        ".ai-agents": (project_root / ".ai-agents").is_dir(),
        ".git": (project_root / ".git").exists(),
        "pyproject.toml": (project_root / "pyproject.toml").is_file(),
        "package.json": (project_root / "package.json").is_file(),
    }


def validate_project_root_safety(
    project_root: Path,
    *,
    allow_non_project_root: bool = False,
) -> list[str]:
    resolved = project_root.expanduser().resolve()
    sensitive = [
        Path("/").resolve(),
        Path("/etc").resolve(),
        Path("/usr").resolve(),
        Path("/var").resolve(),
        Path("/private").resolve(),
        Path("/System").resolve(),
        Path("/Library").resolve(),
        (Path.home() / "Library").resolve(),
    ]
    if _is_under_sensitive_project_root(resolved, sensitive):
        raise SchemaError(f"unsafe --project-root refused: {resolved}")
    markers = project_markers(resolved)
    if not any(markers.values()):
        if allow_non_project_root:
            return [f"--project-root has no project markers: {resolved}"]
        raise SchemaError(
            "--project-root must contain at least one project marker: .ai-agents/, .git/, pyproject.toml, or package.json",
        )
    return []


def _is_under_sensitive_project_root(path: Path, sensitive_roots: list[Path]) -> bool:
    allowed_temp = Path(tempfile.gettempdir()).resolve()
    for root in sensitive_roots:
        if root == Path("/").resolve():
            if path == root:
                return True
            continue
        try:
            path.relative_to(root)
        except ValueError:
            continue
        if _is_allowed_user_temp(path, allowed_temp):
            return False
        return True
    return False


def _is_allowed_user_temp(path: Path, allowed_temp: Path) -> bool:
    try:
        path.relative_to(allowed_temp)
        return True
    except ValueError:
        return False


def suggested_next_action(exit_code: int, command: str, message: str) -> str:
    lowered = message.lower()
    if exit_code == EXIT_TASK_NOT_FOUND:
        return "Run a2a-agent task list, task active, or task use <task_id>."
    if exit_code == EXIT_USER_DECISION_REQUIRED:
        if "--yes" in message or "--dry-run" in message:
            return "Re-run with --dry-run to preview or --yes to apply the workspace write."
        return "Review the pending human decision and record an explicit choice."
    if exit_code == EXIT_VALIDATION_FAILED:
        if "unresolved blocking risk" in lowered or "p0/p1" in lowered:
            return "Resolve or decide blocking risks before continuing."
        return "Run a2a-agent validate for details and fix the reported inputs."
    if exit_code == EXIT_INVALID_ARGS:
        return f"Run a2a-agent {command} --help and correct the command arguments."
    return "Re-run with --verbose or inspect the runtime files for details."


def build_error(message: str, exit_code: int, command: str) -> CLIError:
    return CLIError(
        code=error_code_for_exit(exit_code),
        message=message,
        suggested_next_action=suggested_next_action(exit_code, command, message),
    )


def normalize_error(error: str | CLIError | dict[str, Any], exit_code: int, command: str) -> CLIError:
    if isinstance(error, CLIError):
        return error
    if isinstance(error, dict):
        return CLIError(
            code=str(error.get("code") or error_code_for_exit(exit_code)),
            message=str(error.get("message") or ""),
            suggested_next_action=str(
                error.get("suggested_next_action")
                or suggested_next_action(exit_code, command, str(error.get("message") or "")),
            ),
        )
    return build_error(str(error), exit_code, command)


def format_error_text(command: str, exit_code: int, error: str | CLIError | dict[str, Any]) -> str:
    normalized = normalize_error(error, exit_code, command)
    return (
        "[A2A CLI Error]\n"
        f"Command: {command}\n"
        f"Exit Code: {exit_code}\n"
        f"Reason: {normalized.message}\n"
        f"Suggested Next Action: {normalized.suggested_next_action}\n"
    )


def load_file_change_plan(ctx: CLIContext, task_id: str) -> FileChangePlan:
    artifact = ctx.artifact_repo.find_artifact(task_id, ArtifactType.FILE_CHANGE_PLAN)
    if artifact is None:
        return FileChangePlan([])
    path = ctx.paths.task_dir(task_id) / artifact.file_path
    try:
        document = frontmatter.load(path)
    except (OSError, A2ARuntimeError):
        return FileChangePlan([])
    raw_entries = document.data.get("entries")
    if isinstance(raw_entries, list):
        entries = []
        for item in raw_entries:
            if isinstance(item, dict):
                try:
                    entries.append(FileChangePlanEntry.from_dict(item))
                except SchemaError:
                    continue
        return FileChangePlan(entries)
    return FileChangePlan(_parse_entries_from_body(document.body))


def _parse_entries_from_body(body: str) -> list[FileChangePlanEntry]:
    entries: list[FileChangePlanEntry] = []
    current: dict[str, object] | None = None
    for raw_line in body.splitlines():
        line = raw_line.strip().strip("|").strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- path:"):
            if current:
                _append_entry(entries, current)
            current = {"path": line.split(":", 1)[1].strip()}
            continue
        if current is not None and ":" in line:
            key, value = line.split(":", 1)
            current[key.strip()] = _coerce_value(key.strip(), value.strip())
    if current:
        _append_entry(entries, current)
    return entries


def _append_entry(entries: list[FileChangePlanEntry], data: dict[str, object]) -> None:
    try:
        entries.append(FileChangePlanEntry.from_dict(data))
    except SchemaError:
        return


def _coerce_value(key: str, value: str) -> object:
    if key == "allowed":
        return value.lower() in {"true", "yes", "y", "1"}
    return value


def safe_count_paths(paths: list[Path]) -> int:
    return sum(1 for path in paths if path.exists())


def read_optional_task_state(ctx: CLIContext, task_id: str) -> tuple[Any | None, Any | None, list[str]]:
    warnings: list[str] = []
    task = None
    state = None
    try:
        task = ctx.task_repo.read(task_id)
    except (RepositoryError, SchemaError) as exc:
        warnings.append(str(exc))
    try:
        state = ctx.state_repo.read(task_id)
    except (RepositoryError, SchemaError) as exc:
        warnings.append(str(exc))
    return task, state, warnings
