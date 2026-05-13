import unittest

from a2a_runtime.core.constants import Role
from tests.test_prompt_generation import PromptGenerationTests


class PromptModelRecommendationTests(PromptGenerationTests):
    def test_pm_prompt_contains_recommended_model(self) -> None:
        prompt = self.service.generate_pm_prompt("T-2026-001")

        self.assertIn("Recommended Model:", prompt)
        self.assertIn("claude-4.6-sonnet-medium-thinking", prompt)

    def test_architect_prompt_recommends_high_reasoning_model(self) -> None:
        prompt = self.service.generate_architect_prompt("T-2026-001")

        self.assertIn("Recommended Model:", prompt)
        self.assertIn("claude-opus-4-7-thinking-high", prompt)
        self.assertIn("Reasoning Effort: high", prompt)

    def test_developer_prompt_codex_context_contains_codex_command(self) -> None:
        prompt = self.service.generate_developer_prompt(
            "T-2026-001",
            target_path="src/app.py",
            operation="modify",
            tool_context="codex",
        )

        self.assertIn("Recommended Model:", prompt)
        self.assertIn("Command Hint: codex --model gpt-5.5", prompt)
        self.assertIn("Runtime 不会自动执行该命令", prompt)

    def test_architect_codex_prompt_does_not_emit_claude_codex_command(self) -> None:
        prompt = self.service.generate_architect_prompt("T-2026-001", tool_context="codex")

        self.assertIn("Command Hint: codex --model gpt-5.5", prompt)
        self.assertNotIn("codex --model claude-", prompt)
        self.assertIn("Codex does not support", prompt)

    def test_cursor_prompt_does_not_claim_auto_model_switch(self) -> None:
        prompt = self.service.generate_architect_prompt("T-2026-001", tool_context="cursor")

        self.assertIn("Cursor Action:", prompt)
        self.assertNotIn("Runtime 会自动切换", prompt)
        self.assertNotIn("Runtime will auto-switch", prompt)

    def test_prompt_does_not_claim_real_llm_call(self) -> None:
        prompt = self.service.generate_pm_prompt("T-2026-001")

        self.assertNotIn("Runtime 会调用真实 LLM", prompt)
        self.assertNotIn("Runtime will call a real LLM", prompt)

    def test_a2a_header_is_not_modified_by_model_section(self) -> None:
        prompt = self.service.generate_pm_prompt("T-2026-001")
        expected_header = [
            "[A2A]",
            "- Current Agent: pm",
            "- Current Task: T-2026-001",
            "- Current Status: developer_processing",
            "- Human Review Status: approved",
            "- Reading Artifacts: [task.md, state.md, messages/from-controller-*-handoff.md]",
            "- Producing Artifacts: [requirement.md, prd.md, task-breakdown.md]",
            "- May Write Code: no, PM Agent 不允许写源码",
        ]

        self.assertEqual(prompt.splitlines()[:8], expected_header)
        self.assertEqual(prompt.splitlines()[9], "Recommended Model:")

    def test_pm_architect_qa_controller_still_may_write_no(self) -> None:
        prompts = [
            self.service.generate_pm_prompt("T-2026-001"),
            self.service.generate_architect_prompt("T-2026-001"),
            self.service.generate_qa_prompt("T-2026-001"),
            self.service.generate_controller_prompt("T-2026-001"),
        ]

        for prompt in prompts:
            self.assertIn("May Write Code: no", prompt)

    def test_developer_may_write_code_still_uses_gate_service(self) -> None:
        allowed = self.service.generate_developer_prompt(
            "T-2026-001",
            target_path="src/app.py",
            operation="modify",
        )
        package = self.service.generate_developer_prompt(
            "T-2026-001",
            target_path="package.json",
            operation="modify",
        )

        self.assertIn("May Write Code: yes", allowed)
        self.assertIn("GateService none", allowed)
        self.assertIn("May Write Code: no", package)
        self.assertIn("risk_decision_required", package)

    def test_prompt_does_not_contain_auto_risk_acceptance_phrase(self) -> None:
        prompt = self.service.generate(Role.ARCHITECT, "T-2026-001")

        self.assertNotIn("自动接受风险", prompt)


if __name__ == "__main__":
    unittest.main()
