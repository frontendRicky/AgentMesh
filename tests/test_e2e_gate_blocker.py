from __future__ import annotations

import unittest

from a2a_runtime.core.clock import Clock
from a2a_runtime.core.constants import MessageType, ReviewStatus, Role, TaskStatus
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.message import Message
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


class E2EGateBlockerTests(unittest.TestCase):
    def test_developer_gate_dry_run_allowed_blocker_and_risk_paths(self) -> None:
        with create_temp_project_root() as root:
            paths, task_id = self._developer_ready_task(root)

            code, out, _ = run_cli("--project-root", str(root), "gate", "developer", "--path", "src/app.py", "--operation", "modify")
            self.assertEqual(code, 0)
            self.assertIn("Allowed: true", out)

            code, out, _ = run_cli("--project-root", str(root), "gate", "developer", "--path", "src/missing.py", "--operation", "modify")
            self.assertEqual(code, 1)
            self.assertIn("Failure Type: blocker_request", out)

            code, out, _ = run_cli("--project-root", str(root), "gate", "developer", "--path", "package.json", "--operation", "modify")
            self.assertEqual(code, 1)
            self.assertIn("Failure Type: risk_decision_required", out)
            self.assertEqual(len(MessageRepo(paths).list_messages(task_id)), 1)
            self.assertEqual(list(paths.blockers_dir(task_id).glob("*.md")), [])

    def test_blocker_request_create_and_resolve(self) -> None:
        with create_temp_project_root() as root:
            paths, task_id = self._developer_ready_task(root)
            before_status = StateRepo(paths).read(task_id).current_status

            request_id = self._blocker_request(root, paths, task_id)
            self.assertEqual(list(paths.blockers_dir(task_id).glob("*.md")), [])
            self.assertEqual(StateRepo(paths).read(task_id).current_status, before_status)

            code, out, _ = run_cli("--project-root", str(root), "blocker", "create", "--from-request", request_id, "--yes")
            self.assertEqual(code, 0, out)
            state = StateRepo(paths).read(task_id)
            self.assertEqual(state.current_status, TaskStatus.BLOCKED)
            self.assertIsNotNone(state.active_blocker)
            self.assertIsNotNone(state.blocked_context)

            blocker_id = state.active_blocker or ""
            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "blocker",
                "resolve",
                blocker_id,
                "--missing-artifacts-resolved",
                "--yes",
            )
            self.assertEqual(code, 0, out)
            state = StateRepo(paths).read(task_id)
            self.assertEqual(state.current_status, TaskStatus.ARCHITECT_PROCESSING)
            self.assertEqual(state.current_agent, Role.ARCHITECT)

    def test_gate_failure_cannot_be_promoted_to_formal_blocker(self) -> None:
        with create_temp_project_root() as root:
            paths, task_id = self._developer_ready_task(root)
            repo = MessageRepo(paths)
            seq = repo.next_sequence(task_id)
            message = Message(
                message_id=f"M-{task_id}-{seq:03d}",
                task_id=task_id,
                from_agent=Role.DEVELOPER,
                to_agent=Role.CONTROLLER,
                message_type=MessageType.GATE_FAILURE,
                intent="write_gate_failed",
                summary="Gate failure",
                payload={"reason": "wrong state"},
                required_response=True,
                created_at=Clock().now_iso(),
            )
            repo.write_message(message)

            code, _, _ = run_cli("--project-root", str(root), "blocker", "create", "--from-request", message.message_id, "--yes")

            self.assertNotEqual(code, 0)
            self.assertEqual(list(paths.blockers_dir(task_id).glob("*.md")), [])
            self.assertNotEqual(StateRepo(paths).read(task_id).current_status, TaskStatus.BLOCKED)

    def _developer_ready_task(self, root):
        create_minimal_a2a_protocol_tree(root)
        task_id = create_task_with_cli(root)
        paths = A2APaths(root)
        create_ready_architect_artifacts(paths, task_id)
        set_state(
            paths,
            task_id,
            current_status=TaskStatus.DEVELOPER_PROCESSING,
            previous_status=TaskStatus.HUMAN_REVIEW_REQUIRED,
            current_agent=Role.DEVELOPER,
            human_review_status=ReviewStatus.APPROVED,
        )
        return paths, task_id

    def _blocker_request(self, root, paths, task_id: str) -> str:
        code, out, _ = run_cli(
            "--project-root",
            str(root),
            "blocker",
            "request",
            "--from",
            "developer",
            "--reason",
            "file-change-plan missing src/services/settings.ts",
            "--resume-to-agent",
            "architect",
            "--resume-to-status",
            "architect_processing",
            "--missing-artifact",
            "file_change_plan",
            "--required-fix",
            "Add missing file to file-change-plan",
            "--yes",
        )
        self.assertEqual(code, 0, out)
        request = [path for path in MessageRepo(paths).list_messages(task_id) if "blocker-request" in path.name][0]
        return MessageRepo(paths).read_message(request).message_id


if __name__ == "__main__":
    unittest.main()
