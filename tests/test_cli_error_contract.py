from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import RiskSeverity
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.state_repo import StateRepo

from tests.cli_helpers import make_finalizable_project, make_project, run_cli, write_risk


class CLIErrorContractTests(unittest.TestCase):
    def test_missing_active_task_text_error_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents").mkdir()
            (root / ".ai-agents/workspace").mkdir(parents=True)

            code, out, _ = run_cli("--project-root", str(root), "status")

            self.assertEqual(code, 3)
            self.assertIn("[A2A CLI Error]", out)
            self.assertIn("Command: status", out)
            self.assertIn("Exit Code: 3", out)
            self.assertIn("Reason:", out)
            self.assertIn("Suggested Next Action:", out)

    def test_missing_active_task_json_error_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents").mkdir()
            (root / ".ai-agents/workspace").mkdir(parents=True)

            code, out, _ = run_cli("--project-root", str(root), "--json", "status")

            self.assertEqual(code, 3)
            payload = json.loads(out)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["errors"][0]["code"], "TASK_NOT_FOUND")
            self.assertIn("suggested_next_action", payload["errors"][0])

    def test_invalid_task_id_json_error_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".ai-agents").mkdir()

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "--task-id",
                "bad",
                "--json",
                "task",
                "create",
                "--type",
                "feature",
                "--title",
                "Bad task",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
                "--yes",
            )

            self.assertEqual(code, 4)
            payload = json.loads(out)
            self.assertEqual(payload["errors"][0]["code"], "INVALID_ARGS")

    def test_invalid_reviewer_json_error_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "--json",
                "review",
                "approve",
                "--stage",
                "architect",
                "--step",
                "1",
                "--reviewer",
                "controller",
                "--yes",
            )

            self.assertEqual(code, 4)
            payload = json.loads(out)
            self.assertEqual(payload["errors"][0]["code"], "INVALID_ARGS")

    def test_missing_yes_for_mutating_command_exit_code_2(self) -> None:
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
                "Needs yes",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
            )

            self.assertEqual(code, 2)
            self.assertIn("mutating command requires --yes or --dry-run", out)
            self.assertFalse((root / ".ai-agents/workspace").exists())

    def test_unresolved_p0_finalize_json_error_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_finalizable_project(root)
            write_risk(paths, "T-2026-001", severity=RiskSeverity.P0_BLOCKER)

            code, out, _ = run_cli("--project-root", str(root), "--json", "finalize", "--yes")

            self.assertEqual(code, 2)
            payload = json.loads(out)
            self.assertEqual(payload["errors"][0]["code"], "USER_DECISION_REQUIRED")
            self.assertIn("unresolved blocking risk", payload["errors"][0]["message"])

    def test_invalid_risk_decision_json_error_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "--json",
                "risk",
                "decide",
                risk_id,
                "--decision",
                "send_to_qa",
                "--reason",
                "not an option",
                "--by",
                "zhangxia",
                "--yes",
            )

            self.assertEqual(code, 2)
            payload = json.loads(out)
            self.assertEqual(payload["errors"][0]["code"], "USER_DECISION_REQUIRED")

    def test_blocker_resolve_missing_flag_error_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "blocker",
                "request",
                "--from",
                "developer",
                "--reason",
                "missing artifact",
                "--resume-to-agent",
                "architect",
                "--resume-to-status",
                "architect_processing",
                "--required-fix",
                "fix artifact",
                "--yes",
            )
            self.assertEqual(code, 0)
            request = [path for path in MessageRepo(paths).list_messages("T-2026-001") if "blocker-request" in path.name][0]
            message_id = MessageRepo(paths).read_message(request).message_id
            code, _, _ = run_cli("--project-root", str(root), "blocker", "create", "--from-request", message_id, "--yes")
            self.assertEqual(code, 0)
            blocker_id = StateRepo(paths).read("T-2026-001").active_blocker or ""

            code, out, _ = run_cli("--project-root", str(root), "--json", "blocker", "resolve", blocker_id, "--yes")

            self.assertEqual(code, 4)
            payload = json.loads(out)
            self.assertEqual(payload["errors"][0]["code"], "INVALID_ARGS")
            self.assertIn("--missing-artifacts-resolved", payload["errors"][0]["message"])


if __name__ == "__main__":
    unittest.main()
