"""Minimal Cursor prompt generation for risk decisions."""

from __future__ import annotations

from dataclasses import dataclass, field

from a2a_runtime.core.constants import FileOperation, RiskDecisionAction, Role, TaskStatus
from a2a_runtime.models.file_change_plan import FileChangePlan
from a2a_runtime.models.risk import RuntimeRiskFinding
from a2a_runtime.models.risk_decision import RiskDecision
from a2a_runtime.models.state import State
from a2a_runtime.services.gate_service import GateService
from a2a_runtime.services.model_selection_service import ModelSelectionService
from a2a_runtime.services.prompt_sections import (
    MayWriteCodeDecision,
    render_a2a_header,
    render_bullets,
    render_forbidden_paths_or_actions,
)


@dataclass(frozen=True)
class RiskPromptRegenerationService:
    gate_service: GateService = field(default_factory=GateService)
    model_selection_service: ModelSelectionService = field(default_factory=ModelSelectionService)

    def generate_prompt_for_decision(
        self,
        *,
        risk: RuntimeRiskFinding,
        decision: RiskDecision,
        state: State,
        target_path: str | None = None,
        operation: FileOperation | str | None = None,
        file_change_plan: FileChangePlan | None = None,
        tool_context: str = "cursor",
    ) -> str:
        target_agent = decision.target_agent or Role.CONTROLLER
        target_status = decision.target_status
        may_write = self._may_write_code(
            target_agent,
            target_status,
            state,
            target_path=target_path,
            operation=operation,
            file_change_plan=file_change_plan,
        )
        expected = self._expected_output_artifacts(decision.decision, target_agent)
        model_role: Role | str = Role.CONTROLLER if decision.decision == RiskDecisionAction.CONVERT_TO_BLOCKER else target_agent
        model_result = self.model_selection_service.recommend_for_role(
            model_role,
            tool_context=tool_context,
            risk_level=risk.severity,
        )
        model_section = self.model_selection_service.render_prompt_section(model_result)
        header = render_a2a_header(
            role=target_agent,
            task_id=risk.task_id,
            state=state,
            reading_artifacts=["messages/*risk*", f"workspace/{risk.task_id}/task.md", f"workspace/{risk.task_id}/state.md"],
            producing_artifacts=expected,
            may_write_code=may_write,
        )
        blocker_note = (
            "\nTwo-stage Blocker rule: professional agents may only create blocker_request; "
            "formal blockers are Controller-only."
            if decision.decision == RiskDecisionAction.CONVERT_TO_BLOCKER
            else ""
        )
        return f"""{header}

{model_section}

# Risk Decision Dispatch

risk_id: {risk.risk_id}
decision_id: {decision.decision_id}
selected_option: {decision.selected_option}
target_agent: {target_agent.value}
target_status: {target_status.value if target_status else 'none'}

## Required Reads
- workspace/{risk.task_id}/task.md
- workspace/{risk.task_id}/state.md
- messages/*risk*

## Forbidden Actions
{render_forbidden_paths_or_actions([
    "Do not modify package or lock files unless explicitly authorized.",
    "Do not write business source outside the approved gate.",
    "Do not decide on behalf of the user.",
])}

## Risk Trigger
If any P0/P1 risk, scope expansion, package/lock/CI change, QA fail/blocked, or multiple reasonable recovery paths appear, stop and trigger Human Risk Decision Gate.
Do not decide on behalf of the user.

## Regenerate Artifacts
{render_bullets(expected)}

## Expected Output Artifacts
{render_bullets(expected)}

## Handoff Requirements
- Summarize the risk evidence.
- Explain the selected decision.
- Produce only artifacts allowed for {target_agent.value}.
- Return a handoff message to controller when done.{blocker_note}
"""

    def _may_write_code(
        self,
        target_agent: Role,
        target_status: TaskStatus | None,
        state: State,
        *,
        target_path: str | None,
        operation: FileOperation | str | None,
        file_change_plan: FileChangePlan | None,
    ) -> MayWriteCodeDecision:
        if target_agent != Role.DEVELOPER:
            return MayWriteCodeDecision(False, f"{target_agent.value} prompt is readonly for business source")
        if target_status != TaskStatus.DEVELOPER_PROCESSING:
            return MayWriteCodeDecision(False, "target_status is not developer_processing")
        if target_path is None or operation is None:
            return MayWriteCodeDecision(False, "未指定目标路径与操作")
        result = self.gate_service.check_developer_write(
            state=state,
            target_path=target_path,
            operation=operation,
            file_change_plan=file_change_plan or FileChangePlan([]),
        )
        return MayWriteCodeDecision(
            result.allowed,
            f"GateService {result.failure_type.value}: {result.reason}",
        )

    def _expected_output_artifacts(
        self,
        decision: RiskDecisionAction,
        target_agent: Role,
    ) -> list[str]:
        if decision == RiskDecisionAction.CONVERT_TO_BLOCKER:
            return ["blocker_request"]
        mapping = {
            Role.PM: ["requirement", "prd", "task_breakdown"],
            Role.ARCHITECT: ["tech_plan", "file_change_plan", "risk_plan"],
            Role.DEVELOPER: ["implementation_log", "changed_files"],
            Role.QA: ["test_report", "acceptance_checklist"],
            Role.CONTROLLER: ["status_message"],
            Role.HUMAN: ["review_record"],
        }
        return mapping[target_agent]
