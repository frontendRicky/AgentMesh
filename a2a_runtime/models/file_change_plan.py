"""File change plan model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from a2a_runtime.core.constants import FileOperation
from a2a_runtime.models._coerce import as_bool, as_enum, as_optional_str, as_str, require


@dataclass(frozen=True)
class FileChangePlanEntry:
    path: str
    operation: FileOperation
    allowed: bool
    reason: str
    risk: str
    owner: str
    notes: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FileChangePlanEntry":
        return cls(
            path=as_str(require(data, "path"), "path"),
            operation=as_enum(require(data, "operation"), FileOperation, "operation"),
            allowed=as_bool(require(data, "allowed"), "allowed"),
            reason=as_str(require(data, "reason"), "reason"),
            risk=as_str(require(data, "risk"), "risk"),
            owner=as_str(require(data, "owner"), "owner"),
            notes=as_optional_str(data.get("notes"), "notes"),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "operation": self.operation.value,
            "allowed": self.allowed,
            "reason": self.reason,
            "risk": self.risk,
            "owner": self.owner,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class FileChangePlan:
    entries: list[FileChangePlanEntry]

    def allowed_entry_for(self, path: str, operation: FileOperation) -> FileChangePlanEntry | None:
        for entry in self.entries:
            if entry.path == path and entry.operation == operation and entry.allowed:
                return entry
        return None
