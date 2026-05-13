from __future__ import annotations

import unittest

from a2a_runtime.core.constants import RiskDecisionAction
from tests.test_prompt_generation import PromptGenerationTests


class PromptHeaderStrictMatchTests(PromptGenerationTests):
    def assert_header(self, prompt: str, role: str) -> None:
        lines = prompt.splitlines()[:8]
        self.assertEqual(lines[0], "[A2A]")
        self.assertEqual(lines[1], f"- Current Agent: {role}")
        self.assertTrue(lines[2].startswith("- Current Task: "))
        self.assertTrue(lines[3].startswith("- Current Status: "))
        self.assertTrue(lines[4].startswith("- Human Review Status: "))
        self.assertTrue(lines[5].startswith("- Reading Artifacts: ["))
        self.assertTrue(lines[6].startswith("- Producing Artifacts: ["))
        self.assertTrue(lines[7].startswith("- May Write Code: "))
        self.assertNotIn("Final Review Status", "\n".join(lines))
        self.assertTrue(all(line.startswith("- ") for line in lines[1:]))
        self.assertIn("## Risk Trigger", prompt)
        self.assertNotIn("自动接受风险", prompt)

    def test_all_agent_prompt_headers_strict(self) -> None:
        prompts = {
            "pm": self.service.generate_pm_prompt("T-2026-001"),
            "architect": self.service.generate_architect_prompt("T-2026-001"),
            "developer": self.service.generate_developer_prompt("T-2026-001"),
            "qa": self.service.generate_qa_prompt("T-2026-001"),
            "controller": self.service.generate_controller_prompt("T-2026-001"),
        }
        for role, prompt in prompts.items():
            with self.subTest(role=role):
                self.assert_header(prompt, role)

    def test_risk_prompt_header_strict(self) -> None:
        from tests.test_risk_prompt_regeneration import RiskPromptRegenerationTests

        fixture = RiskPromptRegenerationTests()
        fixture.setUp()
        prompt = fixture.prompt_for(RiskDecisionAction.SEND_TO_ARCHITECT)

        self.assert_header(prompt, "architect")


if __name__ == "__main__":
    unittest.main()
