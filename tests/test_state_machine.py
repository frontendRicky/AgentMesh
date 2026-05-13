import unittest

from a2a_runtime.core.constants import (
    MessageType,
    QAStatus,
    RiskSeverity,
    ReviewStatus,
    Role,
    TaskStatus,
    normalize_role,
    role_to_wire,
)
from a2a_runtime.core.errors import StateMachineError
from a2a_runtime.models.state import BlockedContext, State
from a2a_runtime.services.state_machine import StateMachine


def make_state(
    status: TaskStatus,
    *,
    human_review_status: ReviewStatus = ReviewStatus.NOT_REQUIRED,
    final_review_status: ReviewStatus = ReviewStatus.NOT_REQUIRED,
    blocked_context: BlockedContext | None = None,
) -> State:
    return State(
        task_id="T-2026-001",
        current_status=status,
        previous_status=status,
        current_agent=Role.CONTROLLER,
        next_agent=Role.PM,
        allowed_next_statuses=[],
        human_review_status=human_review_status,
        final_review_status=final_review_status,
        updated_at="2026-05-12T10:00:00+08:00",
        active_blocker=blocked_context.blocker_id if blocked_context else None,
        blockers_history=[blocked_context.blocker_id] if blocked_context else [],
        blocked_context=blocked_context,
    )


def make_blocked_context(
    *,
    resume_to_status: TaskStatus = TaskStatus.DEVELOPER_PROCESSING,
    resume_to_agent: Role = Role.DEVELOPER,
) -> BlockedContext:
    return BlockedContext(
        blocker_id="B-T-2026-001-001",
        blocked_from_agent=Role.DEVELOPER,
        blocked_from_status=TaskStatus.DEVELOPER_PROCESSING,
        resume_to_agent=resume_to_agent,
        resume_to_status=resume_to_status,
        blocking_reason="missing file change plan entry",
        missing_artifacts=["file_change_plan"],
        required_fix="add missing file change plan entry",
    )


class StateMachineEnumTests(unittest.TestCase):
    def test_state_status_enum_is_frozen_to_fourteen_values(self) -> None:
        values = {status.value for status in TaskStatus}

        self.assertEqual(len(values), 14)
        self.assertIn("developer_processing", values)
        self.assertNotIn("human_review_approved", values)
        self.assertNotIn("final_approved", values)

    def test_roles_are_canonical_and_read_side_accepts_dev_alias(self) -> None:
        values = {role.value for role in Role}

        self.assertEqual(values, {"pm", "architect", "developer", "qa", "controller", "human"})
        self.assertEqual(normalize_role("dev"), Role.DEVELOPER)
        self.assertEqual(role_to_wire(normalize_role("dev")), "developer")

    def test_message_type_supports_gate_failure(self) -> None:
        self.assertEqual(MessageType.GATE_FAILURE.value, "gate_failure")

    def test_qa_status_supports_manual_required(self) -> None:
        values = {status.value for status in QAStatus}

        self.assertEqual(values, {"pass", "fail", "blocked", "not_executed", "manual_required"})

    def test_risk_severity_supports_required_levels(self) -> None:
        values = {severity.value for severity in RiskSeverity}

        self.assertEqual(values, {"P0_BLOCKER", "P1_HIGH", "P2_MEDIUM", "P3_LOW", "INFO"})


class StateMachineTransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.machine = StateMachine()

    def test_created_to_pm_processing_is_legal(self) -> None:
        result = self.machine.transition(make_state(TaskStatus.CREATED), TaskStatus.PM_PROCESSING)

        self.assertEqual(result.state.current_status, TaskStatus.PM_PROCESSING)
        self.assertEqual(result.state.current_agent, Role.PM)

    def test_pm_processing_to_architect_processing_is_illegal(self) -> None:
        with self.assertRaises(StateMachineError):
            self.machine.transition(
                make_state(TaskStatus.PM_PROCESSING),
                TaskStatus.ARCHITECT_PROCESSING,
            )

    def test_architect_completed_to_human_review_required_is_legal(self) -> None:
        result = self.machine.transition(
            make_state(TaskStatus.ARCHITECT_COMPLETED),
            TaskStatus.HUMAN_REVIEW_REQUIRED,
        )

        self.assertEqual(result.state.current_status, TaskStatus.HUMAN_REVIEW_REQUIRED)
        self.assertEqual(result.state.human_review_status, ReviewStatus.PENDING)

    def test_human_review_to_developer_requires_approved_status(self) -> None:
        with self.assertRaises(StateMachineError):
            self.machine.transition(
                make_state(
                    TaskStatus.HUMAN_REVIEW_REQUIRED,
                    human_review_status=ReviewStatus.PENDING,
                ),
                TaskStatus.DEVELOPER_PROCESSING,
                review_valid=True,
            )

    def test_human_review_to_developer_with_approved_and_valid_review_is_legal(self) -> None:
        result = self.machine.transition(
            make_state(
                TaskStatus.HUMAN_REVIEW_REQUIRED,
                human_review_status=ReviewStatus.APPROVED,
            ),
            TaskStatus.DEVELOPER_PROCESSING,
            review_valid=True,
        )

        self.assertEqual(result.state.current_status, TaskStatus.DEVELOPER_PROCESSING)
        self.assertEqual(result.state.current_agent, Role.DEVELOPER)

    def test_final_review_to_completed_requires_approved_status(self) -> None:
        with self.assertRaises(StateMachineError):
            self.machine.transition(
                make_state(
                    TaskStatus.FINAL_REVIEW_REQUIRED,
                    final_review_status=ReviewStatus.PENDING,
                ),
                TaskStatus.COMPLETED,
                final_review_valid=True,
            )

    def test_final_review_to_completed_with_approved_and_valid_review_is_legal(self) -> None:
        result = self.machine.transition(
            make_state(
                TaskStatus.FINAL_REVIEW_REQUIRED,
                human_review_status=ReviewStatus.APPROVED,
                final_review_status=ReviewStatus.APPROVED,
            ),
            TaskStatus.COMPLETED,
            final_review_valid=True,
        )

        self.assertEqual(result.state.current_status, TaskStatus.COMPLETED)
        self.assertEqual(result.state.current_agent, Role.CONTROLLER)

    def test_blocked_to_developer_processing_matches_resume_context(self) -> None:
        blocked_context = make_blocked_context()
        result = self.machine.recover_from_blocked(
            make_state(TaskStatus.BLOCKED, blocked_context=blocked_context),
            TaskStatus.DEVELOPER_PROCESSING,
            Role.DEVELOPER,
            missing_artifacts_resolved=True,
        )

        self.assertEqual(result.state.current_status, TaskStatus.DEVELOPER_PROCESSING)
        self.assertEqual(result.state.current_agent, Role.DEVELOPER)
        self.assertIsNone(result.state.active_blocker)
        self.assertIsNone(result.state.blocked_context)
        self.assertEqual(result.state.blockers_history, ["B-T-2026-001-001"])

    def test_blocked_to_qa_processing_is_illegal_when_resume_status_does_not_match(self) -> None:
        blocked_context = make_blocked_context(resume_to_status=TaskStatus.DEVELOPER_PROCESSING)

        with self.assertRaises(StateMachineError):
            self.machine.recover_from_blocked(
                make_state(TaskStatus.BLOCKED, blocked_context=blocked_context),
                TaskStatus.QA_PROCESSING,
                Role.QA,
                missing_artifacts_resolved=True,
            )

    def test_completed_is_terminal(self) -> None:
        with self.assertRaises(StateMachineError):
            self.machine.transition(make_state(TaskStatus.COMPLETED), TaskStatus.PM_PROCESSING)

    def test_cancelled_is_terminal(self) -> None:
        with self.assertRaises(StateMachineError):
            self.machine.transition(make_state(TaskStatus.CANCELLED), TaskStatus.PM_PROCESSING)

    def test_architect_review_middle_state_recovers_to_developer_processing(self) -> None:
        result = self.machine.controller_startup_recovery_check(
            make_state(
                TaskStatus.HUMAN_REVIEW_REQUIRED,
                human_review_status=ReviewStatus.APPROVED,
            ),
            architect_review_valid=True,
        )

        self.assertTrue(result.recovery)
        self.assertEqual(result.state.current_status, TaskStatus.DEVELOPER_PROCESSING)
        self.assertEqual(result.state.current_agent, Role.DEVELOPER)

    def test_final_review_middle_state_recovers_to_completed(self) -> None:
        result = self.machine.controller_startup_recovery_check(
            make_state(
                TaskStatus.FINAL_REVIEW_REQUIRED,
                human_review_status=ReviewStatus.APPROVED,
                final_review_status=ReviewStatus.APPROVED,
            ),
            final_review_valid=True,
        )

        self.assertTrue(result.recovery)
        self.assertEqual(result.state.current_status, TaskStatus.COMPLETED)
        self.assertEqual(result.state.current_agent, Role.CONTROLLER)

    def test_invalid_review_record_prevents_recovery(self) -> None:
        with self.assertRaises(StateMachineError):
            self.machine.controller_startup_recovery_check(
                make_state(
                    TaskStatus.HUMAN_REVIEW_REQUIRED,
                    human_review_status=ReviewStatus.APPROVED,
                ),
                architect_review_valid=False,
            )

    def test_double_step_helpers_do_not_change_current_status_in_step_1(self) -> None:
        result = self.machine.approve_architect_review_step_1(
            make_state(
                TaskStatus.HUMAN_REVIEW_REQUIRED,
                human_review_status=ReviewStatus.PENDING,
            ),
        )

        self.assertEqual(result.state.current_status, TaskStatus.HUMAN_REVIEW_REQUIRED)
        self.assertEqual(result.state.human_review_status, ReviewStatus.APPROVED)


if __name__ == "__main__":
    unittest.main()
