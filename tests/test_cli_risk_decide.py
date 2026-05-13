from __future__ import annotations

import tempfile
import unittest
import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from a2a_runtime.core.constants import RiskDecisionAction, RiskSeverity, ReviewStatus, Role
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.state_repo import StateRepo

from tests.cli_helpers import make_project, run_cli, write_risk


class CLIRiskDecideTests(unittest.TestCase):
    def test_decision_by_controller_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")

            code, _, _ = self._decide(root, risk_id, by="controller")

            self.assertNotEqual(code, 0)

    def test_reason_missing_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")

            code, _, _ = self._decide(root, risk_id, reason="")

            self.assertNotEqual(code, 0)

    def test_decision_not_in_options_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")

            code, _, _ = self._decide(root, risk_id, decision="send_to_qa")

            self.assertNotEqual(code, 0)

    def test_send_to_architect_generates_dispatch_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")

            code, _, _ = self._decide(root, risk_id, decision="send_to_architect")

            self.assertEqual(code, 0)
            dispatch_paths = [path for path in MessageRepo(paths).list_messages("T-2026-001") if "risk-decision-dispatch" in path.name]
            self.assertEqual(len(dispatch_paths), 1)
            body = dispatch_paths[0].read_text(encoding="utf-8")
            self.assertIn("target_agent: architect", body)
            self.assertIn("risk_id: RISK-T-2026-001-001", body)

    def test_send_to_developer_prompt_remains_gate_limited(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root, active=True)
            state = StateRepo(paths).read("T-2026-001")
            StateRepo(paths).write(
                "T-2026-001",
                replace(state, human_review_status=ReviewStatus.PENDING),
                actor=Role.CONTROLLER,
                body="# State",
            )
            risk_id = write_risk(paths, "T-2026-001", options=[RiskDecisionAction.SEND_TO_DEVELOPER])

            code, _, _ = self._decide(root, risk_id, decision="send_to_developer")

            self.assertEqual(code, 0)
            dispatch_paths = [path for path in MessageRepo(paths).list_messages("T-2026-001") if "risk-decision-dispatch" in path.name]
            body = dispatch_paths[0].read_text(encoding="utf-8")
            self.assertIn("May Write Code: no", body)
            self.assertIn("target_agent: developer", body)

    def test_accept_risk_and_continue_writes_decision_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")

            code, _, _ = self._decide(root, risk_id, decision="accept_risk_and_continue")

            self.assertEqual(code, 0)
            human_decisions = [path for path in MessageRepo(paths).list_messages("T-2026-001") if "risk-decision" in path.name and "from-human" in path.name]
            self.assertEqual(len(human_decisions), 1)

    def test_p0_disallows_approve_continue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(
                paths,
                "T-2026-001",
                severity=RiskSeverity.P0_BLOCKER,
                options=[RiskDecisionAction.APPROVE_CONTINUE],
            )

            code, _, _ = self._decide(root, risk_id, decision="approve_continue")

            self.assertNotEqual(code, 0)

    def test_p0_disallows_accept_risk_and_continue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001", severity=RiskSeverity.P0_BLOCKER)

            code, _, _ = self._decide(root, risk_id, decision="accept_risk_and_continue")

            self.assertNotEqual(code, 0)

    def test_cancel_task_updates_cancelled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001", options=[RiskDecisionAction.CANCEL_TASK])

            code, _, _ = self._decide(root, risk_id, decision="cancel_task")

            self.assertEqual(code, 0)
            self.assertEqual(StateRepo(paths).read("T-2026-001").current_status.value, "cancelled")

    def test_risk_decide_does_not_write_business_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")

            code, _, _ = self._decide(root, risk_id, decision="accept_risk_and_continue")

            self.assertEqual(code, 0)
            self.assertFalse((root / "src").exists())

    def test_decision_by_mismatch_emits_warning_and_payload_audit_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")

            with patch.dict("os.environ", {"USER": "localuser"}):
                code, out, _ = self._decide(root, risk_id, by="zhangxia")

            self.assertEqual(code, 0, out)
            self.assertIn("does not match local user", out)
            messages = [
                path
                for path in MessageRepo(paths).list_messages("T-2026-001")
                if "risk-decision" in path.name and "from-human" in path.name
            ]
            payload = MessageRepo(paths).read_message(messages[0]).payload
            self.assertEqual(payload["decision_by"], "zhangxia")
            self.assertEqual(payload["local_user"], "localuser")
            self.assertTrue(payload["user_mismatch_warning"])

    def test_decision_by_mismatch_json_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")

            with patch.dict("os.environ", {"USER": "localuser"}):
                code, out, _ = run_cli(
                    "--project-root",
                    str(root),
                    "--json",
                    "risk",
                    "decide",
                    risk_id,
                    "--decision",
                    "send_to_architect",
                    "--reason",
                    "human decision reason",
                    "--by",
                    "zhangxia",
                    "--yes",
                )

            self.assertEqual(code, 0, out)
            payload = json.loads(out)
            self.assertTrue(payload["warnings"])
            self.assertTrue(payload["user_mismatch_warning"])

    def test_decision_by_matching_local_user_has_no_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")

            with patch.dict("os.environ", {"USER": "zhangxia"}):
                code, out, _ = self._decide(root, risk_id, by="zhangxia")

            self.assertEqual(code, 0, out)
            self.assertNotIn("does not match local user", out)

    def _decide(
        self,
        root: Path,
        risk_id: str,
        *,
        decision: str = "send_to_architect",
        reason: str = "human decision reason",
        by: str = "zhangxia",
    ) -> tuple[int, str, str]:
        return run_cli(
            "--project-root",
            str(root),
            "risk",
            "decide",
            risk_id,
            "--decision",
            decision,
            "--reason",
            reason,
            "--by",
            by,
            "--yes",
        )


if __name__ == "__main__":
    unittest.main()
