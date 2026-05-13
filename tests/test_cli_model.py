import json
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from tests.cli_helpers import run_cli


class CLIModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".ai-agents").mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def cli(self, *args: str) -> tuple[int, str, str]:
        return run_cli("--project-root", str(self.root), *args)

    def test_model_list_success(self) -> None:
        code, out, _ = self.cli("model", "list")

        self.assertEqual(code, 0, out)
        self.assertIn("pm", out)
        self.assertIn("architect", out)
        self.assertIn("developer", out)

    def test_model_policy_success(self) -> None:
        code, out, _ = self.cli("model", "policy")

        self.assertEqual(code, 0, out)
        self.assertIn("Runtime 只推荐模型", out)
        self.assertIn("Runtime 不自动执行 Codex", out)

    def test_model_recommend_architect_success(self) -> None:
        code, out, _ = self.cli("model", "recommend", "--agent", "architect")

        self.assertEqual(code, 0, out)
        self.assertIn("claude-opus-4-7-thinking-high", out)

    def test_model_recommend_developer_codex_outputs_command(self) -> None:
        code, out, _ = self.cli("model", "recommend", "--agent", "developer", "--tool", "codex")

        self.assertEqual(code, 0, out)
        self.assertIn("codex --model gpt-5.5", out)
        self.assertIn("Runtime 不会自动执行该命令", out)

    def test_model_recommend_qa_p1_high_reasoning(self) -> None:
        code, out, _ = self.cli("model", "recommend", "--agent", "qa", "--risk", "P1_HIGH")

        self.assertEqual(code, 0, out)
        self.assertIn("Reasoning Effort: high", out)

    def test_model_recommend_controller_p0_upgrades_high_reasoning(self) -> None:
        code, out, _ = self.cli("model", "recommend", "--agent", "controller", "--risk", "P0_BLOCKER", "--tool", "cursor")

        self.assertEqual(code, 0, out)
        self.assertIn("claude-opus-4-7-thinking-high", out)
        self.assertIn("Cursor Action", out)
        self.assertIn("Runtime Auto Apply: no", out)

    def test_model_recommend_architect_codex_does_not_output_claude_command(self) -> None:
        code, out, _ = self.cli("model", "recommend", "--agent", "architect", "--tool", "codex")

        self.assertEqual(code, 0, out)
        self.assertIn("Command Hint: codex --model gpt-5.5", out)
        self.assertNotIn("codex --model claude-", out)
        self.assertIn("Codex does not support", out)

    def test_model_recommend_qa_codex_does_not_output_claude_command(self) -> None:
        code, out, _ = self.cli("model", "recommend", "--agent", "qa", "--tool", "codex")

        self.assertEqual(code, 0, out)
        self.assertIn("Command Hint: codex --model gpt-5.5", out)
        self.assertNotIn("codex --model claude-", out)

    def test_model_recommend_json_contract(self) -> None:
        code, out, _ = self.cli("--json", "model", "recommend", "--agent", "architect", "--tool", "cursor")

        self.assertEqual(code, 0, out)
        data = json.loads(out)
        self.assertTrue(data["ok"])
        self.assertEqual(data["command"], "model recommend")
        self.assertEqual(data["role"], "architect")
        self.assertEqual(data["selected_model"], "claude-opus-4-7-thinking-high")
        self.assertFalse(data["may_auto_apply"])
        self.assertTrue(data["user_action_required"])

    def test_model_recommend_controller_codex_p0_json_warning(self) -> None:
        code, out, _ = self.cli("--json", "model", "recommend", "--agent", "controller", "--tool", "codex", "--risk", "P0_BLOCKER")

        self.assertEqual(code, 0, out)
        data = json.loads(out)
        self.assertEqual(data["selected_model"], "gpt-5.5")
        self.assertEqual(data["command_hint"], "codex --model gpt-5.5")
        self.assertTrue(data["warnings"])

    def test_model_recommend_invalid_agent(self) -> None:
        code, out, _ = self.cli("model", "recommend", "--agent", "designer")

        self.assertEqual(code, 4, out)

    def test_model_recommend_dev_alias_outputs_developer(self) -> None:
        code, out, _ = self.cli("--json", "model", "recommend", "--agent", "dev")

        self.assertEqual(code, 0, out)
        data = json.loads(out)
        self.assertEqual(data["role"], "developer")

    def test_model_recommend_invalid_tool(self) -> None:
        code, out, _ = self.cli("model", "recommend", "--agent", "pm", "--tool", "shell")

        self.assertEqual(code, 4, out)

    def test_model_recommend_invalid_risk(self) -> None:
        code, out, _ = self.cli("model", "recommend", "--agent", "pm", "--risk", "P9")

        self.assertEqual(code, 4, out)


if __name__ == "__main__":
    unittest.main()
