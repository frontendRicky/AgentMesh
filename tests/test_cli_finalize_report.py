from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from a2a_runtime.core.constants import RiskDecisionAction, RiskSeverity
from a2a_runtime.repositories.message_repo import MessageRepo

from tests.cli_helpers import make_finalizable_project, make_project, run_cli, write_risk


class CLIFinalizeReportTests(unittest.TestCase):
    def test_finalize_gate_not_satisfied_does_not_write_final_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, _, _ = run_cli("--project-root", str(root), "finalize", "--yes")

            self.assertEqual(code, 1)
            self.assertFalse((root / ".ai-agents/workspace/T-2026-001/artifacts/final/final-delivery.md").exists())

    def test_unresolved_p0_blocks_finalize(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_finalizable_project(root)
            write_risk(paths, "T-2026-001", severity=RiskSeverity.P0_BLOCKER)

            code, _, _ = run_cli("--project-root", str(root), "finalize", "--yes")

            self.assertEqual(code, 2)
            self.assertFalse((root / ".ai-agents/workspace/T-2026-001/artifacts/final/final-delivery.md").exists())

    def test_unresolved_p1_blocks_finalize(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_finalizable_project(root)
            write_risk(paths, "T-2026-001", severity=RiskSeverity.P1_HIGH)

            code, _, _ = run_cli("--project-root", str(root), "finalize", "--yes")

            self.assertEqual(code, 2)
            self.assertFalse((root / ".ai-agents/workspace/T-2026-001/artifacts/final/final-delivery.md").exists())

    def test_accepted_risk_is_written_to_final_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_finalizable_project(root)
            risk_id = write_risk(
                paths,
                "T-2026-001",
                options=[RiskDecisionAction.ACCEPT_RISK_AND_CONTINUE],
            )
            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "risk",
                "decide",
                risk_id,
                "--decision",
                "accept_risk_and_continue",
                "--reason",
                "accepted by user for final delivery traceability",
                "--by",
                "zhangxia",
                "--yes",
            )
            self.assertEqual(code, 0)

            code, _, _ = run_cli("--project-root", str(root), "finalize", "--yes")

            self.assertEqual(code, 0)
            body = (root / ".ai-agents/workspace/T-2026-001/artifacts/final/final-delivery.md").read_text(encoding="utf-8")
            self.assertIn(risk_id, body)
            self.assertIn("accepted risk", body)

    def test_all_gates_pass_write_final_delivery_and_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_finalizable_project(root)
            upstream = root / ".ai-agents/workspace/T-2026-001/artifacts/pm/requirement.md"
            before = upstream.read_text(encoding="utf-8")

            code, _, _ = run_cli("--project-root", str(root), "finalize", "--yes")

            self.assertEqual(code, 0)
            self.assertTrue((root / ".ai-agents/workspace/T-2026-001/artifacts/final/final-delivery.md").exists())
            messages = MessageRepo(paths).list_messages("T-2026-001")
            self.assertTrue(any("final-delivery-completed" in path.name for path in messages))
            self.assertEqual(upstream.read_text(encoding="utf-8"), before)

    def test_finalize_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_finalizable_project(root)

            code, _, _ = run_cli("--project-root", str(root), "finalize", "--dry-run")

            self.assertEqual(code, 0)
            self.assertFalse((root / ".ai-agents/workspace/T-2026-001/artifacts/final/final-delivery.md").exists())

    def test_report_stdout_contains_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_risk(paths, "T-2026-001")
            before = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())

            code, out, _ = run_cli("--project-root", str(root), "report")

            after = sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())
            self.assertEqual(code, 0)
            self.assertIn("Blockers Summary", out)
            self.assertIn("Risk Summary", out)
            self.assertEqual(before, after)

    def test_report_json_contains_summaries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_risk(paths, "T-2026-001")

            code, out, _ = run_cli("--project-root", str(root), "--json", "report")

            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertIn("blockers_summary", payload)
            self.assertIn("risk_summary", payload)
            self.assertEqual(payload["risk_summary"]["unresolved"], ["RISK-T-2026-001-001"])


if __name__ == "__main__":
    unittest.main()
