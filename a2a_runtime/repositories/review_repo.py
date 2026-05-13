"""Repository for human review records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from a2a_runtime.core import frontmatter
from a2a_runtime.core.constants import ReviewType, ReviewVerdict, parse_enum
from a2a_runtime.core.errors import RepositoryError, ReviewError, SchemaError
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.review import ReviewRecord


@dataclass(frozen=True)
class ReviewRepo:
    paths: A2APaths

    def build_review_path(self, task_id: str, review_type: ReviewType | str) -> Path:
        parsed_type = parse_enum(ReviewType, review_type, "review_type")
        filename = (
            "architect-review.md"
            if parsed_type == ReviewType.ARCHITECT_REVIEW
            else "final-review.md"
        )
        return self.paths.human_reviews_dir(task_id) / filename

    def read_review(self, path: Path) -> ReviewRecord:
        if not path.exists():
            raise RepositoryError(f"review record not found: {path}")
        document = frontmatter.load(path)
        review = ReviewRecord.from_frontmatter(document.data)
        expected = self.build_review_path(review.task_id, review.review_type)
        if path.name != expected.name:
            raise SchemaError("review_type must match review filename")
        return review

    def write_review(
        self,
        review_record: ReviewRecord,
        body: str = "",
        *,
        overwrite: bool = False,
    ) -> Path:
        self.validate_review_record(review_record)
        path = self.build_review_path(review_record.task_id, review_record.review_type)
        if path.exists() and not overwrite:
            raise ReviewError("review record already exists; pass overwrite=True to replace it")
        frontmatter.write(path, review_record.to_frontmatter(), body)
        return path

    def find_architect_review(self, task_id: str) -> ReviewRecord | None:
        return self._find_review(task_id, ReviewType.ARCHITECT_REVIEW)

    def find_final_review(self, task_id: str) -> ReviewRecord | None:
        return self._find_review(task_id, ReviewType.FINAL_REVIEW)

    def validate_review_record(self, review_record: ReviewRecord) -> None:
        ReviewRecord.from_frontmatter(review_record.to_frontmatter())
        expected_suffix = (
            "architect" if review_record.review_type == ReviewType.ARCHITECT_REVIEW else "final"
        )
        if not review_record.review_id.endswith(f"-{expected_suffix}"):
            raise SchemaError("review_id suffix must match review_type")
        if review_record.verdict in {ReviewVerdict.REJECTED, ReviewVerdict.NEEDS_CHANGES}:
            if not review_record.issues:
                raise SchemaError("rejected or needs_changes review must include issues")

    def _find_review(self, task_id: str, review_type: ReviewType) -> ReviewRecord | None:
        path = self.build_review_path(task_id, review_type)
        if not path.exists():
            return None
        return self.read_review(path)
