import json
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from a2a_runtime.core.paths import A2APaths
from tests.cli_helpers import make_project, run_cli, write_task


class CLITests(unittest.TestCase):
    def test_help_succeeds(self) -> None:
        code, out, _ = run_cli("--help")

        self.assertEqual(code, 0)
        self.assertIn("a2a-agent", out)

    def test_no_active_task_status_exit_code_3(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents/workspace").mkdir(parents=True)

            code, out, _ = run_cli("--project-root", str(root), "status")

            self.assertEqual(code, 3)
            self.assertIn("no A2A task found", out)

    def test_task_list_can_list_task(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli("--project-root", str(root), "task", "list")

            self.assertEqual(code, 0)
            self.assertIn("T-2026-001", out)

    def test_task_active_displays_active_task(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli("--project-root", str(root), "task", "active")

            self.assertEqual(code, 0)
            self.assertIn("Active Task: T-2026-001", out)

    def test_task_use_updates_active_task(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root, active=False)

            code, out, _ = run_cli("--project-root", str(root), "task", "use", "T-2026-001", "--yes")

            self.assertEqual(code, 0)
            self.assertIn("Active Task: T-2026-001", out)
            self.assertIn("active_task_id: T-2026-001", paths.active_task_path.read_text(encoding="utf-8"))

    def test_task_use_missing_task_exit_code_3(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli("--project-root", str(root), "task", "use", "T-2026-999")

            self.assertEqual(code, 3)
            self.assertIn("task not found", out)

    def test_multiple_tasks_no_active_status_does_not_guess(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root, active=False, task_id="T-2026-001")
            write_task(paths, "T-2026-002")
            from tests.cli_helpers import write_state

            write_state(paths, "T-2026-002")

            code, out, _ = run_cli("--project-root", str(root), "status")

            self.assertEqual(code, 3)
            self.assertIn("multiple A2A tasks found", out)

    def test_json_output_is_valid_json(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli("--project-root", str(root), "--json", "status")

            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["command"], "status")
            self.assertEqual(payload["task_id"], "T-2026-001")

    def test_command_bad_args_exit_code_4(self) -> None:
        code, _, _ = run_cli("does-not-exist")

        self.assertEqual(code, 4)


if __name__ == "__main__":
    unittest.main()
