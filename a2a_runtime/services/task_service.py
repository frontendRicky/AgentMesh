"""Task creation service for controlled CLI entry points."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from a2a_runtime.core.clock import Clock
from a2a_runtime.core.constants import (
    MessageType,
    ReviewStatus,
    Role,
    TaskPriority,
    TaskStatus,
    TaskType,
    parse_enum,
)
from a2a_runtime.core.errors import RepositoryError, SchemaError
from a2a_runtime.core.ids import validate_task_id
from a2a_runtime.models.message import Message
from a2a_runtime.models.state import State
from a2a_runtime.models.task import Task, TaskScope
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.repositories.task_repo import TaskRepo
from a2a_runtime.repositories.workspace_repo import WorkspaceRepo


@dataclass(frozen=True)
class TaskCreatePlan:
    task_id: str
    task_type: TaskType
    title: str
    priority: TaskPriority
    owner: str
    set_active: bool
    planned_files: list[str]


@dataclass(frozen=True)
class TaskCreateResult:
    task_id: str
    written_files: list[Path]


class TaskService:
    def __init__(
        self,
        *,
        workspace_repo: WorkspaceRepo,
        task_repo: TaskRepo,
        state_repo: StateRepo,
        message_repo: MessageRepo,
        clock: Clock | None = None,
    ) -> None:
        self.workspace_repo = workspace_repo
        self.task_repo = task_repo
        self.state_repo = state_repo
        self.message_repo = message_repo
        self.clock = clock or Clock()

    def plan_create_task(
        self,
        *,
        task_type: TaskType | str,
        title: str,
        priority: TaskPriority | str,
        owner: str,
        task_id: str | None = None,
        set_active: bool = True,
    ) -> TaskCreatePlan:
        parsed_type = parse_enum(TaskType, task_type, "task_type")
        parsed_priority = parse_enum(TaskPriority, priority, "priority")
        selected_id = validate_task_id(task_id) if task_id else self.next_task_id()
        if self.workspace_repo.task_exists(selected_id):
            raise RepositoryError(f"task already exists: {selected_id}")
        planned = [
            str(self.workspace_repo.paths.task_md(selected_id)),
            str(self.workspace_repo.paths.state_md(selected_id)),
            str(self.workspace_repo.paths.messages_dir(selected_id) / "from-controller-001-user-to-pm-handoff.md"),
            str(self.workspace_repo.paths.active_task_path),
        ]
        return TaskCreatePlan(
            task_id=selected_id,
            task_type=parsed_type,
            title=title,
            priority=parsed_priority,
            owner=owner,
            set_active=set_active,
            planned_files=planned if set_active else planned[:-1],
        )

    def create_task(self, plan: TaskCreatePlan) -> TaskCreateResult:
        if self.workspace_repo.task_exists(plan.task_id):
            raise RepositoryError(f"task already exists: {plan.task_id}")
        self._create_workspace_dirs(plan.task_id)
        now = self.clock.now_iso()
        task = Task(
            task_id=plan.task_id,
            task_type=plan.task_type,
            task_title=plan.title,
            created_by=plan.owner,
            human_owner=plan.owner,
            priority=plan.priority,
            scope=TaskScope(in_scope=[plan.title], out_of_scope=[]),
            constraints=[],
            required_artifacts=[],
            created_at=now,
        )
        state = State(
            task_id=plan.task_id,
            current_status=TaskStatus.PM_PROCESSING,
            previous_status=TaskStatus.CREATED,
            current_agent=Role.PM,
            next_agent=Role.ARCHITECT,
            allowed_next_statuses=[TaskStatus.PM_COMPLETED, TaskStatus.BLOCKED, TaskStatus.CANCELLED],
            human_review_status=ReviewStatus.PENDING,
            final_review_status=ReviewStatus.NOT_REQUIRED,
            updated_at=now,
        )
        self.task_repo.create(task, body=f"# Task: {plan.title}\n")
        self.state_repo.write(plan.task_id, state, actor=Role.CONTROLLER, body="# State\n")
        message = Message(
            message_id=f"M-{plan.task_id}-001",
            task_id=plan.task_id,
            from_agent=Role.CONTROLLER,
            to_agent=Role.PM,
            message_type=MessageType.HANDOFF,
            intent="user_to_pm_handoff",
            summary=f"Start task {plan.task_id}",
            payload={
                "task_id": plan.task_id,
                "task_title": plan.title,
                "next_action": "pm_processing",
            },
            referenced_artifacts=[],
            required_response=True,
            blockers=[],
            created_at=now,
        )
        message_path = self.message_repo.write_message(message, "# Controller Handoff\n")
        written = [
            self.workspace_repo.paths.task_md(plan.task_id),
            self.workspace_repo.paths.state_md(plan.task_id),
            message_path,
        ]
        if plan.set_active:
            self.workspace_repo.write_active_task_id(plan.task_id, clock=self.clock)
            written.append(self.workspace_repo.paths.active_task_path)
        return TaskCreateResult(task_id=plan.task_id, written_files=written)

    def next_task_id(self) -> str:
        year = self.clock.now().year
        max_seq = 0
        for task_id in self.workspace_repo.list_task_ids():
            parts = task_id.split("-")
            if len(parts) == 3 and parts[1] == str(year):
                max_seq = max(max_seq, int(parts[2]))
        return f"T-{year}-{max_seq + 1:03d}"

    def _create_workspace_dirs(self, task_id: str) -> None:
        base = self.workspace_repo.paths.task_dir(task_id)
        if base.exists():
            raise RepositoryError(f"task already exists: {task_id}")
        for relative in [
            "messages",
            "artifacts/pm",
            "artifacts/architect",
            "artifacts/developer",
            "artifacts/qa",
            "artifacts/final",
            "human-reviews",
            "blockers",
            "archive",
        ]:
            (base / relative).mkdir(parents=True, exist_ok=True)
