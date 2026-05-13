from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.cli_helpers import make_finalizable_project, make_project, run_cli, write_risk


class CLIJSONContractTests(unittest.TestCase):
    def test_success_json_contract_for_core_read_commands(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")

            commands = [
                ("status",),
                ("validate",),
                ("task", "list"),
                ("task", "active"),
                ("prompt", "pm"),
                ("gate", "developer", "--path", "src/app.py", "--operation", "modify"),
                ("risk", "list"),
                ("risk", "show", risk_id),
                ("report",),
            ]

            for command in commands:
                with self.subTest(command=command):
                    code, out, _ = run_cli("--project-root", str(root), "--json", *command)
                    self.assertEqual(code, 0)
                    self._assert_contract(json.loads(out), ok=True)

    def test_finalize_dry_run_json_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_finalizable_project(root)

            code, out, _ = run_cli("--project-root", str(root), "--json", "finalize", "--dry-run")

            self.assertEqual(code, 0)
            payload = json.loads(out)
            self._assert_contract(payload, ok=True)
            self.assertEqual(payload["written_files"], [])
            self.assertTrue(payload["gate_ok"])

    def test_read_only_json_written_files_are_empty(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")
            for command in [
                ("status",),
                ("validate",),
                ("task", "list"),
                ("task", "active"),
                ("prompt", "pm"),
                ("gate", "developer", "--path", "src/app.py", "--operation", "modify"),
                ("risk", "list"),
                ("risk", "show", risk_id),
                ("report",),
            ]:
                with self.subTest(command=command):
                    code, out, _ = run_cli("--project-root", str(root), "--json", *command)
                    self.assertEqual(code, 0)
                    self.assertEqual(json.loads(out)["written_files"], [])

    def test_mutating_dry_run_json_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")
            commands = [
                (
                    "task create",
                    (
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
                    ),
                ),
                (
                    "risk decide",
                    (
                        "risk",
                        "decide",
                        risk_id,
                        "--decision",
                        "send_to_architect",
                        "--reason",
                        "preview",
                        "--by",
                        "zhangxia",
                        "--dry-run",
                    ),
                ),
                (
                    "review approve",
                    (
                        "review",
                        "approve",
                        "--stage",
                        "architect",
                        "--step",
                        "1",
                        "--reviewer",
                        "zhangxia",
                        "--dry-run",
                    ),
                ),
                (
                    "blocker request",
                    (
                        "blocker",
                        "request",
                        "--from",
                        "developer",
                        "--reason",
                        "preview",
                        "--resume-to-agent",
                        "architect",
                        "--resume-to-status",
                        "architect_processing",
                        "--required-fix",
                        "preview",
                        "--dry-run",
                    ),
                ),
                ("finalize", ("finalize", "--dry-run")),
            ]
            for label, command in commands:
                with self.subTest(command=label):
                    code, out, _ = run_cli("--project-root", str(root), "--json", *command)
                    payload = json.loads(out)
                    self.assertIn(code, {0, 1, 2})
                    self.assertTrue(payload["dry_run"])
                    self.assertEqual(payload["written_files"], [])
                    self.assertIn("planned_writes", payload)

    def test_task_use_json_lists_written_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root, active=False)

            code, out, _ = run_cli("--project-root", str(root), "--json", "task", "use", "T-2026-001", "--yes")

            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertTrue(payload["written_files"])

    def test_task_use_dry_run_json_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root, active=False)

            code, out, _ = run_cli("--project-root", str(root), "--json", "task", "use", "T-2026-001", "--dry-run")

            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["written_files"], [])
            self.assertTrue(payload["planned_writes"])

    def test_error_json_contract_and_exit_code(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents/workspace").mkdir(parents=True)

            code, out, _ = run_cli("--project-root", str(root), "--json", "status")

            self.assertEqual(code, 3)
            payload = json.loads(out)
            self._assert_contract(payload, ok=False)
            self.assertTrue(payload["errors"])

    def _assert_contract(self, payload: dict[str, object], *, ok: bool) -> None:
        for key in ["ok", "command", "task_id", "written_files", "errors", "warnings"]:
            self.assertIn(key, payload)
        self.assertEqual(payload["ok"], ok)
        self.assertIsInstance(payload["command"], str)
        self.assertIsInstance(payload["written_files"], list)
        self.assertIsInstance(payload["errors"], list)
        self.assertIsInstance(payload["warnings"], list)


if __name__ == "__main__":
    unittest.main()
