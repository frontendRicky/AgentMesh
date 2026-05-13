from __future__ import annotations

import unittest

from a2a_runtime.core.constants import ReviewType, ReviewVerdict
from a2a_runtime.core.errors import SchemaError
from a2a_runtime.models.review import ReviewRecord


def record(reviewer: str) -> ReviewRecord:
    return ReviewRecord(
        review_id="R-T-2026-001-architect",
        task_id="T-2026-001",
        review_type=ReviewType.ARCHITECT_REVIEW,
        reviewed_artifacts=["tech_plan", "file_change_plan", "risk_plan"],
        reviewer=reviewer,
        reviewed_at="2026-05-12T10:00:00+08:00",
        verdict=ReviewVerdict.APPROVED,
        followup_required=False,
    )


class ReviewRecordValidationSymmetricTests(unittest.TestCase):
    def test_direct_constructor_rejects_role_reviewer(self) -> None:
        for reviewer in ["controller", "pm", "architect", "developer", "dev", "qa", "human", ""]:
            with self.subTest(reviewer=reviewer):
                with self.assertRaises(SchemaError):
                    record(reviewer)

    def test_from_frontmatter_rejects_role_reviewer(self) -> None:
        data = record("zhangxia").to_frontmatter()
        data["reviewer"] = "controller"

        with self.assertRaises(SchemaError):
            ReviewRecord.from_frontmatter(data)

    def test_legal_reviewer_passes(self) -> None:
        self.assertEqual(record("zhangxia").reviewer, "zhangxia")


if __name__ == "__main__":
    unittest.main()
