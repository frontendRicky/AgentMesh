from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import ArtifactStatus, ArtifactType, Role, ValidationOutcome
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.artifact import Artifact
from a2a_runtime.repositories.artifact_repo import ArtifactRepo
from a2a_runtime.services.test_report import check_test_report_clean


class TestReportCleanParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.paths = A2APaths(Path(self.tmp.name))
        self.repo = ArtifactRepo(self.paths)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_report(
        self,
        body: str,
        *,
        validation_result: ValidationOutcome = ValidationOutcome.PASS,
        status: ArtifactStatus = ArtifactStatus.READY,
    ) -> None:
        artifact = Artifact(
            artifact_id="A-T-2026-001-test_report",
            task_id="T-2026-001",
            artifact_type=ArtifactType.TEST_REPORT,
            produced_by=Role.QA,
            consumed_by=[Role.CONTROLLER],
            file_path="artifacts/qa/test-report.md",
            version=1,
            status=status,
            summary="test report",
            validation_result=validation_result,
            created_at="2026-05-12T10:00:00+08:00",
        )
        self.repo.write_artifact(artifact, body)

    def assert_blocked(self, body: str, *, validation_result: ValidationOutcome = ValidationOutcome.PASS) -> None:
        self.write_report(body, validation_result=validation_result)
        result = check_test_report_clean(self.repo, "T-2026-001")
        self.assertFalse(result.ok, result.errors)

    def test_status_fail_rejected(self) -> None:
        self.assert_blocked("status: fail\n")

    def test_status_blocked_rejected(self) -> None:
        self.assert_blocked("status: blocked\n")

    def test_validation_result_fail_rejected(self) -> None:
        self.assert_blocked("# Report\n", validation_result=ValidationOutcome.FAIL)

    def test_table_fail_rejected(self) -> None:
        self.assert_blocked("| case | status |\n| login | fail |\n")

    def test_table_blocked_rejected(self) -> None:
        self.assert_blocked("| case | status |\n| login | blocked |\n")

    def test_case_insensitive_rejected(self) -> None:
        self.assert_blocked("| case | status |\n| login | FAIL |\n")

    def test_chinese_failure_words_rejected(self) -> None:
        for word in ["未通过", "阻塞", "失败"]:
            with self.subTest(word=word):
                self.assert_blocked(f"- status: {word}\n")

    def test_failover_is_not_false_positive(self) -> None:
        self.write_report("failover route verified\nstatus: pass\n")

        self.assertTrue(check_test_report_clean(self.repo, "T-2026-001").ok)

    def test_clean_report_passes(self) -> None:
        self.write_report("| case | status |\n| login | pass |\n")

        self.assertTrue(check_test_report_clean(self.repo, "T-2026-001").ok)


if __name__ == "__main__":
    unittest.main()
