import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.frontmatter import load
from a2a_runtime.core.paths import A2APaths
from tests.cli_helpers import make_project, run_cli


class CLIMutatingTaskTests(unittest.TestCase):
    def test_task_create_auto_allocates_task_id(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents").mkdir()
            make_project(root, task_id="T-2026-001")

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "task",
                "create",
                "--type",
                "feature",
                "--title",
                "New settings",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
                "--yes",
            )

            self.assertEqual(code, 0)
            self.assertIn("T-2026-002", out)
            self.assertTrue((root / ".ai-agents/workspace/T-2026-002/task.md").exists())

    def test_task_create_manual_task_id(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents").mkdir()

            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "task",
                "create",
                "--task-id",
                "T-2026-003",
                "--type",
                "feature",
                "--title",
                "Manual",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
                "--yes",
            )

            self.assertEqual(code, 0)
            self.assertTrue((root / ".ai-agents/workspace/T-2026-003/task.md").exists())

    def test_task_create_illegal_task_id_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents").mkdir()
            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "task",
                "create",
                "--task-id",
                "BAD",
                "--type",
                "feature",
                "--title",
                "Bad",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
                "--yes",
            )

            self.assertNotEqual(code, 0)
            self.assertIn("task_id", out)

    def test_task_create_existing_directory_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "task",
                "create",
                "--task-id",
                "T-2026-001",
                "--type",
                "feature",
                "--title",
                "Exists",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
                "--yes",
            )

            self.assertNotEqual(code, 0)
            self.assertIn("already exists", out)

    def test_task_create_files_and_initial_state(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents").mkdir()
            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "task",
                "create",
                "--task-id",
                "T-2026-001",
                "--type",
                "feature",
                "--title",
                "Init",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
                "--yes",
            )
            self.assertEqual(code, 0)
            paths = A2APaths(root)
            task_data = load(paths.task_md("T-2026-001")).data
            self.assertNotIn("current_status", task_data)
            state_data = load(paths.state_md("T-2026-001")).data
            self.assertEqual(state_data["current_status"], "pm_processing")
            self.assertEqual(state_data["current_agent"], "pm")
            self.assertTrue((paths.messages_dir("T-2026-001") / "from-controller-001-user-to-pm-handoff.md").exists())

    def test_task_create_no_active_does_not_write_active_task(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents").mkdir()
            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "task",
                "create",
                "--task-id",
                "T-2026-001",
                "--type",
                "feature",
                "--title",
                "No active",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
                "--no-active",
                "--yes",
            )

            self.assertEqual(code, 0)
            self.assertFalse((root / ".ai-agents/workspace/active-task.md").exists())

    def test_task_create_dry_run_writes_nothing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents").mkdir()
            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "task",
                "create",
                "--task-id",
                "T-2026-001",
                "--type",
                "feature",
                "--title",
                "Dry",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
                "--dry-run",
            )

            self.assertEqual(code, 0)
            self.assertIn("Dry Run: true", out)
            self.assertFalse((root / ".ai-agents/workspace/T-2026-001").exists())

    def test_task_create_json_contains_written_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents").mkdir()
            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "--json",
                "task",
                "create",
                "--task-id",
                "T-2026-001",
                "--type",
                "feature",
                "--title",
                "Json",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
                "--yes",
            )

            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertTrue(payload["written_files"])


if __name__ == "__main__":
    unittest.main()
