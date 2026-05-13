from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import ArtifactType, ReviewStatus, Role, TaskStatus
from a2a_runtime.core.errors import ReviewError
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.repositories.review_repo import ReviewRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.services.review_service import ReviewService
from tests.cli_helpers import make_project, run_cli, write_artifact, write_state


class FinalReviewTestReportRequiredTests(unittest.TestCase):
    def test_missing_test_report_step_2_rejects(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_state(paths, "T-2026-001", status=TaskStatus.FINAL_REVIEW_REQUIRED)
            write_artifact(paths, "T-2026-001", ArtifactType.ACCEPTANCE_CHECKLIST, Role.QA)
            code, _, _ = run_cli(
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
            self.assertNotEqual(code, 0)
            self.assertIsNone(ReviewRepo(paths).find_final_review("T-2026-001"))

    def test_fail_and_blocked_reports_step_2_reject(self) -> None:
        for body in ["status: fail\n", "| case | status |\n| login | fail |\n", "status: blocked\n"]:
            with self.subTest(body=body):
                with TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    paths = make_project(root)
                    write_state(paths, "T-2026-001", status=TaskStatus.FINAL_REVIEW_REQUIRED)
                    write_artifact(paths, "T-2026-001", ArtifactType.TEST_REPORT, Role.QA, body=body)
                    write_artifact(paths, "T-2026-001", ArtifactType.ACCEPTANCE_CHECKLIST, Role.QA)
                    code, out, _ = run_cli(
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
                    self.assertEqual(code, 0, out)
                    code, out, _ = run_cli(
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
                    self.assertNotEqual(code, 0)
                    self.assertNotEqual(StateRepo(paths).read("T-2026-001").current_status, TaskStatus.COMPLETED)

    def test_clean_report_step_2_completes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_state(paths, "T-2026-001", status=TaskStatus.FINAL_REVIEW_REQUIRED)
            write_artifact(paths, "T-2026-001", ArtifactType.TEST_REPORT, Role.QA, body="# Test Report\nstatus: pass\n")
            write_artifact(paths, "T-2026-001", ArtifactType.ACCEPTANCE_CHECKLIST, Role.QA)
            self.assertEqual(
                run_cli("--project-root", str(root), "review", "approve", "--stage", "final", "--step", "1", "--reviewer", "zhangxia", "--yes")[0],
                0,
            )
            self.assertEqual(
                run_cli("--project-root", str(root), "review", "approve", "--stage", "final", "--step", "2", "--reviewer", "zhangxia", "--yes")[0],
                0,
            )
            self.assertEqual(StateRepo(paths).read("T-2026-001").current_status, TaskStatus.COMPLETED)

    def test_service_step_2_rechecks_test_report(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_state(
                paths,
                "T-2026-001",
                status=TaskStatus.FINAL_REVIEW_REQUIRED,
                human_review_status=ReviewStatus.APPROVED,
            )
            write_artifact(paths, "T-2026-001", ArtifactType.TEST_REPORT, Role.QA, body="status: fail\n")
            write_artifact(paths, "T-2026-001", ArtifactType.ACCEPTANCE_CHECKLIST, Role.QA)
            service = ReviewService(
                review_repo=ReviewRepo(paths),
                state_repo=StateRepo(paths),
                message_repo=__import__("a2a_runtime.repositories.message_repo", fromlist=["MessageRepo"]).MessageRepo(paths),
                artifact_repo=__import__("a2a_runtime.repositories.artifact_repo", fromlist=["ArtifactRepo"]).ArtifactRepo(paths),
            )
            service.create_final_review(
                task_id="T-2026-001",
                reviewer="zhangxia",
                verdict="approved",
                reviewed_artifacts=["test_report", "acceptance_checklist"],
                issues=[],
                followup_required=False,
            )
            service.approve_final_review_step_1("T-2026-001")

            with self.assertRaises(ReviewError):
                service.approve_final_review_step_2("T-2026-001")


if __name__ == "__main__":
    unittest.main()
