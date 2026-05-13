"""Changed files audit report model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from a2a_runtime.core.constants import FileOperation
from a2a_runtime.models._coerce import as_bool, as_enum, as_int, as_str, require


@dataclass(frozen=True)
class ChangedFileEntry:
    path: str
    operation_actual: FileOperation
    lines_changed: int
    in_file_change_plan: bool
    operation_match: bool
    out_of_scope: bool
    is_dependency_file: bool
    remediation: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChangedFileEntry":
        return cls(
            path=as_str(require(data, "path"), "path"),
            operation_actual=as_enum(
                require(data, "operation_actual"),
                FileOperation,
                "operation_actual",
            ),
            lines_changed=as_int(require(data, "lines_changed"), "lines_changed"),
            in_file_change_plan=as_bool(
                require(data, "in_file_change_plan"),
                "in_file_change_plan",
            ),
            operation_match=as_bool(require(data, "operation_match"), "operation_match"),
            out_of_scope=as_bool(require(data, "out_of_scope"), "out_of_scope"),
            is_dependency_file=as_bool(require(data, "is_dependency_file"), "is_dependency_file"),
            remediation=as_str(require(data, "remediation"), "remediation"),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "operation_actual": self.operation_actual.value,
            "lines_changed": self.lines_changed,
            "in_file_change_plan": self.in_file_change_plan,
            "operation_match": self.operation_match,
            "out_of_scope": self.out_of_scope,
            "is_dependency_file": self.is_dependency_file,
            "remediation": self.remediation,
        }


@dataclass(frozen=True)
class ChangedFilesReport:
    entries: list[ChangedFileEntry]
    summary: dict[str, Any] = field(default_factory=dict)

    def has_unapproved_changes(self) -> bool:
        return any(
            entry.out_of_scope or not entry.in_file_change_plan or not entry.operation_match
            for entry in self.entries
        )
