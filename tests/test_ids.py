import unittest

from a2a_runtime.core.errors import SchemaError
from a2a_runtime.core.ids import task_id_from_scoped_id


class ScopedIdTests(unittest.TestCase):
    def test_message_id_extracts_task_id(self) -> None:
        self.assertEqual(task_id_from_scoped_id("M-T-2026-001-008"), "T-2026-001")

    def test_artifact_id_extracts_task_id(self) -> None:
        self.assertEqual(task_id_from_scoped_id("A-T-2026-001-file_change_plan"), "T-2026-001")

    def test_blocker_id_extracts_task_id(self) -> None:
        self.assertEqual(task_id_from_scoped_id("B-T-2026-001-001"), "T-2026-001")

    def test_review_id_extracts_task_id(self) -> None:
        self.assertEqual(task_id_from_scoped_id("R-T-2026-001-architect"), "T-2026-001")
        self.assertEqual(task_id_from_scoped_id("R-T-2026-001-final"), "T-2026-001")

    def test_risk_id_extracts_task_id(self) -> None:
        self.assertEqual(task_id_from_scoped_id("RISK-T-2026-001-001"), "T-2026-001")

    def test_risk_decision_id_extracts_task_id(self) -> None:
        self.assertEqual(task_id_from_scoped_id("RD-T-2026-001-001"), "T-2026-001")

    def test_embedded_task_id_is_rejected(self) -> None:
        with self.assertRaises(SchemaError):
            task_id_from_scoped_id("xxx T-2026-001 yyy")

    def test_bad_prefix_is_rejected(self) -> None:
        with self.assertRaises(SchemaError):
            task_id_from_scoped_id("BAD-M-T-2026-001-001")

    def test_extra_suffix_is_rejected(self) -> None:
        with self.assertRaises(SchemaError):
            task_id_from_scoped_id("M-T-2026-001-001-extra")


if __name__ == "__main__":
    unittest.main()
