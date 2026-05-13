"""Small Markdown frontmatter parser/dumper implemented with stdlib only."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from a2a_runtime.core.constants import SCHEMA_VERSION
from a2a_runtime.core.errors import FrontmatterError


@dataclass(frozen=True)
class FrontmatterDocument:
    data: dict[str, Any]
    body: str


def loads(markdown: str, *, require_schema_version: bool = True) -> FrontmatterDocument:
    normalized = markdown.replace("\r\n", "\n")
    lines = normalized.split("\n")
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("markdown must start with a frontmatter fence")

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        raise FrontmatterError("frontmatter closing fence not found")

    frontmatter_lines = _clean_lines(lines[1:end_index])
    data, next_index = _parse_block(frontmatter_lines, 0, 0)
    if next_index != len(frontmatter_lines):
        raise FrontmatterError("could not parse complete frontmatter")
    if not isinstance(data, dict):
        raise FrontmatterError("frontmatter root must be a mapping")
    if require_schema_version and data.get("schema_version") != SCHEMA_VERSION:
        raise FrontmatterError(f"schema_version must be {SCHEMA_VERSION}")

    return FrontmatterDocument(data=data, body="\n".join(lines[end_index + 1 :]).lstrip("\n"))


def dumps(
    data: dict[str, Any],
    body: str = "",
    *,
    require_schema_version: bool = True,
) -> str:
    if require_schema_version and data.get("schema_version") != SCHEMA_VERSION:
        raise FrontmatterError(f"schema_version must be {SCHEMA_VERSION}")
    frontmatter = "\n".join(_dump_mapping(data, 0))
    body_text = body.rstrip("\n")
    if body_text:
        return f"---\n{frontmatter}\n---\n\n{body_text}\n"
    return f"---\n{frontmatter}\n---\n"


def load(path: Path, *, require_schema_version: bool = True) -> FrontmatterDocument:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise FrontmatterError(f"frontmatter file is not valid UTF-8: {path}") from exc
    return loads(text, require_schema_version=require_schema_version)


def write(
    path: Path,
    data: dict[str, Any],
    body: str = "",
    *,
    require_schema_version: bool = True,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        dumps(data, body, require_schema_version=require_schema_version),
        encoding="utf-8",
    )


def _clean_lines(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    for line in lines:
        stripped = _strip_inline_comment(line).rstrip()
        if not stripped.strip():
            continue
        cleaned.append(stripped)
    return cleaned


def _strip_inline_comment(line: str) -> str:
    quote: str | None = None
    previous = ""
    for index, char in enumerate(line):
        if char in {"'", '"'} and previous != "\\":
            quote = None if quote == char else char if quote is None else quote
        if char == "#" and quote is None:
            if index == 0 or line[index - 1].isspace():
                return line[:index]
        previous = char
    return line


def _parse_block(lines: list[str], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    if _indent_of(lines[index]) < indent:
        return {}, index

    stripped = lines[index].lstrip()
    if stripped.startswith("- ") or stripped == "-":
        return _parse_list(lines, index, indent)
    return _parse_mapping(lines, index, indent)


def _parse_mapping(lines: list[str], index: int, indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while index < len(lines):
        line = lines[index]
        current_indent = _indent_of(line)
        if current_indent < indent:
            break
        if current_indent > indent:
            break
        stripped = line.strip()
        if stripped.startswith("- ") or stripped == "-":
            break

        key, raw_value = _split_key_value(stripped)
        if raw_value == "":
            next_index = index + 1
            if next_index < len(lines) and _indent_of(lines[next_index]) > current_indent:
                value, index = _parse_block(lines, next_index, _indent_of(lines[next_index]))
            else:
                value = {}
                index = next_index
        else:
            value = _parse_scalar(raw_value)
            index += 1
        if key in result:
            raise FrontmatterError(f"duplicate frontmatter key: {key}")
        result[key] = value
    return result, index


def _parse_list(lines: list[str], index: int, indent: int) -> tuple[list[Any], int]:
    result: list[Any] = []
    while index < len(lines):
        line = lines[index]
        current_indent = _indent_of(line)
        if current_indent < indent:
            break
        if current_indent > indent:
            break
        stripped = line.strip()
        if not (stripped.startswith("- ") or stripped == "-"):
            break

        rest = "" if stripped == "-" else stripped[2:].strip()
        if rest == "":
            next_index = index + 1
            if next_index >= len(lines):
                result.append(None)
                index = next_index
            else:
                value, index = _parse_block(lines, next_index, _indent_of(lines[next_index]))
                result.append(value)
            continue

        if _looks_like_key_value(rest):
            key, raw_value = _split_key_value(rest)
            item: dict[str, Any] = {}
            if raw_value == "":
                next_index = index + 1
                value, index = _parse_block(lines, next_index, _indent_of(lines[next_index]))
            else:
                value = _parse_scalar(raw_value)
                index += 1
            item[key] = value

            while index < len(lines) and _indent_of(lines[index]) > current_indent:
                extra, index = _parse_mapping(lines, index, _indent_of(lines[index]))
                item.update(extra)
            result.append(item)
        else:
            result.append(_parse_scalar(rest))
            index += 1
    return result, index


def _indent_of(line: str) -> int:
    if "\t" in line[: len(line) - len(line.lstrip(" \t"))]:
        raise FrontmatterError("tabs are not supported in frontmatter indentation")
    return len(line) - len(line.lstrip(" "))


def _looks_like_key_value(value: str) -> bool:
    if value.startswith(("'", '"', "[", "{")):
        return False
    return ":" in value


def _split_key_value(line: str) -> tuple[str, str]:
    if ":" not in line:
        raise FrontmatterError(f"expected key: value line, got: {line}")
    key, value = line.split(":", 1)
    key = key.strip()
    if not key:
        raise FrontmatterError(f"empty key in line: {line}")
    return key, value.strip()


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if (value.startswith("[") and not value.endswith("]")) or (
        value.endswith("]") and not value.startswith("[")
    ):
        raise FrontmatterError(f"malformed inline list: {value}")
    if (value.startswith("{") and not value.endswith("}")) or (
        value.endswith("}") and not value.startswith("{")
    ):
        raise FrontmatterError(f"malformed inline mapping: {value}")
    if value.startswith(("'", '"')) or value.endswith(("'", '"')):
        if len(value) < 2 or value[0] != value[-1] or value[0] not in {"'", '"'}:
            raise FrontmatterError(f"malformed quoted scalar: {value}")
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(item) for item in _split_inline_items(inner)]
    if value.startswith("{") and value.endswith("}"):
        inner = value[1:-1].strip()
        if not inner:
            return {}
        result: dict[str, Any] = {}
        for item in _split_inline_items(inner):
            key, raw_value = _split_key_value(item)
            result[key] = _parse_scalar(raw_value)
        return result
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)
    return value


def _split_inline_items(value: str) -> list[str]:
    items: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    previous = ""
    for index, char in enumerate(value):
        if char in {"'", '"'} and previous != "\\":
            quote = None if quote == char else char if quote is None else quote
        elif quote is None and char in "[{":
            depth += 1
        elif quote is None and char in "]}":
            depth -= 1
            if depth < 0:
                raise FrontmatterError(f"malformed inline collection: {value}")
        elif quote is None and depth == 0 and char == ",":
            items.append(value[start:index].strip())
            start = index + 1
        previous = char
    items.append(value[start:].strip())
    if quote is not None or depth != 0:
        raise FrontmatterError(f"malformed inline collection: {value}")
    return [item for item in items if item]


def _dump_mapping(data: dict[str, Any], indent: int) -> list[str]:
    lines: list[str] = []
    prefix = " " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            if value:
                lines.append(f"{prefix}{key}:")
                lines.extend(_dump_mapping(value, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {{}}")
        elif isinstance(value, list):
            if value:
                lines.append(f"{prefix}{key}:")
                lines.extend(_dump_list(value, indent + 2))
            else:
                lines.append(f"{prefix}{key}: []")
        else:
            lines.append(f"{prefix}{key}: {_dump_scalar(value)}")
    return lines


def _dump_list(values: list[Any], indent: int) -> list[str]:
    lines: list[str] = []
    prefix = " " * indent
    for value in values:
        if isinstance(value, dict):
            lines.append(f"{prefix}-")
            lines.extend(_dump_mapping(value, indent + 2))
        elif isinstance(value, list):
            lines.append(f"{prefix}-")
            lines.extend(_dump_list(value, indent + 2))
        else:
            lines.append(f"{prefix}- {_dump_scalar(value)}")
    return lines


def _dump_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    if not text or text.strip() != text or text in {"null", "true", "false"}:
        return repr(text)
    return text
