from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from a2a_runtime.core.clock import Clock
from a2a_runtime.core.constants import MessageType, Role, TaskStatus
from a2a_runtime.models.message import Message
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.state_repo import StateRepo

from tests.cli_helpers import make_project, run_cli


class CLIMutatingBlockerTests(unittest.TestCase):
    def test_blocker_request_only_writes_message(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)

            code, _, _ = run_cli(
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
                "Add src/services/settings.ts to file-change-plan",
                "--yes",
            )

            self.assertEqual(code, 0)
            messages = MessageRepo(paths).list_messages("T-2026-001")
            self.assertEqual(len(messages), 1)
            self.assertIn("blocker-request", messages[0].name)
            self.assertEqual(list(paths.blockers_dir("T-2026-001").glob("*.md")), [])
            self.assertEqual(StateRepo(paths).read("T-2026-001").current_status, TaskStatus.DEVELOPER_PROCESSING)

    def test_blocker_create_from_request_creates_formal_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            message_id = self._create_request(root, paths)

            code, _, _ = run_cli("--project-root", str(root), "blocker", "create", "--from-request", message_id, "--yes")

            self.assertEqual(code, 0)
            blockers = list(paths.blockers_dir("T-2026-001").glob("*.md"))
            self.assertEqual(len(blockers), 1)
            state = StateRepo(paths).read("T-2026-001")
            self.assertEqual(state.current_status, TaskStatus.BLOCKED)
            self.assertIsNotNone(state.active_blocker)
            self.assertIsNotNone(state.blocked_context)
            self.assertEqual(state.blockers_history, [state.active_blocker])

    def test_blocker_create_rejects_gate_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            message = Message(
                message_id="M-T-2026-001-001",
                task_id="T-2026-001",
                from_agent=Role.DEVELOPER,
                to_agent=Role.CONTROLLER,
                message_type=MessageType.GATE_FAILURE,
                intent="write_gate_failed",
                summary="Gate failed",
                payload={"reason": "not developer phase"},
                required_response=True,
                created_at=Clock().now_iso(),
            )
            MessageRepo(paths).write_message(message)

            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "blocker",
                "create",
                "--from-request",
                message.message_id,
                "--yes",
            )

            self.assertNotEqual(code, 0)
            self.assertEqual(list(paths.blockers_dir("T-2026-001").glob("*.md")), [])

    def test_blocker_resolve_success_restores_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            blocker_id = self._create_formal_blocker(root, paths)

            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "blocker",
                "resolve",
                blocker_id,
                "--missing-artifacts-resolved",
                "--yes",
            )

            self.assertEqual(code, 0)
            state = StateRepo(paths).read("T-2026-001")
            self.assertEqual(state.current_status, TaskStatus.ARCHITECT_PROCESSING)
            self.assertEqual(state.current_agent, Role.ARCHITECT)
            self.assertIsNone(state.active_blocker)
            self.assertIsNone(state.blocked_context)
            self.assertEqual(state.blockers_history, [blocker_id])

    def test_blocker_resolve_requires_missing_artifacts_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            blocker_id = self._create_formal_blocker(root, paths)

            code, _, _ = run_cli("--project-root", str(root), "blocker", "resolve", blocker_id, "--yes")

            self.assertNotEqual(code, 0)
            self.assertEqual(StateRepo(paths).read("T-2026-001").current_status, TaskStatus.BLOCKED)

    def test_blocker_resolve_rejects_resume_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            blocker_id = self._create_formal_blocker(root, paths)

            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "blocker",
                "resolve",
                blocker_id,
                "--resume-to-status",
                "qa_processing",
                "--missing-artifacts-resolved",
                "--yes",
            )

            self.assertNotEqual(code, 0)
            self.assertEqual(StateRepo(paths).read("T-2026-001").current_status, TaskStatus.BLOCKED)

    def _create_request(self, root: Path, paths) -> str:
        code, _, _ = run_cli(
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
            "Add src/services/settings.ts to file-change-plan",
            "--yes",
        )
        self.assertEqual(code, 0)
        return MessageRepo(paths).read_message(MessageRepo(paths).list_messages("T-2026-001")[0]).message_id

    def _create_formal_blocker(self, root: Path, paths) -> str:
        message_id = self._create_request(root, paths)
        code, _, _ = run_cli("--project-root", str(root), "blocker", "create", "--from-request", message_id, "--yes")
        self.assertEqual(code, 0)
        state = StateRepo(paths).read("T-2026-001")
        self.assertIsNotNone(state.active_blocker)
        return state.active_blocker or ""


if __name__ == "__main__":
    unittest.main()
