import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import MessageType, ReviewStatus, Role, TaskStatus
from a2a_runtime.core.errors import BlockerError, StateMachineError
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.state import State
from a2a_runtime.repositories.blocker_repo import BlockerRepo
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.services.blocker_service import (
    REQUIRED_BLOCKER_REQUEST_PAYLOAD_FIELDS,
    BlockerService,
)
from a2a_runtime.services.gate_service import GateCheckResult, GateService
from a2a_runtime.core.constants import GateFailureType


def make_developer_state() -> State:
    return State(
        task_id="T-2026-001",
        current_status=TaskStatus.DEVELOPER_PROCESSING,
        previous_status=TaskStatus.HUMAN_REVIEW_REQUIRED,
        current_agent=Role.DEVELOPER,
        next_agent=Role.QA,
        allowed_next_statuses=[TaskStatus.DEVELOPER_COMPLETED, TaskStatus.BLOCKED],
        human_review_status=ReviewStatus.APPROVED,
        final_review_status=ReviewStatus.NOT_REQUIRED,
        updated_at="2026-05-12T10:00:00+08:00",
    )


class BlockerFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.paths = A2APaths(Path(self.tmp.name))
        self.state_repo = StateRepo(self.paths)
        self.message_repo = MessageRepo(self.paths)
        self.blocker_repo = BlockerRepo(self.paths)
        self.service = BlockerService(
            message_repo=self.message_repo,
            blocker_repo=self.blocker_repo,
            state_repo=self.state_repo,
        )
        self.state_repo.write(
            "T-2026-001",
            make_developer_state(),
            actor=Role.CONTROLLER,
            body="# State",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def create_request(self):
        return self.service.create_blocker_request(
            task_id="T-2026-001",
            from_agent=Role.DEVELOPER,
            blocked_from_status=TaskStatus.DEVELOPER_PROCESSING,
            resume_to_agent=Role.ARCHITECT,
            resume_to_status=TaskStatus.DEVELOPER_PROCESSING,
            blocking_reason="file-change-plan missing src/api.py",
            missing_artifacts=["file_change_plan"],
            required_fix="add src/api.py to file-change-plan",
        )

    def request_path(self, message_id: str):
        seq = int(message_id.rsplit("-", 1)[1])
        return self.message_repo.build_message_path(
            "T-2026-001",
            Role.DEVELOPER,
            seq,
            "blocker_request",
        )

    def test_professional_agent_creates_complete_blocker_request_message(self) -> None:
        message = self.create_request()

        self.assertEqual(message.message_type, MessageType.BLOCKER)
        self.assertEqual(message.intent, "blocker_request")
        self.assertTrue(REQUIRED_BLOCKER_REQUEST_PAYLOAD_FIELDS.issubset(message.payload))
        self.assertEqual(self.blocker_repo.list_blockers("T-2026-001"), [])
        self.assertEqual(
            self.state_repo.read("T-2026-001").current_status,
            TaskStatus.DEVELOPER_PROCESSING,
        )

    def test_controller_creates_formal_blocker_and_blocks_state(self) -> None:
        request = self.create_request()
        result = self.service.create_formal_blocker_from_request(self.request_path(request.message_id))
        state = self.state_repo.read("T-2026-001")

        self.assertEqual(result.blocker.created_by, "controller")
        self.assertEqual(state.current_status, TaskStatus.BLOCKED)
        self.assertEqual(state.active_blocker, result.blocker.blocker_id)
        self.assertIsNotNone(state.blocked_context)
        self.assertIn(result.blocker.blocker_id, state.blockers_history)

    def test_resolve_rejects_when_missing_artifacts_are_unresolved(self) -> None:
        request = self.create_request()
        self.service.create_formal_blocker_from_request(self.request_path(request.message_id))

        with self.assertRaises(StateMachineError):
            self.service.resolve_blocker(
                task_id="T-2026-001",
                resume_to_status=TaskStatus.DEVELOPER_PROCESSING,
                resume_to_agent=Role.ARCHITECT,
                missing_artifacts_resolved=False,
            )

    def test_resolve_rejects_when_resume_status_does_not_match(self) -> None:
        request = self.create_request()
        self.service.create_formal_blocker_from_request(self.request_path(request.message_id))

        with self.assertRaises(StateMachineError):
            self.service.resolve_blocker(
                task_id="T-2026-001",
                resume_to_status=TaskStatus.QA_PROCESSING,
                resume_to_agent=Role.ARCHITECT,
                missing_artifacts_resolved=True,
            )

    def test_resolve_success_restores_state_and_keeps_history(self) -> None:
        request = self.create_request()
        formal = self.service.create_formal_blocker_from_request(self.request_path(request.message_id))
        self.service.resolve_blocker(
            task_id="T-2026-001",
            resume_to_status=TaskStatus.DEVELOPER_PROCESSING,
            resume_to_agent=Role.ARCHITECT,
            missing_artifacts_resolved=True,
        )
        state = self.state_repo.read("T-2026-001")

        self.assertEqual(state.current_status, TaskStatus.DEVELOPER_PROCESSING)
        self.assertIsNone(state.active_blocker)
        self.assertIsNone(state.blocked_context)
        self.assertIn(formal.blocker.blocker_id, state.blockers_history)

    def test_gate_failure_is_not_upgraded_to_formal_blocker(self) -> None:
        gate_service = GateService(message_repo=self.message_repo)
        state = self.state_repo.read("T-2026-001")
        gate_message = gate_service.create_gate_failure_message(
            task_id="T-2026-001",
            state=state,
            gate_result=GateCheckResult(
                allowed=False,
                failure_type=GateFailureType.GATE_FAILURE,
                failed_conditions=["current_agent_not_developer"],
                reason="agent mismatch",
                recommended_next_action="write gate_failure message",
            ),
            attempted_operation="Write",
            target_path="src/settings.py",
        )
        gate_path = self.message_repo.build_message_path(
            "T-2026-001",
            Role.DEVELOPER,
            int(gate_message.message_id.rsplit("-", 1)[1]),
            "write_gate_failed",
        )

        with self.assertRaises(BlockerError):
            self.service.create_formal_blocker_from_request(gate_path)
        self.assertEqual(self.blocker_repo.list_blockers("T-2026-001"), [])


if __name__ == "__main__":
    unittest.main()
