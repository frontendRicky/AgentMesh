import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import GateFailureType, ReviewStatus, Role, TaskStatus
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.state import State
from a2a_runtime.repositories.blocker_repo import BlockerRepo
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.services.gate_service import GateCheckResult, GateService


def make_state(status: TaskStatus = TaskStatus.HUMAN_REVIEW_REQUIRED) -> State:
    return State(
        task_id="T-2026-001",
        current_status=status,
        previous_status=status,
        current_agent=Role.HUMAN,
        next_agent=Role.DEVELOPER,
        allowed_next_statuses=[],
        human_review_status=ReviewStatus.PENDING,
        final_review_status=ReviewStatus.NOT_REQUIRED,
        updated_at="2026-05-12T10:00:00+08:00",
    )


class GateFailureTests(unittest.TestCase):
    def test_create_gate_failure_message_does_not_create_blocker_or_change_state(self) -> None:
        with TemporaryDirectory() as tmp:
            paths = A2APaths(Path(tmp))
            state_repo = StateRepo(paths)
            message_repo = MessageRepo(paths)
            blocker_repo = BlockerRepo(paths)
            state = make_state()
            state_repo.write("T-2026-001", state, actor=Role.CONTROLLER, body="# State")

            service = GateService(message_repo=message_repo)
            message = service.create_gate_failure_message(
                task_id="T-2026-001",
                state=state,
                gate_result=GateCheckResult(
                    allowed=False,
                    failure_type=GateFailureType.GATE_FAILURE,
                    failed_conditions=["current_status_not_developer_processing"],
                    reason="not developer_processing",
                    recommended_next_action="write gate_failure message",
                ),
                attempted_operation="Write",
                target_path="src/settings.py",
            )

            self.assertEqual(message.message_type.value, "gate_failure")
            self.assertEqual(message.intent, "write_gate_failed")
            self.assertIn("five_gate_conditions", message.payload)
            self.assertEqual(message.payload["tool"], "gate_service")
            self.assertTrue(message.payload["reason_for_user"])
            self.assertEqual(message.payload["target_path"], "src/settings.py")
            self.assertEqual(message.payload["operation"], "Write")
            self.assertEqual(blocker_repo.list_blockers("T-2026-001"), [])
            self.assertEqual(
                state_repo.read("T-2026-001").current_status,
                TaskStatus.HUMAN_REVIEW_REQUIRED,
            )


if __name__ == "__main__":
    unittest.main()
