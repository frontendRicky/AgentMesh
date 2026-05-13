"""Protocol constants and enums for A2A v1 runtime files."""

from __future__ import annotations

from enum import StrEnum
from typing import TypeVar

from a2a_runtime.core.errors import SchemaError

SCHEMA_VERSION = "a2a/v1"

TASK_ID_PATTERN = r"^T-\d{4}-\d{3}$"
MESSAGE_ID_PATTERN = r"^M-T-\d{4}-\d{3}-\d{3}$"
ARTIFACT_ID_PATTERN = r"^A-T-\d{4}-\d{3}-[a-z_]+$"
BLOCKER_ID_PATTERN = r"^B-T-\d{4}-\d{3}-\d{3}$"
REVIEW_ID_PATTERN = r"^R-T-\d{4}-\d{3}-(architect|final)$"
RISK_ID_PATTERN = r"^RISK-T-\d{4}-\d{3}-\d{3}$"
RISK_DECISION_ID_PATTERN = r"^RD-T-\d{4}-\d{3}-\d{3}$"
HANDOFF_CONTRACT_ID_PATTERN = r"^HC-[a-z-]+-to-[a-z-]+$"

TASK_STATIC_FIELDS = {
    "task_id",
    "task_type",
    "task_title",
    "created_by",
    "human_owner",
    "priority",
    "scope",
    "constraints",
    "initial_input_messages",
    "required_artifacts",
    "created_at",
    "schema_version",
}

TASK_DYNAMIC_FIELDS = {
    "task_status",
    "current_status",
    "previous_status",
    "current_agent",
    "next_agent",
    "human_review_status",
    "final_review_status",
    "produced_artifacts",
    "blockers",
    "checkpoints",
    "final_status",
    "updated_at",
}

DEFAULT_FORBIDDEN_WRITE_PATHS = (
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lock",
    "bun.lockb",
    ".github/**",
    ".gitlab-ci.yml",
    ".circleci/**",
    ".buildkite/**",
    "azure-pipelines.yml",
    "bitbucket-pipelines.yml",
    "Jenkinsfile",
    "Dockerfile",
)


class Role(StrEnum):
    """Canonical writable role enum.

    The runtime accepts the legacy input alias ``dev`` on read, but all model
    serialization writes ``developer``.
    """

    PM = "pm"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    QA = "qa"
    CONTROLLER = "controller"
    HUMAN = "human"


ROLE_ALIASES = {"dev": Role.DEVELOPER}


class TaskType(StrEnum):
    FEATURE = "feature"
    REFACTOR = "refactor"
    BUGFIX = "bugfix"
    UI_REDESIGN = "ui-redesign"
    PERMISSION = "permission"
    API_INTEGRATION = "api-integration"


class TaskPriority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class TaskStatus(StrEnum):
    CREATED = "created"
    PM_PROCESSING = "pm_processing"
    PM_COMPLETED = "pm_completed"
    ARCHITECT_PROCESSING = "architect_processing"
    ARCHITECT_COMPLETED = "architect_completed"
    HUMAN_REVIEW_REQUIRED = "human_review_required"
    DEVELOPER_PROCESSING = "developer_processing"
    DEVELOPER_COMPLETED = "developer_completed"
    QA_PROCESSING = "qa_processing"
    QA_COMPLETED = "qa_completed"
    FINAL_REVIEW_REQUIRED = "final_review_required"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


