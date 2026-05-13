import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import ArtifactType, ReviewStatus, Role, TaskStatus
from a2a_runtime.repositories.review_repo import ReviewRepo
from tests.cli_helpers import make_project, run_cli, write_artifact, write_state


def write_architect_review_artifacts(paths, task_id: str = "T-2026-001") -> None:
    write_artifact(paths, task_id, ArtifactType.TECH_PLAN, Role.ARCHITECT)
    write_artifact(paths, task_id, ArtifactType.RISK_PLAN, Role.ARCHITECT)


def write_final_review_artifacts(paths, task_id: str = "T-2026-001", body: str = "# Test Report\nstatus: pass\n") -> None:
    write_artifact(paths, task_id, ArtifactType.TEST_REPORT, Role.QA, body=body)
    write_artifact(paths, task_id, ArtifactType.ACCEPTANCE_CHECKLIST, Role.QA)


class CLIReviewTests(unittest.TestCase):
    def test_review_approve_requires_explicit_step(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "review",
                "approve",
                "--stage",
                "architect",
                "--reviewer",
                "zhangxia",
                "--yes",
            )

            self.assertEqual(code, 4)
            self.assertIn("--step 1 or --step 2", out)

    def test_architect_approve_missing_required_artifact_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_state(paths, "T-2026-001", status=TaskStatus.HUMAN_REVIEW_REQUIRED)
            write_artifact(paths, "T-2026-001", ArtifactType.TECH_PLAN, Role.ARCHITECT)
            write_artifact(paths, "T-2026-001", ArtifactType.RISK_PLAN, Role.ARCHITECT)
            (paths.task_dir("T-2026-001") / "artifacts/architect/file-change-plan.md").unlink()

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "review",
                "approve",
                "--stage",
                "architect",
                "--step",
                "1",
                "--reviewer",
                "zhangxia",
                "--yes",
            )

            self.assertNotEqual(code, 0)
            self.assertIn("file_change_plan", out)

    def test_review_approve_architect_double_step(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_state(paths, "T-2026-001", status=TaskStatus.HUMAN_REVIEW_REQUIRED)
            write_architect_review_artifacts(paths)

            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "review",
                "approve",
                "--stage",
                "architect",
                "--step",
                "1",
                "--reviewer",
                "zhangxia",
                "--yes",
            )
            self.assertEqual(code, 0)
            state = __import__("a2a_runtime.repositories.state_repo", fromlist=["StateRepo"]).StateRepo(paths).read("T-2026-001")
            self.assertEqual(state.human_review_status, ReviewStatus.APPROVED)
            self.assertEqual(state.current_status, TaskStatus.HUMAN_REVIEW_REQUIRED)

            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "review",
                "approve",
                "--stage",
                "architect",
                "--step",
                "2",
                "--reviewer",
                "zhangxia",
                "--yes",
            )

            self.assertEqual(code, 0)
            state = __import__("a2a_runtime.repositories.state_repo", fromlist=["StateRepo"]).StateRepo(paths).read("T-2026-001")
            self.assertEqual(state.human_review_status, ReviewStatus.APPROVED)
            self.assertEqual(state.current_status, TaskStatus.DEVELOPER_PROCESSING)

    def test_review_approve_final_double_step(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_state(paths, "T-2026-001", status=TaskStatus.FINAL_REVIEW_REQUIRED)
            write_final_review_artifacts(paths)

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
            self.assertEqual(code, 0)
            state = __import__("a2a_runtime.repositories.state_repo", fromlist=["StateRepo"]).StateRepo(paths).read("T-2026-001")
            self.assertEqual(state.final_review_status, ReviewStatus.APPROVED)
            self.assertEqual(state.current_status, TaskStatus.FINAL_REVIEW_REQUIRED)

            code, _, _ = run_cli(
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

            self.assertEqual(code, 0)
            state = __import__("a2a_runtime.repositories.state_repo", fromlist=["StateRepo"]).StateRepo(paths).read("T-2026-001")
            self.assertEqual(state.final_review_status, ReviewStatus.APPROVED)
            self.assertEqual(state.current_status, TaskStatus.COMPLETED)

    def test_reviewer_controller_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_state(paths, "T-2026-001", status=TaskStatus.HUMAN_REVIEW_REQUIRED)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
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

            self.assertNotEqual(code, 0)
            self.assertIn("reviewer", out)

    def test_reviewer_developer_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_state(paths, "T-2026-001", status=TaskStatus.HUMAN_REVIEW_REQUIRED)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "review",
                "approve",
                "--stage",
                "architect",
                "--step",
                "1",
                "--reviewer",
                "developer",
                "--yes",
            )

            self.assertNotEqual(code, 0)
            self.assertIn("reviewer", out)

    def test_reject_without_reason_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "review",
                "reject",
                "--stage",
                "architect",
                "--step",
                "1",
                "--reviewer",
                "zhangxia",
                "--yes",
            )

            self.assertEqual(code, 4)
            self.assertIn("reason", out)

    def test_reject_architect_does_not_enter_developer_processing(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_state(paths, "T-2026-001", status=TaskStatus.HUMAN_REVIEW_REQUIRED)

            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "review",
                "reject",
                "--stage",
                "architect",
                "--step",
                "1",
                "--reviewer",
                "zhangxia",
                "--reason",
                "too broad",
                "--yes",
            )

            self.assertEqual(code, 0)
            state = __import__("a2a_runtime.repositories.state_repo", fromlist=["StateRepo"]).StateRepo(paths).read("T-2026-001")
            self.assertEqual(state.current_status, TaskStatus.ARCHITECT_PROCESSING)

    def test_reject_final_does_not_enter_completed(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_state(paths, "T-2026-001", status=TaskStatus.FINAL_REVIEW_REQUIRED)
            write_final_review_artifacts(paths)
            write_final_review_artifacts(paths)

            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "review",
                "reject",
                "--stage",
                "final",
                "--reviewer",
                "zhangxia",
                "--reason",
                "qa failed",
                "--yes",
            )

            self.assertEqual(code, 0)
            state = __import__("a2a_runtime.repositories.state_repo", fromlist=["StateRepo"]).StateRepo(paths).read("T-2026-001")
            self.assertNotEqual(state.current_status, TaskStatus.COMPLETED)

    def test_review_dry_run_writes_no_review(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_state(paths, "T-2026-001", status=TaskStatus.HUMAN_REVIEW_REQUIRED)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "review",
                "approve",
                "--stage",
                "architect",
                "--step",
                "1",
                "--reviewer",
                "zhangxia",
                "--dry-run",
            )

            self.assertEqual(code, 0)
            self.assertIn("Dry Run: true", out)
            self.assertIsNone(ReviewRepo(paths).find_architect_review("T-2026-001"))

    def test_approve_final_does_not_auto_finalize(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_state(paths, "T-2026-001", status=TaskStatus.FINAL_REVIEW_REQUIRED)
            write_final_review_artifacts(paths)

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

            self.assertEqual(code, 0)
            code, _, _ = run_cli(
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
            self.assertEqual(code, 0)
            self.assertFalse((paths.task_dir("T-2026-001") / "artifacts/final/final-delivery.md").exists())


if __name__ == "__main__":
    unittest.main()
