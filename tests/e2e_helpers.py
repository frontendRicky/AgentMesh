from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator

from a2a_runtime.core.constants import (
    ArtifactType,
    ReviewStatus,
    ReviewType,
    ReviewVerdict,
    Role,
    TaskStatus,
)
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.review import ReviewRecord
from a2a_runtime.repositories.review_repo import ReviewRepo
from a2a_runtime.repositories.state_repo import StateRepo

from tests.cli_helpers import (
    run_cli,
    write_artifact,
    write_file_change_plan,
    write_profile_files,
)


@contextmanager
def create_temp_project_root() -> Iterator[Path]:
    with TemporaryDirectory() as tmp:
        yield Path(tmp)


def create_minimal_a2a_protocol_tree(root: Path) -> A2APaths:
    write_profile_files(root)
    (root / ".ai-agents/workspace").mkdir(parents=True, exist_ok=True)
    return A2APaths(root)


def create_task_with_cli(root: Path, *, title: str = "E2E task", task_id: str | None = None) -> str:
    args = [
        "--project-root",
        str(root),
        "task",
        "create",
        "--type",
        "feature",
        "--title",
        title,
        "--priority",
        "P1",
        "--owner",
        "zhangxia",
        "--yes",
    ]
    if task_id is not None:
        args.extend(["--task-id", task_id])
    code, out, err = run_cli(*args)
    if code != 0:
        raise AssertionError(f"task create failed: code={code}\nstdout={out}\nstderr={err}")
    if task_id is not None:
        return task_id
    active = (root / ".ai-agents/workspace/active-task.md").read_text(encoding="utf-8")
    for line in active.splitlines():
        if line.startswith("active_task_id:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError("active-task.md did not contain active_task_id")


def create_ready_pm_artifacts(paths: A2APaths, task_id: str) -> None:
    write_artifact(paths, task_id, ArtifactType.REQUIREMENT, Role.PM)
    write_artifact(paths, task_id, ArtifactType.PRD, Role.PM)
    write_artifact(paths, task_id, ArtifactType.TASK_BREAKDOWN, Role.PM)


def create_ready_architect_artifacts(paths: A2APaths, task_id: str) -> None:
    write_artifact(paths, task_id, ArtifactType.TECH_PLAN, Role.ARCHITECT)
    write_file_change_plan(paths, task_id)
    write_artifact(paths, task_id, ArtifactType.RISK_PLAN, Role.ARCHITECT)


def create_ready_developer_artifacts(paths: A2APaths, task_id: str) -> None:
    write_artifact(paths, task_id, ArtifactType.IMPLEMENTATION_LOG, Role.DEVELOPER)
    write_artifact(paths, task_id, ArtifactType.CHANGED_FILES, Role.DEVELOPER)


def create_ready_qa_artifacts(paths: A2APaths, task_id: str) -> None:
    write_artifact(paths, task_id, ArtifactType.TEST_REPORT, Role.QA, body="# Test Report\nstatus: pass\n")
    write_artifact(paths, task_id, ArtifactType.ACCEPTANCE_CHECKLIST, Role.QA)


def create_approved_architect_review(paths: A2APaths, task_id: str) -> None:
    ReviewRepo(paths).write_review(
        ReviewRecord(
            review_id=f"R-{task_id}-architect",
            task_id=task_id,
            review_type=ReviewType.ARCHITECT_REVIEW,
            reviewed_artifacts=["tech_plan", "file_change_plan", "risk_plan"],
            reviewer="zhangxia",
            reviewed_at="2026-05-12T10:00:00+08:00",
            verdict=ReviewVerdict.APPROVED,
            issues=[],
            followup_required=False,
        ),
    )


def create_clean_final_review_preconditions(paths: A2APaths, task_id: str) -> None:
    create_ready_pm_artifacts(paths, task_id)
    create_ready_architect_artifacts(paths, task_id)
    create_ready_developer_artifacts(paths, task_id)
    create_ready_qa_artifacts(paths, task_id)
    create_approved_architect_review(paths, task_id)
    set_state(
        paths,
        task_id,
        current_status=TaskStatus.FINAL_REVIEW_REQUIRED,
        previous_status=TaskStatus.QA_COMPLETED,
        current_agent=Role.HUMAN,
        human_review_status=ReviewStatus.APPROVED,
        final_review_status=ReviewStatus.PENDING,
    )


def set_state(
    paths: A2APaths,
    task_id: str,
    *,
    current_status: TaskStatus,
    previous_status: TaskStatus | None = None,
    current_agent: Role | None = None,
    human_review_status: ReviewStatus | None = None,
    final_review_status: ReviewStatus | None = None,
) -> None:
    state = StateRepo(paths).read(task_id)
    StateRepo(paths).write(
        task_id,
        replace(
            state,
            current_status=current_status,
            previous_status=previous_status or state.current_status,
            current_agent=current_agent if current_agent is not None else state.current_agent,
            human_review_status=human_review_status or state.human_review_status,
            final_review_status=final_review_status or state.final_review_status,
        ),
        actor=Role.CONTROLLER,
        body="# State\n",
    )