ALLOWED_TASK_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.CREATED: {TaskStatus.PM_PROCESSING, TaskStatus.CANCELLED},
    TaskStatus.PM_PROCESSING: {TaskStatus.PM_COMPLETED, TaskStatus.BLOCKED, TaskStatus.CANCELLED},
    TaskStatus.PM_COMPLETED: {TaskStatus.ARCHITECT_PROCESSING, TaskStatus.CANCELLED},
    TaskStatus.ARCHITECT_PROCESSING: {
        TaskStatus.ARCHITECT_COMPLETED,
        TaskStatus.BLOCKED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.ARCHITECT_COMPLETED: {TaskStatus.HUMAN_REVIEW_REQUIRED, TaskStatus.CANCELLED},
    TaskStatus.HUMAN_REVIEW_REQUIRED: {
        TaskStatus.ARCHITECT_PROCESSING,
        TaskStatus.DEVELOPER_PROCESSING,
        TaskStatus.CANCELLED,
    },
    TaskStatus.DEVELOPER_PROCESSING: {
        TaskStatus.DEVELOPER_COMPLETED,
        TaskStatus.BLOCKED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.DEVELOPER_COMPLETED: {TaskStatus.QA_PROCESSING, TaskStatus.CANCELLED},
    TaskStatus.QA_PROCESSING: {TaskStatus.QA_COMPLETED, TaskStatus.BLOCKED, TaskStatus.CANCELLED},
    TaskStatus.QA_COMPLETED: {TaskStatus.FINAL_REVIEW_REQUIRED, TaskStatus.CANCELLED},
    TaskStatus.FINAL_REVIEW_REQUIRED: {
        TaskStatus.DEVELOPER_PROCESSING,
        TaskStatus.COMPLETED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.BLOCKED: {
        TaskStatus.PM_PROCESSING,
        TaskStatus.ARCHITECT_PROCESSING,
        TaskStatus.DEVELOPER_PROCESSING,
        TaskStatus.QA_PROCESSING,
        TaskStatus.CANCELLED,
    },
    TaskStatus.COMPLETED: set(),
    TaskStatus.CANCELLED: set(),
}

TERMINAL_TASK_STATUSES = {TaskStatus.COMPLETED, TaskStatus.CANCELLED}


class ReviewStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MessageType(StrEnum):
    REQUEST = "request"
    RESPONSE = "response"
    HANDOFF = "handoff"
    REVIEW = "review"
    BLOCKER = "blocker"
    GATE_FAILURE = "gate_failure"
    STATUS = "status"
    FINAL = "final"


class QAStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    BLOCKED = "blocked"
    NOT_EXECUTED = "not_executed"
    MANUAL_REQUIRED = "manual_required"


class ArtifactType(StrEnum):
    REQUIREMENT = "requirement"
    PRD = "prd"
    BUG_BRIEF = "bug_brief"
    REGRESSION_SCOPE = "regression_scope"
    TASK_BREAKDOWN = "task_breakdown"
    TECH_PLAN = "tech_plan"
    FILE_CHANGE_PLAN = "file_change_plan"
    QA_FILE_CHANGE_PLAN = "qa_file_change_plan"
    RISK_PLAN = "risk_plan"
    IMPLEMENTATION_LOG = "implementation_log"
    CHANGED_FILES = "changed_files"
    TEST_REPORT = "test_report"
    ACCEPTANCE_CHECKLIST = "acceptance_checklist"
    HUMAN_REVIEW_RECORD = "human_review_record"
    FINAL_REVIEW_RECORD = "final_review_record"
    FINAL_DELIVERY = "final_delivery"


class ArtifactStatus(StrEnum):
    DRAFT = "draft"
    READY = "ready"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class ValidationOutcome(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    PENDING = "pending"


class ReviewType(StrEnum):
    ARCHITECT_REVIEW = "architect_review"
    FINAL_REVIEW = "final_review"


class ReviewVerdict(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CHANGES = "needs_changes"


class ReviewIssueSeverity(StrEnum):
    BLOCKER = "blocker"
    MAJOR = "major"
    MINOR = "minor"


class FileOperation(StrEnum):
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"


class GateFailureType(StrEnum):
    NONE = "none"
    GATE_FAILURE = "gate_failure"
    BLOCKER_REQUEST = "blocker_request"
    RISK_DECISION_REQUIRED = "risk_decision_required"


class RiskSeverity(StrEnum):
    P0_BLOCKER = "P0_BLOCKER"
    P1_HIGH = "P1_HIGH"
    P2_MEDIUM = "P2_MEDIUM"
    P3_LOW = "P3_LOW"
    INFO = "INFO"


class RiskCategory(StrEnum):
    SCOPE = "scope"
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    PERMISSION = "permission"
    SECURITY = "security"
    RUNTIME = "runtime"
    DATA = "data"
    DEPENDENCY = "dependency"
    CI_CD = "ci_cd"
    TESTING = "testing"
    ROLLBACK = "rollback"
    HANDOFF = "handoff"
    REVIEW = "review"
    UNKNOWN = "unknown"


class RiskStatus(StrEnum):
    OPEN = "open"
    WAITING_HUMAN_DECISION = "waiting_human_decision"
    PENDING_MANUAL_REVIEW = "pending_manual_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CONVERTED_TO_BLOCKER = "converted_to_blocker"
    SENT_TO_REPLAN = "sent_to_replan"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class RiskDecisionAction(StrEnum):
    APPROVE_CONTINUE = "approve_continue"
    ACCEPT_RISK_AND_CONTINUE = "accept_risk_and_continue"
    REJECT_AND_REPLAN = "reject_and_replan"
    SEND_TO_PM = "send_to_pm"
    SEND_TO_ARCHITECT = "send_to_architect"
    SEND_TO_DEVELOPER = "send_to_developer"
    SEND_TO_QA = "send_to_qa"
    CONVERT_TO_BLOCKER = "convert_to_blocker"
    MARK_MANUAL_REQUIRED = "mark_manual_required"
    CANCEL_TASK = "cancel_task"


EnumT = TypeVar("EnumT", bound=StrEnum)


def parse_enum(enum_type: type[EnumT], value: object, field_name: str) -> EnumT:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(str(value))
    except ValueError as exc:
        allowed = ", ".join(member.value for member in enum_type)
        raise SchemaError(f"{field_name} must be one of: {allowed}") from exc


def normalize_role(value: object, *, allow_none: bool = False, field_name: str = "role") -> Role | None:
    if value is None:
        if allow_none:
            return None
        raise SchemaError(f"{field_name} is required")
    if isinstance(value, Role):
        return value
    raw = str(value)
    if allow_none and raw == "none":
        return None
    if raw in ROLE_ALIASES:
        return ROLE_ALIASES[raw]
    return parse_enum(Role, raw, field_name)


def role_to_wire(value: Role | None) -> str:
    return "none" if value is None else value.value
