"""Developer write gate checks and failure message helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Iterable

from a2a_runtime.core.clock import Clock
from a2a_runtime.core.constants import (
    DEFAULT_FORBIDDEN_WRITE_PATHS,
    FileOperation,
    GateFailureType,
    MessageType,
    ReviewStatus,
    RiskCategory,
    RiskDecisionAction,
    RiskSeverity,
    Role,
    TaskStatus,
    parse_enum,
    role_to_wire,
)
from a2a_runtime.core.errors import GateError, SchemaError
from a2a_runtime.models.file_change_plan import FileChangePlan, FileChangePlanEntry
from a2a_runtime.models.message import Message
from a2a_runtime.models.state import State
from a2a_runtime.repositories.message_repo import MessageRepo


@dataclass(frozen=True)
class GateCheckResult:
    allowed: bool
    failure_type: GateFailureType
    failed_conditions: list[str]
    reason: str
    recommended_next_action: str


class GateService:
    def __init__(self, message_repo: MessageRepo | None = None, clock: Clock | None = None) -> None:
        self.message_repo = message_repo
        self.clock = clock or Clock()

    def check_developer_write(
        self,
        *,
        state: State,
        target_path: str,
        operation: FileOperation | str,
        file_change_plan: FileChangePlan | Iterable[FileChangePlanEntry],
        changed_files_audit_available: bool = True,
    ) -> GateCheckResult:
        try:
            parsed_operation = parse_enum(FileOperation, operation, "operation")
        except SchemaError:
            return self._blocker_request(
                ["operation_invalid"],
                "operation must be create, modify, or delete",
            )

        if state.current_status != TaskStatus.DEVELOPER_PROCESSING:
            return self._gate_failure(
                ["current_status_not_developer_processing"],
                "state.current_status must be developer_processing before writing code",
            )
        if state.human_review_status != ReviewStatus.APPROVED:
            return self._gate_failure(
                ["human_review_status_not_approved"],
                "human_review_status must be approved before developer writes code",
            )
        if state.current_agent != Role.DEVELOPER:
            return self._gate_failure(
                ["current_agent_not_developer"],
                "state.current_agent must be developer",
            )

        normalized_path = self._normalize_target_path(target_path)
        if normalized_path.error is not None:
            return GateCheckResult(
                allowed=False,
                failure_type=GateFailureType.RISK_DECISION_REQUIRED,
                failed_conditions=[normalized_path.error],
                reason=normalized_path.reason or "target path is not safe",
                recommended_next_action="stop; use a project-relative path inside the task scope",
            )

        entries = self._entries(file_change_plan)
        path_entries = [
            entry
            for entry in entries
            if self._normalize_target_path(entry.path).path == normalized_path.path
        ]
        matching_entry = next(
            (entry for entry in path_entries if entry.operation == parsed_operation),
            None,
        )

        forbidden = self._default_forbidden_reason(normalized_path.path)
        if forbidden is not None:
            if (
                not matching_entry
                or not matching_entry.allowed
                or matching_entry.owner != "user-approved"
            ):
                return GateCheckResult(
                    allowed=False,
                    failure_type=GateFailureType.RISK_DECISION_REQUIRED,
                    failed_conditions=[forbidden],
                    reason=f"target path is in the default forbidden set: {forbidden}",
                    recommended_next_action="stop and ask user to make a risk decision",
                )
            return GateCheckResult(
                allowed=False,
                failure_type=GateFailureType.RISK_DECISION_REQUIRED,
                failed_conditions=[forbidden, "explicit_user_approved_forbidden_path"],
                reason="default forbidden path has user-approved file-change-plan entry and still requires Human Risk Decision Gate",
                recommended_next_action="record an explicit human risk decision before writing this path",
            )

        if not path_entries:
            return self._blocker_request(
                ["target_path_missing_from_file_change_plan"],
                "target path is not in file-change-plan",
            )
        if matching_entry is None:
            return self._blocker_request(
                ["operation_mismatch"],
                "target path exists in file-change-plan but operation does not match",
            )
        if not matching_entry.allowed:
            return self._blocker_request(
                ["file_change_plan_entry_not_allowed"],
                "file-change-plan entry is not allowed",
            )
        if parsed_operation.value == "delete" and not matching_entry.reason.strip():
            return self._blocker_request(
                ["delete_missing_reason"],
                "delete operation requires a non-empty reason",
            )
        if not changed_files_audit_available:
            return self._blocker_request(
                ["changed_files_audit_unavailable"],
                "actual change must be auditable in changed-files.md",
            )

        return GateCheckResult(
            allowed=True,
            failure_type=GateFailureType.NONE,
            failed_conditions=[],
            reason="developer write gate passed",
            recommended_next_action="proceed with the planned write and record changed-files audit",
        )

    def create_gate_failure_message(
        self,
        *,
        task_id: str,
        state: State,
        gate_result: GateCheckResult,
        attempted_operation: str,
        target_path: str,
        body: str = "",
    ) -> Message:
        if self.message_repo is None:
            raise GateError("message_repo is required to write gate_failure messages")
        if gate_result.failure_type != GateFailureType.GATE_FAILURE:
            raise GateError("gate_result must be gate_failure")
        seq = self.message_repo.next_sequence(task_id)
        message = Message(
            message_id=f"M-{task_id}-{seq:03d}",
            task_id=task_id,
            from_agent=Role.DEVELOPER,
            to_agent=Role.CONTROLLER,
            message_type=MessageType.GATE_FAILURE,
            intent="write_gate_failed",
            summary=gate_result.reason,
            payload={
                "five_gate_conditions": {
                    "state_status": state.current_status == TaskStatus.DEVELOPER_PROCESSING,
                    "human_review": state.human_review_status == ReviewStatus.APPROVED,
                    "current_agent": state.current_agent == Role.DEVELOPER,
                    "file_change_plan": "target_path_missing_from_file_change_plan"
                    not in gate_result.failed_conditions
                    and "operation_mismatch" not in gate_result.failed_conditions
                    and "file_change_plan_entry_not_allowed" not in gate_result.failed_conditions,
                    "default_forbidden": "target_path_default_forbidden"
                    not in gate_result.failed_conditions,
                },
                "tool": "gate_service",
                "reason_for_user": gate_result.reason,
                "attempted_action": {
                    "operation": attempted_operation,
                    "target_path": target_path,
                },
                "state_at_attempt": {
                    "current_status": state.current_status.value,
                    "human_review_status": state.human_review_status.value,
                    "final_review_status": state.final_review_status.value,
                    "current_agent": role_to_wire(state.current_agent),
                },
                "failed_conditions": list(gate_result.failed_conditions),
                "recommended_next_action": gate_result.recommended_next_action,
                "target_path": target_path,
                "operation": attempted_operation,
                "decision": "refuse_to_write",
                "controller_action_required": "none",
            },
            referenced_artifacts=[],
            required_response=False,
            blockers=[],
            created_at=self.clock.now_iso(),
        )
        self.message_repo.write_message(message, body)
        return message

    def build_risk_finding_kwargs(
        self,
        *,
        task_id: str,
        gate_result: GateCheckResult,
        target_path: str,
    ) -> dict[str, object]:
        if gate_result.failure_type != GateFailureType.RISK_DECISION_REQUIRED:
            raise GateError("gate_result must be risk_decision_required")
        return {
            "task_id": task_id,
            "source_agent": Role.CONTROLLER,
            "category": self._risk_category_for_path(target_path),
            "severity": RiskSeverity.P1_HIGH,
            "title": f"Developer write needs human risk decision: {target_path}",
            "description": gate_result.reason,
            "evidence": "; ".join(gate_result.failed_conditions) or gate_result.reason,
            "affected_files": [target_path],
            "affected_artifacts": ["file_change_plan", "changed_files"],
            "recommended_options": [
                RiskDecisionAction.SEND_TO_ARCHITECT.value,
                RiskDecisionAction.CONVERT_TO_BLOCKER.value,
                RiskDecisionAction.ACCEPT_RISK_AND_CONTINUE.value,
                RiskDecisionAction.CANCEL_TASK.value,
            ],
            "default_recommendation": RiskDecisionAction.SEND_TO_ARCHITECT.value,
        }

    def _gate_failure(self, failed_conditions: list[str], reason: str) -> GateCheckResult:
        return GateCheckResult(
            allowed=False,
            failure_type=GateFailureType.GATE_FAILURE,
            failed_conditions=failed_conditions,
            reason=reason,
            recommended_next_action="write gate_failure message; do not change state",
        )

    def _blocker_request(self, failed_conditions: list[str], reason: str) -> GateCheckResult:
        return GateCheckResult(
            allowed=False,
            failure_type=GateFailureType.BLOCKER_REQUEST,
            failed_conditions=failed_conditions,
            reason=reason,
            recommended_next_action="write blocker_request message; wait for controller",
        )

    def _entries(
        self,
        file_change_plan: FileChangePlan | Iterable[FileChangePlanEntry],
    ) -> list[FileChangePlanEntry]:
        if isinstance(file_change_plan, FileChangePlan):
            return list(file_change_plan.entries)
        return list(file_change_plan)

    def _default_forbidden_reason(self, target_path: str) -> str | None:
        parts = [part.lower() for part in PurePosixPath(target_path).parts]
        basename = parts[-1] if parts else ""
        ci_cd_dirs = {".github", ".circleci", ".buildkite"}
        dependency_files = {
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "bun.lock",
            "bun.lockb",
        }
        if basename in dependency_files:
            return "forbidden dependency file"
        if basename == "dockerfile" or basename.startswith("dockerfile."):
            return "forbidden docker file"
        if any(part in ci_cd_dirs for part in parts):
            return "forbidden ci/cd file"
        if basename in {
            ".gitlab-ci.yml",
            "azure-pipelines.yml",
            "bitbucket-pipelines.yml",
            "jenkinsfile",
        }:
            return "forbidden ci/cd file"
        return None

    def _risk_category_for_path(self, target_path: str) -> RiskCategory:
        normalized_result = self._normalize_target_path(target_path)
        normalized = normalized_result.path or target_path.replace("\\", "/")
        parts = [part.lower() for part in PurePosixPath(normalized).parts]
        basename = parts[-1] if parts else ""
        if basename in {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"}:
            return RiskCategory.DEPENDENCY
        if self._default_forbidden_reason(normalized) == "forbidden ci/cd file":
            return RiskCategory.CI_CD
        return RiskCategory.SCOPE

    def _is_default_forbidden(self, target_path: str) -> bool:
        normalized = self._normalize_target_path(target_path)
        if normalized.error is not None:
            return True
        return self._default_forbidden_reason(normalized.path) is not None

    def _normalize_target_path(self, target_path: str) -> "_NormalizedPath":
        raw = str(target_path).strip()
        if not raw:
            return _NormalizedPath("", "target_path_empty", "target path is required")
        if len(raw) >= 2 and raw[1] == ":" and raw[0].isalpha():
            return _NormalizedPath("", "absolute path", "windows absolute paths are not allowed")
        replaced = raw.replace("\\", "/")
        if replaced.startswith("/"):
            return _NormalizedPath("", "absolute path", "absolute paths are not allowed")
        path = PurePosixPath(replaced)
        if any(part == ".." for part in path.parts):
            return _NormalizedPath("", "path traversal", "path traversal using .. is not allowed")
        normalized = "/".join(part for part in path.parts if part not in {"", "."})
        if not normalized:
            return _NormalizedPath("", "target_path_empty", "target path is required")
        return _NormalizedPath(normalized, None, None)


@dataclass(frozen=True)
class _NormalizedPath:
    path: str
    error: str | None
    reason: str | None
