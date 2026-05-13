from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.cli_helpers import make_project


class CLISubprocessSmokeTests(unittest.TestCase):
    def run_subprocess(self, *args: str, root: Path | None = None) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, "-m", "a2a_runtime.cli"]
        if root is not None:
            command.extend(["--project-root", str(root)])
        command.extend(args)
        return subprocess.run(command, text=True, capture_output=True, check=False)

    def test_help_subprocess_success(self) -> None:
        result = self.run_subprocess("--help")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("A2A Runtime does not call a real LLM", result.stdout)

    def test_status_json_subprocess(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            result = self.run_subprocess("--json", "status", root=root)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["task_id"], "T-2026-001")

    def test_task_create_dry_run_json_subprocess(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents").mkdir()

            result = self.run_subprocess(
                "--json",
                "task",
                "create",
                "--type",
                "feature",
                "--title",
                "Dry run",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
                "--dry-run",
                root=root,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["written_files"], [])

    def test_model_recommend_codex_json_subprocess(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents").mkdir()

            result = self.run_subprocess(
                "--json",
                "model",
                "recommend",
                "--agent",
                "developer",
                "--tool",
                "codex",
                root=root,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["command_hint"], "codex --model gpt-5.5")

    def test_gate_developer_json_subprocess(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            result = self.run_subprocess(
                "--json",
                "gate",
                "developer",
                "--path",
                "src/app.py",
                "--operation",
                "modify",
                root=root,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["allowed"])
            self.assertFalse((root / "src").exists())

    def test_invalid_args_subprocess_nonzero(self) -> None:
        result = self.run_subprocess("model", "recommend", "--agent", "developer", "--tool", "invalid")

        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
