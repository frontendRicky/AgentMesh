from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import ReviewStatus, ReviewType, ReviewVerdict, RiskDecisionAction, RiskSeverity, Role, TaskStatus
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.review import ReviewRecord
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.review_repo import ReviewRepo
from a2a_runtime.repositories.state_repo import StateRepo
from tests.cli_helpers import make_finalizable_project, make_project, write_risk
from tests.e2e_helpers import create_approved_architect_review, create_ready_architect_artifacts, create_ready_developer_artifacts, create_ready_pm_artifacts, set_state


class CLISubprocessMutatingFailureTests(unittest.TestCase):
    def run_subprocess(self, root: Path, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, "-m", "a2a_runtime.cli", "--project-root", str(root), *args]
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)
        return subprocess.run(command, text=True, capture_output=True, check=False, env=merged_env)

    def test_gate_developer_monorepo_ci_forbidden_subprocess(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)

            result = self.run_subprocess(
                root,
                "--json",
                "gate",
                "developer",
                "--path",
                "apps/web/.github/workflows/deploy.yml",
                "--operation",
                "modify",
            )

            self.assertNotEqual(result.returncode, 0, result.stdout)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["allowed"])
            self.assertEqual(payload["failure_type"], "risk_decision_required")
            self.assertIn("forbidden ci/cd file", payload["reason"])
            self.assertEqual(MessageRepo(paths).list_messages("T-2026-001"), [])
            self.assertEqual(list(paths.blockers_dir("T-2026-001").glob("*.md")), [])
            self.assertFalse((root / "apps").exists())

    def test_risk_decide_by_mismatch_warning_subprocess(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")

            result = self.run_subprocess(
                root,
                "--json",
                "risk",
                "decide",
                risk_id,
                "--decision",
                "send_to_architect",
                "--reason",
                "需要重新设计权限控制点",
                "--by",
                "alice",
                "--yes",
                env={"USER": "bob"},
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])
            self.assertTrue(payload["warnings"])
            self.assertEqual(payload["local_user"], "bob")
            self.assertTrue(payload["user_mismatch_warning"])
            messages = [
                path
                for path in MessageRepo(paths).list_messages("T-2026-001")
                if "risk-decision" in path.name and "from-human" in path.name
            ]
            decision_payload = MessageRepo(paths).read_message(messages[0]).payload
            self.assertEqual(decision_payload["local_user"], "bob")
            self.assertTrue(decision_payload["user_mismatch_warning"])

    def test_final_review_step2_missing_test_report_rejected_subprocess(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            task_id = "T-2026-001"
            create_ready_pm_artifacts(paths, task_id)
            create_ready_architect_artifacts(paths, task_id)
            create_ready_developer_artifacts(paths, task_id)
            create_approved_architect_review(paths, task_id)
            ReviewRepo(paths).write_review(
                ReviewRecord(
                    review_id=f"R-{task_id}-final",
                    task_id=task_id,
                    review_type=ReviewType.FINAL_REVIEW,
                    reviewed_artifacts=["test_report", "acceptance_checklist"],
                    reviewer="zhangxia",
                    reviewed_at="2026-05-12T10:00:00+08:00",
                    verdict=ReviewVerdict.APPROVED,
                    issues=[],
                    followup_required=False,
                ),
                overwrite=True,
            )
            set_state(
                paths,
                task_id,
                current_status=TaskStatus.FINAL_REVIEW_REQUIRED,
                previous_status=TaskStatus.QA_COMPLETED,
                current_agent=Role.HUMAN,
                human_review_status=ReviewStatus.APPROVED,
                final_review_status=ReviewStatus.APPROVED,
            )

            result = self.run_subprocess(
                root,
                "--json",
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

            self.assertNotEqual(result.returncode, 0, result.stdout)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            state = StateRepo(paths).read(task_id)
            self.assertNotEqual(state.current_status, TaskStatus.COMPLETED)
            self.assertFalse((paths.task_dir(task_id) / "artifacts/final/final-delivery.md").exists())

    def test_finalize_unresolved_p0_rejected_subprocess(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_finalizable_project(root)
            write_risk(
                paths,
                "T-2026-001",
                severity=RiskSeverity.P0_BLOCKER,
                options=[RiskDecisionAction.SEND_TO_QA, RiskDecisionAction.CANCEL_TASK],
            )

            result = self.run_subprocess(root, "--json", "finalize", "--yes")

            self.assertEqual(result.returncode, 2, result.stdout)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])
            self.assertIn("unresolved blocking risk", payload["errors"][0]["message"])
            self.assertFalse((paths.task_dir("T-2026-001") / "artifacts/final/final-delivery.md").exists())


if __name__ == "__main__":
    unittest.main()
