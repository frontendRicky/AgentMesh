"""Read-only runtime report service."""

from __future__ import annotations

from dataclasses import dataclass

from a2a_runtime.core.constants import ArtifactType, RiskDecisionAction, RiskSeverity
from a2a_runtime.core.clock import Clock
from a2a_runtime.repositories.artifact_repo import ArtifactRepo
from a2a_runtime.repositories.blocker_repo import BlockerRepo
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.risk_repo import RiskRepo
from a2a_runtime.repositories.review_repo import ReviewRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.repositories.task_repo import TaskRepo


@dataclass(frozen=True)
class RuntimeReport:
    data: dict[str, object]

    def render_text(self) -> str:
        risks = self.data.get("risk_summary", {})
        blockers = self.data.get("blockers_summary", {})
        return f"""[A2A CLI]
Command: report
Task: {self.data.get('task_id')}
Title: {self.data.get('task_title')}
Current Status: {self.data.get('current_status')}
Current Agent: {self.data.get('current_agent')}
Produced Artifacts: {self.data.get('produced_artifacts_count')}
Messages Count: {self.data.get('messages_count')}
Blockers Summary: active={blockers.get('active_blocker')} history={blockers.get('history')}
Review Status: human={self.data.get('human_review_status')} final={self.data.get('final_review_status')}
Risk Summary: accepted={risks.get('accepted')} unresolved={risks.get('unresolved')}
Final Delivery Status: {self.data.get('final_delivery_status')}
Next Action: {self.data.get('next_action')}
Generated At: {self.data.get('generated_at')}
"""


class ReportService:
    def __init__(
        self,
        *,
        task_repo: TaskRepo,
        state_repo: StateRepo,
        artifact_repo: ArtifactRepo,
        message_repo: MessageRepo,
        blocker_repo: BlockerRepo,
        review_repo: ReviewRepo,
        risk_repo: RiskRepo,
        clock: Clock | None = None,
    ) -> None:
        self.task_repo = task_repo
        self.state_repo = state_repo
        self.artifact_repo = artifact_repo
        self.message_repo = message_repo
        self.blocker_repo = blocker_repo
        self.review_repo = review_repo
        self.risk_repo = risk_repo
        self.clock = clock or Clock()

    def build_report(self, task_id: str) -> RuntimeReport:
        task = self.task_repo.read(task_id)
        state = self.state_repo.read(task_id)
        artifacts = self.artifact_repo.list_artifacts(task_id)
        messages = self.message_repo.list_messages(task_id)
        blockers = self.blocker_repo.list_blockers(task_id)
        decisions = self.risk_repo.list_decisions(task_id)
        accepted = [
            decision.risk_id
            for decision in decisions
            if decision.decision == RiskDecisionAction.ACCEPT_RISK_AND_CONTINUE
        ]
        unresolved = [
            risk.risk_id
            for risk in self.risk_repo.list_open_risks(task_id)
            if risk.severity in {RiskSeverity.P0_BLOCKER, RiskSeverity.P1_HIGH}
        ]
        final_delivery = self.artifact_repo.find_artifact(task_id, ArtifactType.FINAL_DELIVERY)
        architect_review = self.review_repo.find_architect_review(task_id)
        final_review = self.review_repo.find_final_review(task_id)
        data: dict[str, object] = {
            "task_id": task_id,
            "task_title": task.task_title,
            "task_type": task.task_type.value,
            "current_status": state.current_status.value,
            "current_agent": state.current_agent.value if state.current_agent else None,
            "human_review_status": state.human_review_status.value,
            "final_review_status": state.final_review_status.value,
            "produced_artifacts_count": len(artifacts),
            "messages_count": len(messages),
            "blockers_summary": {
                "active_blocker": state.active_blocker,
                "history": list(state.blockers_history),
                "blockers_count": len(blockers),
            },
            "reviews": {
                "architect_review": architect_review.review_id if architect_review else None,
                "final_review": final_review.review_id if final_review else None,
            },
            "risk_summary": {
                "accepted": accepted,
                "unresolved": unresolved,
                "all_risks": [risk.risk_id for risk in self.risk_repo.list_risks(task_id)],
            },
            "final_delivery_status": "present" if final_delivery else "missing",
            "next_action": self._next_action(state.current_status.value, unresolved),
            "generated_at": self.clock.now_iso(),
        }
        return RuntimeReport(data=data)

    def _next_action(self, current_status: str, unresolved: list[str]) -> str:
        if unresolved:
            return "resolve human risk decisions"
        if current_status == "completed":
            return "finalize or report"
        if current_status == "blocked":
            return "resolve active blocker"
        return "continue workflow through controller"
