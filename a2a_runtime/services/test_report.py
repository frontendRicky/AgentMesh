"""Shared QA test-report gate checks."""

from __future__ import annotations

from dataclasses import dataclass
import re

from a2a_runtime.core import frontmatter
from a2a_runtime.core.constants import ArtifactStatus, ArtifactType, ValidationOutcome
from a2a_runtime.models.artifact import Artifact
from a2a_runtime.repositories.artifact_repo import ArtifactRepo


@dataclass(frozen=True)
class TestReportCheck:
    ok: bool
    errors: list[str]
    warnings: list[str]


BLOCKING_QA_STATUSES = {"fail", "failed", "blocked", "失败", "未通过", "阻塞"}
STATUS_FIELD_PATTERN = re.compile(r"^\s*(status|validation_result)\s*:\s*([^\s#|]+)\s*$", re.IGNORECASE)
TOKEN_PATTERN = re.compile(r"(?<![A-Za-z])(fail|failed|blocked)(?![A-Za-z])", re.IGNORECASE)


def check_test_report_clean(artifact_repo: ArtifactRepo, task_id: str) -> TestReportCheck:
    artifact = artifact_repo.find_artifact(task_id, ArtifactType.TEST_REPORT)
    if artifact is None:
        return TestReportCheck(False, ["test-report.md 缺失，请先完成 QA"], [])
    errors = _artifact_errors(artifact)
    body = ""
    data: dict[str, object] = {}
    try:
        path = artifact_repo.paths.task_dir(task_id) / artifact.file_path
        document = frontmatter.load(path)
        data = document.data
        body = document.body
    except Exception as exc:
        errors.append(f"test-report.md invalid or unreadable: {exc}")
    errors.extend(_frontmatter_status_errors(data))
    errors.extend(_body_status_errors(body))
    return TestReportCheck(ok=not errors, errors=errors, warnings=[])


def is_test_report_clean(artifact_repo: ArtifactRepo, artifact: Artifact) -> bool:
    return check_test_report_clean(artifact_repo, artifact.task_id).ok


def _artifact_errors(artifact: Artifact) -> list[str]:
    errors: list[str] = []
    if artifact.status != ArtifactStatus.READY:
        errors.append("test-report.md status must be ready")
    if artifact.validation_result == ValidationOutcome.FAIL:
        errors.append("test-report validation_result is fail")
    return errors


def _frontmatter_status_errors(data: dict[str, object]) -> list[str]:
    errors: list[str] = []
    for key in ["status", "validation_result"]:
        value = str(data.get(key, "")).strip().lower()
        if value in BLOCKING_QA_STATUSES:
            errors.append(f"test-report frontmatter {key} is {value}")
    return errors


def _body_status_errors(body: str) -> list[str]:
    errors: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = STATUS_FIELD_PATTERN.match(line)
        if match and match.group(2).strip().lower() in BLOCKING_QA_STATUSES:
            errors.append(f"test-report body {match.group(1)} is {match.group(2)}")
            continue
        if "|" in line:
            cells = [cell.strip().lower() for cell in line.strip("|").split("|")]
            if any(cell in BLOCKING_QA_STATUSES for cell in cells):
                errors.append("test-report table contains fail or blocked status")
                continue
        lowered = line.lower()
        if TOKEN_PATTERN.search(line):
            errors.append("test-report body contains fail or blocked status")
            continue
        if any(word in lowered for word in {"失败", "未通过", "阻塞"}):
            errors.append("test-report body contains unresolved Chinese fail or blocked status")
    return errors
