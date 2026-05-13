from __future__ import annotations

import unittest

from a2a_runtime.core.constants import FileOperation, GateFailureType
from a2a_runtime.models.file_change_plan import FileChangePlan, FileChangePlanEntry
from a2a_runtime.services.gate_service import GateService

from tests.test_developer_gate import make_state


class DeveloperGatePathTraversalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = GateService()

    def check(self, path: str):
        return self.service.check_developer_write(
            state=make_state(),
            target_path=path,
            operation="modify",
            file_change_plan=FileChangePlan(
                [
                    FileChangePlanEntry(
                        path=path,
                        operation=FileOperation.MODIFY,
                        allowed=True,
                        reason="planned",
                        risk="high",
                        owner="user-approved",
                    ),
                ],
            ),
        )

    def test_parent_directory_traversal_rejected(self) -> None:
        for path in ["../package.json", "../../../etc/passwd", "src/../package.json"]:
            with self.subTest(path=path):
                result = self.check(path)
                self.assertFalse(result.allowed)
                self.assertEqual(result.failure_type, GateFailureType.RISK_DECISION_REQUIRED)
                self.assertIn("path traversal", result.failed_conditions)

    def test_absolute_paths_rejected(self) -> None:
        for path in ["/etc/hosts", "/tmp/package.json", "C:\\Windows\\system32\\drivers\\etc\\hosts"]:
            with self.subTest(path=path):
                result = self.check(path)
                self.assertFalse(result.allowed)
                self.assertEqual(result.failure_type, GateFailureType.RISK_DECISION_REQUIRED)
                self.assertIn("absolute path", result.failed_conditions)


if __name__ == "__main__":
    unittest.main()
