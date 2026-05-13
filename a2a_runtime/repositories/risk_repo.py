"""Message-based persistence for Human Risk Decision Gate records."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from a2a_runtime.core.clock import Clock
from a2a_runtime.core.constants import MessageType, RiskDecisionAction, RiskStatus, Role
from a2a_runtime.core.ids import validate_risk_id, validate_task_id
from a2a_runtime.models.message import Message
from a2a_runtime.models.risk import RuntimeRiskFinding
from a2a_runtime.models.risk_decision import RiskDecision
from a2a_runtime.repositories.message_repo import MessageRepo


class RiskRepo:
    def __init__(self, message_repo: MessageRepo, clock: Clock | None = None) -> None:
        self.message_repo = message_repo
        self.clock = clock or Clock()

    def next_risk_sequence(self, task_id: str) -> int:
        validate_task_id(task_id)
        sequences: list[int] = []
        for message in self._risk_review_messages(task_id):
            risk_id = str(message.payload.get("risk_id", ""))
            if risk_id.startswith(f"RISK-{task_id}-"):
                sequences.append(int(risk_id.rsplit("-", 1)[1]))
        return max(sequences, default=0) + 1

    def build_risk_id(self, task_id: str, seq: int) -> str:
        return validate_risk_id(f"RISK-{task_id}-{seq:03d}")

    def build_risk_review_request_message(
        self,
        risk: RuntimeRiskFinding,
        *,
        body: str = "",
    ) -> Message:
        seq = self.message_repo.next_sequence(risk.task_id)
        return Message(
            message_id=f"M-{risk.task_id}-{seq:03d}",
            task_id=risk.task_id,
            from_agent=Role.CONTROLLER,
            to_agent=Role.HUMAN,
            message_type=MessageType.STATUS,
            intent="risk_review_request",
            summary=risk.title,
            payload=risk.to_frontmatter(),
            referenced_artifacts=[],
            required_response=True,
            blockers=[],
            created_at=self.clock.now_iso(),
        )

    def build_risk_decision_message(
        self,
        decision: RiskDecision,
        *,
        body: str = "",
    ) -> Message:
        seq = self.message_repo.next_sequence(decision.task_id)
        return Message(
            message_id=f"M-{decision.task_id}-{seq:03d}",
            task_id=decision.task_id,
            from_agent=Role.HUMAN,
            to_agent=Role.CONTROLLER,
            message_type=MessageType.REVIEW,
            intent="risk_decision",
            summary=f"Risk decision {decision.decision_id}",
            payload=decision.to_frontmatter(),
            referenced_artifacts=[],
            required_response=True,
            blockers=[],
            created_at=self.clock.now_iso(),
        )

    def write_risk_review_request(self, risk: RuntimeRiskFinding, body: str = "") -> Message:
        message = self.build_risk_review_request_message(risk, body=body)
        self.message_repo.write_message(message, body or self._risk_body(risk))
        return message

    def write_risk_decision(self, decision: RiskDecision, body: str = "") -> Message:
        message = self.build_risk_decision_message(decision, body=body)
        self.message_repo.write_message(message, body)
        return message

    def write_risk_dispatch(
        self,
        *,
        task_id: str,
        decision: RiskDecision,
        prompt: str,
    ) -> Message:
        seq = self.message_repo.next_sequence(task_id)
        message = Message(
            message_id=f"M-{task_id}-{seq:03d}",
            task_id=task_id,
            from_agent=Role.CONTROLLER,
            to_agent=decision.target_agent or Role.CONTROLLER,
            message_type=MessageType.STATUS,
            intent="risk_decision_dispatch",
            summary=f"Dispatch risk decision {decision.decision_id}",
            payload=decision.to_frontmatter(),
            referenced_artifacts=[],
            required_response=True,
            blockers=[],
            created_at=self.clock.now_iso(),
        )
        self.message_repo.write_message(message, prompt)
        return message

    def list_risk_messages(self, task_id: str) -> list[Message]:
        messages: list[Message] = []
        for path in self.message_repo.list_messages(task_id):
            message = self.message_repo.read_message(path)
            if message.intent in {"risk_review_request", "risk_decision", "risk_decision_dispatch"}:
                messages.append(message)
        return messages

    def list_open_risks(self, task_id: str) -> list[RuntimeRiskFinding]:
        decisions_by_risk = {decision.risk_id: decision for decision in self.list_decisions(task_id)}
        risks: list[RuntimeRiskFinding] = []
        for risk in self.list_risks(task_id):
            decision = decisions_by_risk.get(risk.risk_id)
            if decision is None:
                if risk.status in {
                    RiskStatus.OPEN,
                    RiskStatus.WAITING_HUMAN_DECISION,
                    RiskStatus.PENDING_MANUAL_REVIEW,
                }:
                    risks.append(risk)
                continue
            if decision.decision == RiskDecisionAction.CONVERT_TO_BLOCKER:
                status = RiskStatus.CONVERTED_TO_BLOCKER
            elif decision.decision in {
                RiskDecisionAction.REJECT_AND_REPLAN,
                RiskDecisionAction.SEND_TO_PM,
                RiskDecisionAction.SEND_TO_ARCHITECT,
                RiskDecisionAction.SEND_TO_DEVELOPER,
                RiskDecisionAction.SEND_TO_QA,
            }:
                status = RiskStatus.SENT_TO_REPLAN
            elif decision.decision == RiskDecisionAction.CANCEL_TASK:
                status = RiskStatus.REJECTED
            elif decision.decision == RiskDecisionAction.MARK_MANUAL_REQUIRED:
                status = RiskStatus.PENDING_MANUAL_REVIEW
            else:
                status = RiskStatus.ACCEPTED
            updated = replace(risk, status=status)
            if updated.status in {
                RiskStatus.OPEN,
                RiskStatus.WAITING_HUMAN_DECISION,
                RiskStatus.PENDING_MANUAL_REVIEW,
            }:
                risks.append(updated)
        return risks

    def list_risks(self, task_id: str) -> list[RuntimeRiskFinding]:
        return [
            RuntimeRiskFinding.from_frontmatter(message.payload)
            for message in self._risk_review_messages(task_id)
        ]

    def list_decisions(self, task_id: str) -> list[RiskDecision]:
        return [
            RiskDecision.from_frontmatter(message.payload)
            for message in self._risk_decision_messages(task_id)
        ]

    def find_risk(self, task_id: str, risk_id: str) -> RuntimeRiskFinding:
        validate_risk_id(risk_id)
        for risk in self.list_risks(task_id):
            if risk.risk_id == risk_id:
                return risk
        raise KeyError(f"risk not found: {risk_id}")

    def find_decision(self, task_id: str, risk_id: str) -> RiskDecision | None:
        for decision in self.list_decisions(task_id):
            if decision.risk_id == risk_id:
                return decision
        return None

    def _risk_review_messages(self, task_id: str) -> list[Message]:
        return [
            message
            for message in self.list_risk_messages(task_id)
            if message.intent == "risk_review_request"
        ]

    def _risk_decision_messages(self, task_id: str) -> list[Message]:
        return [
            message
            for message in self.list_risk_messages(task_id)
            if message.intent == "risk_decision"
        ]

    def _risk_body(self, risk: RuntimeRiskFinding) -> str:
        options = "\n".join(f"- {option}" for option in risk.recommended_options)
        return f"""# Human Risk Decision Required

## Risk
- risk_id: {risk.risk_id}
- severity: {risk.severity.value}
- category: {risk.category.value}

## Evidence
{risk.evidence}

## Options
{options}
"""
