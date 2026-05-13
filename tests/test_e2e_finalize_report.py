from __future__ import annotations

import json
import unittest
from dataclasses import replace

from a2a_runtime.core.constants import RiskDecisionAction, RiskSeverity, Role, TaskStatus
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.repositories.state_repo import StateRepo

from tests.cli_helpers import run_cli, write_risk
from tests.e2e_helpers import (
    create_clean_final_review_preconditions,
    create_minimal_a2a_protocol_tree,
    create_task_with_cli,
    create_temp_project_root,
)


class E2EFinalizeReportTests(unittest.TestCase):
    def test_final_review_approve_finalize_and_report(self) -> None:
        with create_temp_project_root() as root:
            paths, task_id = self._ready_for_final_review(root)

            code, out, _ = self._approve_final(root)
            self.assertEqual(code, 0, out)
            self.assertEqual(StateRepo(paths).read(task_id).current_status, TaskStatus.COMPLETED)

            code, out, _ = run_cli("--project-root", str(root), "finalize", "--yes")
            self.assertEqual(code, 0, out)

            final_delivery = root / f".ai-agents/workspace/{task_id}/artifacts/final/final-delivery.md"
            body = final_delivery.read_text(encoding="utf-8")
            self.assertIn("## Artifact Index", body)
            self.assertIn("## Review Record Index", body)
            self.assertIn("## Final Gate Check Summary", body)

            code, out, _ = run_cli("--project-root", str(root), "report")
            self.assertEqual(code, 0)
            self.assertIn("Final Delivery Status: present", out)

            code, out, _ = run_cli("--project-root", str(root), "--json", "report")
            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertEqual(payload["final_delivery_status"], "present")

    def test_accepted_risk_appears_in_final_delivery(self) -> None:
        with create_temp_project_root() as root:
            paths, task_id = self._ready_for_final_review(root)
            code, out, _ = self._approve_final(root)
            self.assertEqual(code, 0, out)
            risk_id = write_risk(paths, task_id, options=[RiskDecisionAction.ACCEPT_RISK_AND_CONTINUE])
            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "risk",
                "decide",
                risk_id,
                "--decision",
                "accept_risk_and_continue",
                "--reason",
                "Accepted for release with traceability",
                "--by",
                "zhangxia",
                "--yes",
            )
            self.assertEqual(code, 0, out)

            code, out, _ = run_cli("--project-root", str(root), "finalize", "--yes")

            self.assertEqual(code, 0, out)
            body = (root / f".ai-agents/workspace/{task_id}/artifacts/final/final-delivery.md").read_text(encoding="utf-8")
            self.assertIn(risk_id, body)
            self.assertIn("accepted risk", body)

    def test_unresolved_p0_or_p1_blocks_finalize(self) -> None:
        for severity in [RiskSeverity.P0_BLOCKER, RiskSeverity.P1_HIGH]:
            with self.subTest(severity=severity.value):
                with create_temp_project_root() as root:
                    paths, task_id = self._ready_for_final_review(root)
                    code, out, _ = self._approve_final(root)
                    self.assertEqual(code, 0, out)
                    write_risk(paths, task_id, severity=severity)

                    code, _, _ = run_cli("--project-root", str(root), "finalize", "--yes")

                    self.assertEqual(code, 2)
                    self.assertFalse((root / f".ai-agents/workspace/{task_id}/artifacts/final/final-delivery.md").exists())

    def test_active_blocker_blocks_finalize(self) -> None:
        with create_temp_project_root() as root:
            paths, task_id = self._ready_for_final_review(root)
            code, out, _ = self._approve_final(root)
            self.assertEqual(code, 0, out)
            state = StateRepo(paths).read(task_id)
            StateRepo(paths).write(
                task_id,
                replace(state, active_blocker=f"B-{task_id}-001"),
                actor=Role.CONTROLLER,
                body="# State\n",
            )

            code, _, _ = run_cli("--project-root", str(root), "finalize", "--yes")

            self.assertNotEqual(code, 0)
            self.assertFalse((root / f".ai-agents/workspace/{task_id}/artifacts/final/final-delivery.md").exists())

    def test_finalize_dry_run_writes_no_final_delivery(self) -> None:
        with create_temp_project_root() as root:
            paths, task_id = self._ready_for_final_review(root)
            code, out, _ = self._approve_final(root)
            self.assertEqual(code, 0, out)

            code, _, _ = run_cli("--project-root", str(root), "finalize", "--dry-run")

            self.assertEqual(code, 0)
            self.assertFalse((root / f".ai-agents/workspace/{task_id}/artifacts/final/final-delivery.md").exists())

    def _ready_for_final_review(self, root):
        create_minimal_a2a_protocol_tree(root)
        task_id = create_task_with_cli(root)
        paths = A2APaths(root)
        create_clean_final_review_preconditions(paths, task_id)
        return paths, task_id

    def _approve_final(self, root):
        code, out, err = run_cli(
            "--project-root",
            str(root),
            "review",
            "approve",
            "--stage",
            "final",
            "--step",
            "1",
            "--reviewer",
            "zhangxia",
            "--yes",
        )
        if code != 0:
            return code, out, err
        return run_cli(
            "--project-root",
            str(root),
            "review",
            "approve",
            "--stage",
            "final",
            "--step",
            "2",
            "--reviewer",
            "zhangxia",
            "--yes",
        )


if __name__ == "__main__":
    unittest.main()
