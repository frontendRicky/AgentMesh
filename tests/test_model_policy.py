import unittest

from a2a_runtime.core.constants import RiskSeverity, Role
from a2a_runtime.core.constants import normalize_role
from a2a_runtime.core.errors import SchemaError
from a2a_runtime.models.model_policy import normalize_model_policy_role
from a2a_runtime.services.model_selection_service import ModelSelectionService, _is_low_cost_model


class ModelPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ModelSelectionService()

    def test_pm_recommends_medium_model(self) -> None:
        result = self.service.recommend_for_role(Role.PM)

        self.assertEqual(result.selected_model, "claude-4.6-sonnet-medium-thinking")
        self.assertEqual(result.reasoning_effort, "medium")
        self.assertEqual(result.cost_tier, "medium")

    def test_architect_recommends_high_reasoning_model(self) -> None:
        result = self.service.recommend_for_role(Role.ARCHITECT)

        self.assertEqual(result.selected_model, "claude-opus-4-7-thinking-high")
        self.assertEqual(result.reasoning_effort, "high")

    def test_developer_codex_recommends_gpt_55(self) -> None:
        result = self.service.recommend_for_role(Role.DEVELOPER, tool_context="codex")

        self.assertEqual(result.selected_model, "gpt-5.5")
        self.assertEqual(result.command_hint, "codex --model gpt-5.5")

    def test_qa_recommends_high_reasoning(self) -> None:
        result = self.service.recommend_for_role(Role.QA)

        self.assertEqual(result.selected_model, "claude-opus-4-7-thinking-high")
        self.assertEqual(result.cost_tier, "high")

    def test_controller_default_is_low_cost(self) -> None:
        result = self.service.recommend_for_role(Role.CONTROLLER)

        self.assertEqual(result.selected_model, "gpt-5.5-mini")
        self.assertEqual(result.reasoning_effort, "low")
        self.assertEqual(result.cost_tier, "low")

    def test_risk_role_recommends_high_reasoning(self) -> None:
        result = self.service.recommend_for_role("risk")

        self.assertEqual(result.selected_model, "claude-opus-4-7-thinking-high")
        self.assertEqual(result.reasoning_effort, "high")

    def test_p0_risk_upgrades_controller_to_high_reasoning(self) -> None:
        result = self.service.recommend_for_role(Role.CONTROLLER, risk_level=RiskSeverity.P0_BLOCKER)

        self.assertEqual(result.reasoning_effort, "high")
        self.assertEqual(result.selected_model, "claude-opus-4-7-thinking-high")
        self.assertTrue(result.warnings)

    def test_p1_risk_upgrades_controller_to_high_reasoning(self) -> None:
        result = self.service.recommend_for_role(Role.CONTROLLER, risk_level=RiskSeverity.P1_HIGH)

        self.assertEqual(result.reasoning_effort, "high")
        self.assertNotIn("mini", result.selected_model)

    def test_p2_risk_does_not_force_high_reasoning(self) -> None:
        result = self.service.recommend_for_role(Role.CONTROLLER, risk_level=RiskSeverity.P2_MEDIUM)

        self.assertEqual(result.selected_model, "gpt-5.5-mini")
        self.assertEqual(result.reasoning_effort, "low")

    def test_generic_context_has_no_command_hint(self) -> None:
        result = self.service.recommend_for_role(Role.DEVELOPER, tool_context="generic")

        self.assertIsNone(result.command_hint)

    def test_cursor_context_has_no_auto_command(self) -> None:
        result = self.service.recommend_for_role(Role.ARCHITECT, tool_context="cursor")

        self.assertIsNone(result.command_hint)
        section = self.service.render_prompt_section(result)
        self.assertIn("Cursor Action:", section)
        self.assertIn("Runtime 不会自动切换模型", section)

    def test_codex_context_generates_command_hint(self) -> None:
        result = self.service.recommend_for_role(Role.DEVELOPER, tool_context="codex")

        self.assertEqual(result.command_hint, "codex --model gpt-5.5")

    def test_architect_codex_does_not_generate_claude_command(self) -> None:
        result = self.service.recommend_for_role(Role.ARCHITECT, tool_context="codex")

        self.assertEqual(result.selected_model, "gpt-5.5")
        self.assertEqual(result.command_hint, "codex --model gpt-5.5")
        self.assertTrue(any("Codex does not support" in warning for warning in result.warnings))

    def test_controller_codex_p0_uses_gpt_55_not_claude(self) -> None:
        result = self.service.recommend_for_role(Role.CONTROLLER, tool_context="codex", risk_level=RiskSeverity.P0_BLOCKER)

        self.assertEqual(result.selected_model, "gpt-5.5")
        self.assertEqual(result.command_hint, "codex --model gpt-5.5")
        self.assertNotIn("claude", result.command_hint or "")

    def test_low_cost_model_detection_uses_allowlist(self) -> None:
        self.assertTrue(_is_low_cost_model("gpt-5.5-mini"))
        self.assertFalse(_is_low_cost_model("gemini-pro"))
        self.assertFalse(_is_low_cost_model("claude-lighthouse-9"))

    def test_recommendation_is_never_auto_applied(self) -> None:
        result = self.service.recommend_for_role(Role.PM)

        self.assertFalse(result.may_auto_apply)
        self.assertTrue(result.user_action_required)

    def test_dev_alias_outputs_developer(self) -> None:
        result = self.service.recommend_for_role("dev")

        self.assertEqual(result.role_value, "developer")
        self.assertEqual(result.to_dict()["role"], "developer")

    def test_model_policy_role_normalization_delegates_dev_alias(self) -> None:
        self.assertEqual(normalize_model_policy_role("dev"), Role.DEVELOPER)
        self.assertEqual(normalize_role("dev"), Role.DEVELOPER)

    def test_invalid_role_errors_are_consistent(self) -> None:
        with self.assertRaises(SchemaError):
            normalize_model_policy_role("designer")
        with self.assertRaises(SchemaError):
            normalize_role("designer")


if __name__ == "__main__":
    unittest.main()
