from __future__ import annotations

import unittest

from a2a_runtime.core.constants import RiskDecisionAction, RiskSeverity, TaskStatus
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.state_repo import StateRepo

from tests.cli_helpers import run_cli, write_risk
from tests.e2e_helpers import (
    create_minimal_a2a_protocol_tree,
    create_task_with_cli,
    create_temp_project_root,
)


class E2ERiskDecisionTests(unittest.TestCase):
    def test_risk_review_decide_and_dispatch_prompt(self) -> None:
        with create_temp_project_root() as root:
            paths, task_id = self._task_with_protocol(root)
            risk_id = write_risk(paths, task_id)

            code, out, _ = run_cli("--project-root", str(root), "risk", "list")
            self.assertEqual(code, 0)
            self.assertIn(risk_id, out)

            code, out, _ = run_cli("--project-root", str(root), "risk", "show", risk_id)
            self.assertEqual(code, 0)
            self.assertIn("Risk title", out)

            code, out, _ = run_cli("--project-root", str(root), "risk", "review", risk_id)
            self.assertEqual(code, 0)
            self.assertIn("send_to_architect", out)

            code, out, _ = run_cli("--project-root", str(root), "risk", "prompt", risk_id)
            self.assertEqual(code, 0)
            self.assertTrue(out.startswith("[A2A Risk Decision Required]"))

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "risk",
                "decide",
                risk_id,
                "--decision",
                "send_to_architect",
                "--by",
                "zhangxia",
                "--reason",
                "Need to redesign permission boundary",
                "--yes",
            )

            self.assertEqual(code, 0, out)
            messages = MessageRepo(paths).list_messages(task_id)
            self.assertTrue(any("from-human" in path.name and "risk-decision" in path.name for path in messages))
            dispatch = [path for path in messages if "risk-decision-dispatch" in path.name]
            self.assertEqual(len(dispatch), 1)
            self.assertIn("target_agent: architect", dispatch[0].read_text(encoding="utf-8"))

    def test_decision_by_controller_rejected(self) -> None:
        with create_temp_project_root() as root:
            paths, task_id = self._task_with_protocol(root)
            risk_id = write_risk(paths, task_id)

            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "risk",
                "decide",
                risk_id,
                "--decision",
                "send_to_architect",
                "--by",
                "controller",
                "--reason",
                "controller cannot decide",
                "--yes",
            )

            self.assertNotEqual(code, 0)

    def test_p0_disallows_approve_and_accept(self) -> None:
        with create_temp_project_root() as root:
            paths, task_id = self._task_with_protocol(root)
            risk_id = write_risk(paths, task_id, severity=RiskSeverity.P0_BLOCKER, options=[RiskDecisionAction.APPROVE_CONTINUE])
            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "risk",
                "decide",
                risk_id,
                "--decision",
                "approve_continue",
                "--by",
                "zhangxia",
                "--reason",
                "try approve",
                "--yes",
            )
            self.assertNotEqual(code, 0)

        with create_temp_project_root() as root:
            paths, task_id = self._task_with_protocol(root)
            risk_id = write_risk(paths, task_id, severity=RiskSeverity.P0_BLOCKER)
            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "risk",
                "decide",
                risk_id,
                "--decision",
                "accept_risk_and_continue",
                "--by",
                "zhangxia",
                "--reason",
                "try accept",
                "--yes",
            )
            self.assertNotEqual(code, 0)

    def test_cancel_task_sets_state_cancelled(self) -> None:
        with create_temp_project_root() as root:
            paths, task_id = self._task_with_protocol(root)
            risk_id = write_risk(paths, task_id, options=[RiskDecisionAction.CANCEL_TASK])

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "risk",
                "decide",
                risk_id,
                "--decision",
                "cancel_task",
                "--by",
                "zhangxia",
                "--reason",
                "Cancel due to unacceptable risk",
                "--yes",
            )

            self.assertEqual(code, 0, out)
            self.assertEqual(StateRepo(paths).read(task_id).current_status, TaskStatus.CANCELLED)

    def _task_with_protocol(self, root):
        create_minimal_a2a_protocol_tree(root)
        task_id = create_task_with_cli(root)
        return A2APaths(root), task_id


if __name__ == "__main__":
    unittest.main()
