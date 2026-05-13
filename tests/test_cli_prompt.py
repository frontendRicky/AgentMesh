import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import ReviewStatus
from tests.cli_helpers import make_project, run_cli, write_state


class CLIPromptTests(unittest.TestCase):
    def test_prompt_pm_outputs_a2a_header(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli("--project-root", str(root), "prompt", "pm")

            self.assertEqual(code, 0)
            self.assertTrue(out.startswith("[A2A]"))

    def test_prompt_architect_may_write_code_no(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli("--project-root", str(root), "prompt", "architect")

            self.assertEqual(code, 0)
            self.assertIn("May Write Code: no", out)

    def test_prompt_developer_no_path_may_write_code_no(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli("--project-root", str(root), "prompt", "developer")

            self.assertEqual(code, 0)
            self.assertIn("May Write Code: no", out)

    def test_prompt_developer_allowed_path_may_write_code_yes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "prompt",
                "developer",
                "--path",
                "src/app.py",
                "--operation",
                "modify",
            )

            self.assertEqual(code, 0)
            self.assertIn("May Write Code: yes", out)

    def test_prompt_developer_human_review_pending_no(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_state(paths, "T-2026-001", human_review_status=ReviewStatus.PENDING)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "prompt",
                "developer",
                "--path",
                "src/app.py",
                "--operation",
                "modify",
            )

            self.assertEqual(code, 0)
            self.assertIn("May Write Code: no", out)
            self.assertIn("human_review_status_not_approved", out)

    def test_prompt_qa_contains_risk_trigger(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli("--project-root", str(root), "prompt", "qa")

            self.assertEqual(code, 0)
            self.assertIn("## Risk Trigger", out)

    def test_prompt_controller_contains_no_forge_review(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli("--project-root", str(root), "prompt", "controller")

            self.assertEqual(code, 0)
            self.assertIn("不能伪造 human review", out)

    def test_prompts_do_not_contain_auto_accept_risk(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            for role in ["pm", "architect", "developer", "qa", "controller"]:
                with self.subTest(role=role):
                    code, out, _ = run_cli("--project-root", str(root), "prompt", role)
                    self.assertEqual(code, 0)
                    self.assertNotIn("自动接受风险", out)


if __name__ == "__main__":
    unittest.main()
