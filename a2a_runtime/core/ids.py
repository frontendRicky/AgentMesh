"""Identifier validation helpers."""

from __future__ import annotations

import re

from a2a_runtime.core.constants import (
    ARTIFACT_ID_PATTERN,
    BLOCKER_ID_PATTERN,
    HANDOFF_CONTRACT_ID_PATTERN,
    MESSAGE_ID_PATTERN,
    REVIEW_ID_PATTERN,
    RISK_DECISION_ID_PATTERN,
    RISK_ID_PATTERN,
    TASK_ID_PATTERN,
)
from a2a_runtime.core.errors import SchemaError

TASK_ID_RE = re.compile(TASK_ID_PATTERN)
MESSAGE_ID_RE = re.compile(MESSAGE_ID_PATTERN)
ARTIFACT_ID_RE = re.compile(ARTIFACT_ID_PATTERN)
BLOCKER_ID_RE = re.compile(BLOCKER_ID_PATTERN)
REVIEW_ID_RE = re.compile(REVIEW_ID_PATTERN)
RISK_ID_RE = re.compile(RISK_ID_PATTERN)
RISK_DECISION_ID_RE = re.compile(RISK_DECISION_ID_PATTERN)
HANDOFF_CONTRACT_ID_RE = re.compile(HANDOFF_CONTRACT_ID_PATTERN)


def _validate(pattern: re.Pattern[str], value: str, label: str) -> str:
    if not pattern.fullmatch(value):
        raise SchemaError(f"{label} has invalid format: {value}")
    return value


def is_task_id(value: str) -> bool:
    return bool(TASK_ID_RE.fullmatch(value))


def validate_task_id(value: str) -> str:
    return _validate(TASK_ID_RE, value, "task_id")


def validate_message_id(value: str) -> str:
    return _validate(MESSAGE_ID_RE, value, "message_id")


def validate_artifact_id(value: str) -> str:
    return _validate(ARTIFACT_ID_RE, value, "artifact_id")


def validate_blocker_id(value: str) -> str:
    return _validate(BLOCKER_ID_RE, value, "blocker_id")


def validate_review_id(value: str) -> str:
    return _validate(REVIEW_ID_RE, value, "review_id")


def validate_risk_id(value: str) -> str:
    return _validate(RISK_ID_RE, value, "risk_id")


def validate_risk_decision_id(value: str) -> str:
    return _validate(RISK_DECISION_ID_RE, value, "decision_id")


def validate_handoff_contract_id(value: str) -> str:
    return _validate(HANDOFF_CONTRACT_ID_RE, value, "contract_id")


def task_id_from_scoped_id(value: str) -> str:
    """Extract ``T-YYYY-NNN`` from a known scoped id format."""

    patterns = [
        r"^M-(T-\d{4}-\d{3})-\d{3}$",
        r"^A-(T-\d{4}-\d{3})-[a-z_]+$",
        r"^B-(T-\d{4}-\d{3})-\d{3}$",
        r"^R-(T-\d{4}-\d{3})-(architect|final)$",
        r"^RISK-(T-\d{4}-\d{3})-\d{3}$",
        r"^RD-(T-\d{4}-\d{3})-\d{3}$",
    ]
    for pattern in patterns:
        match = re.fullmatch(pattern, value)
        if match:
            return validate_task_id(match.group(1))
    raise SchemaError(f"cannot extract task_id from scoped id: {value}")
