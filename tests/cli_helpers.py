from __future__ import annotations

import io
from dataclasses import replace
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from a2a_runtime.cli import main
from a2a_runtime.core.constants import (
    ArtifactStatus,
    ArtifactType,
    ReviewStatus,
    ReviewType,
    ReviewVerdict,
    RiskCategory,
    RiskDecisionAction,
    RiskSeverity,
    RiskStatus,
    Role,
    TaskPriority,
    TaskStatus,
    TaskType,
    ValidationOutcome,
)
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.artifact import Artifact
from a2a_runtime.models.risk import RuntimeRiskFinding
from a2a_runtime.models.review import ReviewRecord
from a2a_runtime.models.state import State
from a2a_runtime.models.task import Task, TaskScope
from a2a_runtime.repositories.artifact_repo import ArtifactRepo
from a2a_runtime.repositories.risk_repo import RiskRepo
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.review_repo import ReviewRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.repositories.task_repo import TaskRepo
from a2a_runtime.repositories.workspace_repo import WorkspaceRepo


def run_cli(*args: str) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(args))
    return code, out.getvalue(), err.getvalue()


def make_project(root: Path, *, active: bool = True, task_id: str = "T-2026-001") -> A2APaths:
    paths = A2APaths(root)
    write_profile_files(root)
    write_task(paths, task_id)
    write_state(paths, task_id)
    write_file_change_plan(paths, task_id)
    if active:
        WorkspaceRepo(paths).write_active_task_id(task_id)
    return paths


def write_profile_files(root: Path) -> None:
    for directory in [
        ".ai-agents/agent-cards",
        ".ai-agents/agents",
        ".ai-agents/handoffs",
        ".ai-agents/flows",
        ".ai-agents/rules",
        ".ai-agents/templates",
        ".cursor/rules",
        "归档",
    ]:
        (root / directory).mkdir(parents=True, exist_ok=True)
    cards = {
        "product-manager.card.md": ("pm-001", "Product Manager Agent", "pm"),
        "architect.card.md": ("architect-001", "Architect Agent", "architect"),
        "senior-frontend-developer.card.md": ("developer-001", "Senior Frontend Developer Agent", "developer"),
        "qa-tester.card.md": ("qa-001", "QA Tester Agent", "qa"),
        "flow-controller.card.md": ("controller-001", "Flow Controller Agent", "controller"),
    }
    for filename, (agent_id, name, role) in cards.items():
        (root / ".ai-agents/agent-cards" / filename).write_text(
            f"""---
agent_id: {agent_id}
agent_name: {name}
role: {role}
version: 1.0.0
schema_version: a2a/v1
---

## output_artifacts
- {role}-artifact.md

## writable_paths
- workspace/<task-id>/artifacts/{role}/**

## forbidden_actions
- Do not write state.md
""",
            encoding="utf-8",
        )
    for filename in [
        "product-manager.agent.md",
        "architect.agent.md",
        "senior-frontend-developer.agent.md",
        "qa-tester.agent.md",
        "flow-controller.agent.md",
    ]:
        (root / ".ai-agents/agents" / filename).write_text("# Behavior\n", encoding="utf-8")
    (root / ".ai-agents/handoffs/developer-to-qa.md").write_text(
        """---
contract_id: HC-developer-to-qa
from_agent: developer
to_agent: qa
schema_version: a2a/v1
---

## required_output_messages
- handoff
""",
        encoding="utf-8",
    )
    (root / ".ai-agents/flows/feature-flow.md").write_text("# Flow\n", encoding="utf-8")
    (root / ".ai-agents/rules/a2a-rules.md").write_text("# Rules\n", encoding="utf-8")
    (root / ".ai-agents/templates/message-template.md").write_text("# Template\n", encoding="utf-8")
    (root / ".cursor/rules/ai-agents.mdc").write_text("# Cursor A2A\n", encoding="utf-8")
    (root / "归档/planner.md").write_text("需求摘要。\n", encoding="utf-8")
    (root / "归档/architect.md").write_text("readonly\n", encoding="utf-8")
    (root / "归档/implementer.md").write_text("不主动 commit / push / 创建 MR。\n", encoding="utf-8")
    (root / "归档/verifier.md").write_text("P0/P1 风险不得给“通过”。\n", encoding="utf-8")
    (root / "归档/a-to-a-workflow.mdc").write_text("A2A flow。\n", encoding="utf-8")


def write_task(paths: A2APaths, task_id: str) -> None:
    TaskRepo(paths).create(
        Task(
            task_id=task_id,
            task_type=TaskType.FEATURE,
            task_title=f"Task {task_id}",
            created_by="user",
            human_owner="zhangxia",
            priority=TaskPriority.P1,
            scope=TaskScope(in_scope=["feature"], out_of_scope=["none"]),
            constraints=[],
            required_artifacts=[],
            created_at="2026-05-12T10:00:00+08:00",
        ),
    )


def write_state(
    paths: A2APaths,
    task_id: str,
    *,
    status: TaskStatus = TaskStatus.DEVELOPER_PROCESSING,
    human_review_status: ReviewStatus = ReviewStatus.APPROVED,
) -> None:
    StateRepo(paths).write(
        task_id,
        State(
            task_id=task_id,
            current_status=status,
            previous_status=status,
            current_agent=Role.DEVELOPER,
            next_agent=None,
            allowed_next_statuses=[],
            human_review_status=human_review_status,
            final_review_status=ReviewStatus.NOT_REQUIRED,
            updated_at="2026-05-12T10:00:00+08:00",
        ),
        actor=Role.CONTROLLER,
        body="# State",
    )


