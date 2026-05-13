from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.cli_helpers import run_cli


class ProjectRootValidationTests(unittest.TestCase):
    def test_system_roots_are_rejected(self) -> None:
        for root in [
            "/",
            "/etc",
            "/etc/foo",
            "/usr",
            "/usr/local/foo",
            "/var",
            "/var/tmp/foo",
            "/private",
            "/private/tmp/foo",
            "/System",
            "/System/foo",
            "/Library",
            str(Path.home() / "Library"),
        ]:
            with self.subTest(root=root):
                code, out, _ = run_cli("--project-root", root, "status")
                self.assertEqual(code, 4)
                self.assertIn("unsafe --project-root refused", out)

    def test_directory_without_project_marker_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            code, out, _ = run_cli("--project-root", tmp, "status")

            self.assertEqual(code, 4)
            self.assertIn("project marker", out)

    def test_ai_agents_marker_allows_project_root(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents/workspace").mkdir(parents=True)

            code, out, _ = run_cli("--project-root", str(root), "status")

            self.assertEqual(code, 3)
            self.assertNotIn("project marker", out)

    def test_pyproject_marker_allows_project_root(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")

            code, out, _ = run_cli("--project-root", str(root), "status")

            self.assertEqual(code, 3)
            self.assertNotIn("project marker", out)

    def test_allow_non_project_root_warns(self) -> None:
        with TemporaryDirectory() as tmp:
            code, out, _ = run_cli("--project-root", tmp, "--allow-non-project-root", "--json", "status")

            self.assertEqual(code, 3)
            payload = json.loads(out)
            self.assertTrue(payload["warnings"])

    def test_task_create_output_contains_resolved_project_root(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents").mkdir()

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "task",
                "create",
                "--type",
                "feature",
                "--title",
                "Root prompt",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
                "--dry-run",
            )

            self.assertEqual(code, 0)
            self.assertIn(f"Project Root: {root.resolve()}", out)
            self.assertIn("Project Markers:", out)
            self.assertIn("Will Create Task:", out)


if __name__ == "__main__":
    unittest.main()
