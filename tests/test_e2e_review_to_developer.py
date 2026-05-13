from __future__ import annotations

import unittest

from a2a_runtime.core.constants import ReviewStatus, Role, TaskStatus
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.state_repo import StateRepo

from tests.cli_helpers import run_cli
from tests.e2e_helpers import (
    create_minimal_a2a_protocol_tree,
    create_ready_architect_artifacts,
    create_task_with_cli,
    create_temp_project_root,
    set_state,
)


class E2EReviewToDeveloperTests(unittest.TestCase):
    def test_approve_architect_review_enters_developer_processing(self) -> None:
        with create_temp_project_root() as root:
            create_minimal_a2a_protocol_tree(root)
            task_id = create_task_with_cli(root)
            paths = A2APaths(root)
            create_ready_architect_artifacts(paths, task_id)
            set_state(
                paths,
                task_id,
                current_status=TaskStatus.HUMAN_REVIEW_REQUIRED,
                previous_status=TaskStatus.ARCHITECT_COMPLETED,
                current_agent=Role.HUMAN,
                human_review_status=ReviewStatus.PENDING,
            )

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
            self.assertEqual(code, 0, out)
            code, out, _ = run_cli(
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

            self.assertEqual(code, 0, out)
            self.assertTrue(paths.human_reviews_dir(task_id).joinpath("architect-review.md").exists())
            state = StateRepo(paths).read(task_id)
            self.assertEqual(state.human_review_status, ReviewStatus.APPROVED)
            self.assertEqual(state.current_status, TaskStatus.DEVELOPER_PROCESSING)
            self.assertEqual(state.current_agent, Role.DEVELOPER)
            messages = [path.name for path in MessageRepo(paths).list_messages(task_id)]
            self.assertTrue(any("architect-review-status-approved" in name for name in messages))
            self.assertTrue(any("human-review-to-developer-handoff" in name for name in messages))

    def test_reviewer_controller_rejected(self) -> None:
        with create_temp_project_root() as root:
            paths, task_id = self._review_ready_task(root)

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
                "controller",
                "--yes",
            )

            self.assertNotEqual(code, 0)
            self.assertFalse(paths.human_reviews_dir(task_id).joinpath("architect-review.md").exists())

    def test_reviewer_developer_rejected(self) -> None:
        with create_temp_project_root() as root:
            paths, task_id = self._review_ready_task(root)

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
                "developer",
                "--yes",
            )

            self.assertNotEqual(code, 0)
            self.assertFalse(paths.human_reviews_dir(task_id).joinpath("architect-review.md").exists())

    def test_reject_architect_review_does_not_enter_developer_processing(self) -> None:
        with create_temp_project_root() as root:
            paths, task_id = self._review_ready_task(root)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "review",
                "reject",
                "--stage",
                "architect",
                "--reviewer",
                "zhangxia",
                "--reason",
                "file-change-plan range is too broad",
                "--yes",
            )

            self.assertEqual(code, 0, out)
            state = StateRepo(paths).read(task_id)
            self.assertEqual(state.human_review_status, ReviewStatus.REJECTED)
            self.assertEqual(state.current_status, TaskStatus.ARCHITECT_PROCESSING)
            self.assertNotEqual(state.current_status, TaskStatus.DEVELOPER_PROCESSING)

    def _review_ready_task(self, root):
        create_minimal_a2a_protocol_tree(root)
        task_id = create_task_with_cli(root)
        paths = A2APaths(root)
        create_ready_architect_artifacts(paths, task_id)
        set_state(
            paths,
            task_id,
            current_status=TaskStatus.HUMAN_REVIEW_REQUIRED,
            previous_status=TaskStatus.ARCHITECT_COMPLETED,
            current_agent=Role.HUMAN,
            human_review_status=ReviewStatus.PENDING,
        )
        return paths, task_id


if __name__ == "__main__":
    unittest.main()
