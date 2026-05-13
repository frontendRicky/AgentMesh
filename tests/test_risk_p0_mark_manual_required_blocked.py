from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import RiskDecisionAction, RiskSeverity, RiskStatus
from a2a_runtime.core.errors import RiskDecisionError
from a2a_runtime.repositories.risk_repo import RiskRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.services.risk_decision_service import RiskDecisionService
from tests.cli_helpers import make_finalizable_project, run_cli, write_risk


class RiskP0ManualRequiredBlockedTests(unittest.TestCase):
    def test_p0_mark_manual_required_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_finalizable_project(root)
            risk_id = write_risk(
                paths,
                "T-2026-001",
                severity=RiskSeverity.P0_BLOCKER,
                options=[RiskDecisionAction.MARK_MANUAL_REQUIRED, RiskDecisionAction.CANCEL_TASK],
            )
            service = RiskDecisionService(risk_repo=RiskRepo(MessageRepo(paths)), state_repo=StateRepo(paths))

            with self.assertRaises(RiskDecisionError):
                service.record_decision(
                    task_id="T-2026-001",
                    risk_id=risk_id,
                    decision_by="zhangxia",
                    selected_option=RiskDecisionAction.MARK_MANUAL_REQUIRED.value,
                    decision=RiskDecisionAction.MARK_MANUAL_REQUIRED,
                    reason="manual check requested",
                )

    def test_p1_mark_manual_required_stays_unresolved(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_finalizable_project(root)
            risk_id = write_risk(
                paths,
                "T-2026-001",
                severity=RiskSeverity.P1_HIGH,
                options=[RiskDecisionAction.MARK_MANUAL_REQUIRED, RiskDecisionAction.SEND_TO_QA],
            )
            service = RiskDecisionService(risk_repo=RiskRepo(MessageRepo(paths)), state_repo=StateRepo(paths))
            decision = service.record_decision(
                task_id="T-2026-001",
                risk_id=risk_id,
                decision_by="zhangxia",
                selected_option=RiskDecisionAction.MARK_MANUAL_REQUIRED.value,
                decision=RiskDecisionAction.MARK_MANUAL_REQUIRED,
                reason="manual verification required",
            )

            updated = service.apply_decision(task_id="T-2026-001", decision=decision)

            self.assertEqual(updated.status, RiskStatus.PENDING_MANUAL_REVIEW)
            self.assertIn(risk_id, [risk.risk_id for risk in service.risk_repo.list_open_risks("T-2026-001")])

    def test_p1_pending_manual_review_blocks_finalize(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_finalizable_project(root)
            risk_id = write_risk(
                paths,
                "T-2026-001",
                severity=RiskSeverity.P1_HIGH,
                options=[RiskDecisionAction.MARK_MANUAL_REQUIRED, RiskDecisionAction.SEND_TO_QA],
            )
            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "risk",
                "decide",
                risk_id,
                "--decision",
                "mark_manual_required",
                "--reason",
                "manual verification required",
                "--by",
                "zhangxia",
                "--yes",
            )
            self.assertEqual(code, 0, out)

            code, out, _ = run_cli("--project-root", str(root), "finalize", "--yes")

            self.assertEqual(code, 2)
            self.assertIn("unresolved blocking risk", out)


if __name__ == "__main__":
    unittest.main()
