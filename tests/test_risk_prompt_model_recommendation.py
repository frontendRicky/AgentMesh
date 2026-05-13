import unittest
from dataclasses import replace

from a2a_runtime.core.constants import (
    FileOperation,
    ReviewStatus,
    RiskDecisionAction,
    RiskSeverity,
    Role,
    TaskStatus,
)
from a2a_runtime.models.file_change_plan import FileChangePlan, FileChangePlanEntry
from tests.test_risk_prompt_regeneration import RiskPromptRegenerationTests


class RiskPromptModelRecommendationTests(RiskPromptRegenerationTests):
    def test_p0_risk_prompt_recommends_high_reasoning(self) -> None:
        prompt = self.service.generate_prompt_for_decision(
            risk=replace(self.risk, severity=RiskSeverity.P0_BLOCKER),
            decision=self.decision(RiskDecisionAction.SEND_TO_ARCHITECT),
            state=self.state(),
        )

        self.assertIn("Recommended Model:", prompt)
        self.assertIn("Reasoning Effort: high", prompt)
        self.assertIn("高风险任务需要高推理模型", prompt)

    def test_p1_risk_prompt_recommends_high_reasoning(self) -> None:
        prompt = self.prompt_for(RiskDecisionAction.SEND_TO_ARCHITECT)

        self.assertIn("Recommended Model:", prompt)
        self.assertIn("Reasoning Effort: high", prompt)

    def test_send_to_architect_recommends_architect_model(self) -> None:
        prompt = self.prompt_for(RiskDecisionAction.SEND_TO_ARCHITECT)

        self.assertIn("- Current Agent: architect", prompt)
        self.assertIn("claude-opus-4-7-thinking-high", prompt)

    def test_send_to_qa_recommends_qa_verifier_model(self) -> None:
        prompt = self.prompt_for(RiskDecisionAction.SEND_TO_QA)

        self.assertIn("- Current Agent: qa", prompt)
        self.assertIn("claude-opus-4-7-thinking-high", prompt)

    def test_send_to_developer_still_uses_gate_service_for_path(self) -> None:
        prompt = self.service.generate_prompt_for_decision(
            risk=self.risk,
            decision=self.decision(RiskDecisionAction.SEND_TO_DEVELOPER),
            state=self.state(
                status=TaskStatus.DEVELOPER_PROCESSING,
                human_review_status=ReviewStatus.APPROVED,
                current_agent=Role.DEVELOPER,
            ),
            target_path="src/missing.py",
            operation="modify",
            file_change_plan=FileChangePlan([]),
        )

        self.assertIn("May Write Code: no", prompt)
        self.assertIn("GateService blocker_request", prompt)

    def test_send_to_developer_allowed_path_codex_recommends_gpt_55(self) -> None:
        prompt = self.service.generate_prompt_for_decision(
            risk=self.risk,
            decision=self.decision(RiskDecisionAction.SEND_TO_DEVELOPER),
            state=self.state(
                status=TaskStatus.DEVELOPER_PROCESSING,
                human_review_status=ReviewStatus.APPROVED,
                current_agent=Role.DEVELOPER,
            ),
            target_path="src/app.py",
            operation="modify",
            file_change_plan=FileChangePlan(
                [
                    FileChangePlanEntry(
                        path="src/app.py",
                        operation=FileOperation.MODIFY,
                        allowed=True,
                        reason="planned",
                        risk="low",
                        owner="developer",
                    ),
                ],
            ),
            tool_context="codex",
        )

        self.assertIn("May Write Code: yes", prompt)
        self.assertIn("Command Hint: codex --model gpt-5.5", prompt)

    def test_convert_to_blocker_does_not_recommend_developer_write_model(self) -> None:
        prompt = self.prompt_for(RiskDecisionAction.CONVERT_TO_BLOCKER)

        self.assertIn("- Current Agent: controller", prompt)
        self.assertNotIn("- Current Agent: developer", prompt)
        self.assertIn("Two-stage Blocker", prompt)

    def test_risk_prompt_does_not_claim_auto_execution_or_switching(self) -> None:
        prompt = self.service.generate_prompt_for_decision(
            risk=self.risk,
            decision=self.decision(RiskDecisionAction.SEND_TO_ARCHITECT),
            state=self.state(),
            tool_context="codex",
        )

        self.assertIn("Command Hint:", prompt)
        self.assertIn("codex --model gpt-5.5", prompt)
        self.assertNotIn("codex --model claude-", prompt)
        self.assertNotIn("Runtime 会自动执行 Codex", prompt)
        self.assertNotIn("Runtime 会自动切换 Cursor 模型", prompt)
        self.assertNotIn("自动接受风险", prompt)

    def test_controller_codex_p0_risk_prompt_uses_gpt_55_not_claude_command(self) -> None:
        prompt = self.service.generate_prompt_for_decision(
            risk=replace(self.risk, severity=RiskSeverity.P0_BLOCKER),
            decision=self.decision(RiskDecisionAction.CONVERT_TO_BLOCKER),
            state=self.state(),
            tool_context="codex",
        )

        self.assertIn("Command Hint: codex --model gpt-5.5", prompt)
        self.assertNotIn("codex --model claude-", prompt)

    def test_risk_prompt_header_remains_strict(self) -> None:
        prompt = self.prompt_for(RiskDecisionAction.SEND_TO_ARCHITECT)

        self.assertEqual(
            prompt.splitlines()[:8],
            [
                "[A2A]",
                "- Current Agent: architect",
                "- Current Task: T-2026-001",
                "- Current Status: architect_processing",
                "- Human Review Status: pending",
                "- Reading Artifacts: [messages/*risk*, workspace/T-2026-001/task.md, workspace/T-2026-001/state.md]",
                "- Producing Artifacts: [tech_plan, file_change_plan, risk_plan]",
                "- May Write Code: no, architect prompt is readonly for business source",
            ],
        )
        self.assertEqual(prompt.splitlines()[9], "Recommended Model:")


if __name__ == "__main__":
    unittest.main()
