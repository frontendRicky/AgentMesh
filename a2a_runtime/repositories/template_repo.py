"""Read-only repository for A2A templates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from a2a_runtime.core.paths import A2APaths


@dataclass(frozen=True)
class TemplateRepo:
    paths: A2APaths

    def list_templates(self) -> list[Path]:
        root = self.paths.templates_dir
        if not root.exists():
            return []
        return sorted(path for path in root.glob("*.md") if path.is_file())

    def read_template(self, name: str) -> str | None:
        path = self.paths.templates_dir / name
        if not path.exists() or not path.is_file():
            return None
        return path.read_text(encoding="utf-8")