def write_file_change_plan(paths: A2APaths, task_id: str) -> None:
    artifact = Artifact(
        artifact_id=f"A-{task_id}-file_change_plan",
        task_id=task_id,
        artifact_type=ArtifactType.FILE_CHANGE_PLAN,
        produced_by=Role.ARCHITECT,
        consumed_by=[Role.DEVELOPER],
        file_path="artifacts/architect/file-change-plan.md",
        version=1,
        status=ArtifactStatus.READY,
        summary="Plan",
        validation_result=ValidationOutcome.PASS,
        created_at="2026-05-12T10:00:00+08:00",
    )
    ArtifactRepo(paths).write_artifact(
        artifact,
        """# File Change Plan
- path: src/app.py
  operation: modify
  allowed: true
  reason: planned
  risk: low
  owner: developer
- path: package.json
  operation: modify
  allowed: true
  reason: dependency
  risk: high
  owner: developer
""",
    )


def write_artifact(paths: A2APaths, task_id: str, artifact_type: ArtifactType, role: Role, body: str = "# Artifact\n") -> None:
    directory = "qa" if role == Role.QA else role.value
    filename = artifact_type.value.replace("_", "-")
    artifact = Artifact(
        artifact_id=f"A-{task_id}-{artifact_type.value}",
        task_id=task_id,
        artifact_type=artifact_type,
        produced_by=role,
        consumed_by=[Role.CONTROLLER],
        file_path=f"artifacts/{directory}/{filename}.md",
        version=1,
        status=ArtifactStatus.READY,
        summary=f"{artifact_type.value} ready",
        validation_result=ValidationOutcome.PASS,
        created_at="2026-05-12T10:00:00+08:00",
    )
    ArtifactRepo(paths).write_artifact(artifact, body)


def make_finalizable_project(root: Path) -> A2APaths:
    paths = make_project(root)
    task_id = "T-2026-001"
    write_state(paths, task_id, status=TaskStatus.COMPLETED, human_review_status=ReviewStatus.APPROVED)
    state = StateRepo(paths).read(task_id)
    StateRepo(paths).write(
        task_id,
        replace(
            state,
            current_status=TaskStatus.COMPLETED,
            previous_status=TaskStatus.FINAL_REVIEW_REQUIRED,
            current_agent=Role.CONTROLLER,
            next_agent=None,
            allowed_next_statuses=[],
            human_review_status=ReviewStatus.APPROVED,
            final_review_status=ReviewStatus.APPROVED,
            updated_at="2026-05-12T10:00:00+08:00",
        ),
        actor=Role.CONTROLLER,
        body="# State",
    )
    for artifact_type, role in [
        (ArtifactType.REQUIREMENT, Role.PM),
        (ArtifactType.PRD, Role.PM),
        (ArtifactType.TASK_BREAKDOWN, Role.PM),
        (ArtifactType.TECH_PLAN, Role.ARCHITECT),
        (ArtifactType.FILE_CHANGE_PLAN, Role.ARCHITECT),
        (ArtifactType.RISK_PLAN, Role.ARCHITECT),
        (ArtifactType.IMPLEMENTATION_LOG, Role.DEVELOPER),
        (ArtifactType.CHANGED_FILES, Role.DEVELOPER),
        (ArtifactType.TEST_REPORT, Role.QA),
        (ArtifactType.ACCEPTANCE_CHECKLIST, Role.QA),
    ]:
        write_artifact(paths, task_id, artifact_type, role)
    review_repo = ReviewRepo(paths)
    review_repo.write_review(
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
    review_repo.write_review(
        ReviewRecord(
            review_id=f"R-{task_id}-final",
            task_id=task_id,
            review_type=ReviewType.FINAL_REVIEW,
            reviewed_artifacts=["test_report", "acceptance_checklist"],
            reviewer="zhangxia",
            reviewed_at="2026-05-12T10:00:00+08:00",
            verdict=ReviewVerdict.APPROVED,
            issues=[],
            followup_required=False,
        ),
    )
    return paths


def write_risk(
    paths: A2APaths,
    task_id: str,
    *,
    severity: RiskSeverity = RiskSeverity.P1_HIGH,
    options: list[RiskDecisionAction] | None = None,
) -> str:
    repo = RiskRepo(MessageRepo(paths))
    recommended = options or [
        RiskDecisionAction.SEND_TO_ARCHITECT,
        RiskDecisionAction.ACCEPT_RISK_AND_CONTINUE,
        RiskDecisionAction.CANCEL_TASK,
    ]
    risk = RuntimeRiskFinding(
        risk_id=f"RISK-{task_id}-001",
        task_id=task_id,
        source_agent=Role.CONTROLLER,
        category=RiskCategory.SCOPE,
        severity=severity,
        title="Risk title",
        description="Risk description",
        evidence="Risk evidence",
        detected_at="2026-05-12T10:00:00+08:00",
        requires_human_decision=severity in {RiskSeverity.P0_BLOCKER, RiskSeverity.P1_HIGH, RiskSeverity.P2_MEDIUM},
        status=RiskStatus.WAITING_HUMAN_DECISION
        if severity in {RiskSeverity.P0_BLOCKER, RiskSeverity.P1_HIGH, RiskSeverity.P2_MEDIUM}
        else RiskStatus.OPEN,
        recommended_options=[option.value for option in recommended],
        default_recommendation=recommended[0].value,
    )
    repo.write_risk_review_request(risk)
    return risk.risk_id
