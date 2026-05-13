"""Small coercion helpers shared by dataclass models."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum
from typing import Any, TypeVar

from a2a_runtime.core.constants import SCHEMA_VERSION, Role, normalize_role, parse_enum, role_to_wire
from a2a_runtime.core.errors import SchemaError

EnumT = TypeVar("EnumT", bound=StrEnum)


def require(data: dict[str, Any], key: str) -> Any:
    if key not in data:
        raise SchemaError(f"missing required field: {key}")
    return data[key]


def ensure_schema_version(data: dict[str, Any]) -> str:
    value = require(data, "schema_version")
    if value != SCHEMA_VERSION:
        raise SchemaError(f"schema_version must be {SCHEMA_VERSION}")
    return str(value)


def as_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise SchemaError(f"{field_name} must be a non-empty string")
    return value


def as_optional_str(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    return as_str(value, field_name)


def as_int(value: Any, field_name: str) -> int:
    if not isinstance(value, int):
        raise SchemaError(f"{field_name} must be an int")
    return value


def as_bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"yes", "true"}:
            return True
        if normalized in {"no", "false"}:
            return False
    raise SchemaError(f"{field_name} must be a bool")


def as_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SchemaError(f"{field_name} must be a mapping")
    return value


def as_list(value: Any, field_name: str, *, default: list[Any] | None = None) -> list[Any]:
    if value is None and default is not None:
        return list(default)
    if not isinstance(value, list):
        raise SchemaError(f"{field_name} must be a list")
    return value


def as_str_list(value: Any, field_name: str, *, default: list[str] | None = None) -> list[str]:
    raw = as_list(value, field_name, default=default)
    result: list[str] = []
    for index, item in enumerate(raw):
        result.append(as_str(item, f"{field_name}[{index}]"))
    return result


def as_enum(value: Any, enum_type: type[EnumT], field_name: str) -> EnumT:
    return parse_enum(enum_type, value, field_name)


def as_enum_list(value: Any, enum_type: type[EnumT], field_name: str) -> list[EnumT]:
    return [as_enum(item, enum_type, f"{field_name}[]") for item in as_list(value, field_name)]


def as_role(value: Any, field_name: str, *, allow_none: bool = False) -> Role | None:
    return normalize_role(value, allow_none=allow_none, field_name=field_name)


def as_role_list(value: Any, field_name: str) -> list[Role]:
    roles: list[Role] = []
    for item in as_list(value, field_name):
        role = as_role(item, field_name)
        if role is None:
            raise SchemaError(f"{field_name} cannot contain none")
        roles.append(role)
    return roles


def roles_to_wire(values: Iterable[Role]) -> list[str]:
    return [role_to_wire(value) for value in values]


def enums_to_wire(values: Iterable[StrEnum]) -> list[str]:
    return [value.value for value in values]
