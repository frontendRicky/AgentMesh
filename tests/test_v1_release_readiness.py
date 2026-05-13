from __future__ import annotations

import tomllib
import unittest
from pathlib import Path
import re

from tests.cli_helpers import run_cli
from tests.e2e_helpers import create_temp_project_root


class V1ReleaseReadinessTests(unittest.TestCase):
    def test_pyproject_entry_point_is_configured(self) -> None:
        data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(data["project"]["scripts"]["a2a-agent"], "a2a_runtime.cli:main")

    def test_readme_contains_release_sections(self) -> None:
        readme = Path("README.md").read_text(encoding="utf-8")
        readme_lower = readme.lower()
        for text in [
            "## Quick Start",
            "## Commands",
            "## What Runtime Does",
            "## What Runtime Does NOT Do",
            "## What V1 Does",
            "## What V1 Does Not Do",
            "## Safety Model",
            "## Real Project Onboarding",
            "## Phase History",
            "## Next Roadmap",
            "## Release Candidate Docs",
            "End-to-End Testing",
            "## Release Checklist",
            "CLI JSON contract pass",
            "V1 Release Candidate",
            "0.1.0rc5",
        ]:
            self.assertIn(text, readme)
        self.assertIn("does not call a real llm", readme_lower)
        self.assertIn("does not modify business source code", readme_lower)

    def test_release_docs_preserve_safety_language(self) -> None:
        docs_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in Path("docs").rglob("*.md")
        )
        docs_lower = docs_text.lower()
        safety = Path("docs/safety-boundaries.md").read_text(encoding="utf-8").lower()

        self.assertIn("does not commit", safety)
        self.assertIn("does not push", safety)
        self.assertIn("does not automatically execute cursor prompt", docs_lower)
        self.assertIn("does not bypass gateservice", docs_lower)
        self.assertIn("does not automatically modify business source code", docs_lower)
        self.assertIn("does not call a real llm", docs_lower)
        self.assertIn("do not execute `git tag`", docs_lower)
        self.assertNotIn("bypass gateservice to", docs_lower)
        self.assertNotIn("automatically execute cursor prompt to", docs_lower)
        self.assertNotIn("runtime directly writes business source", docs_lower)
        self.assertNotIn("runtime will modify business source", docs_lower)
        unsafe_review_commands = re.findall(r"review approve --stage (architect|final)(?![^\n]*--step)", docs_text)
        self.assertEqual(unsafe_review_commands, [])

    def test_runtime_does_not_use_subprocess_git_or_llm_provider(self) -> None:
        runtime_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in Path("a2a_runtime").rglob("*.py")
            if "__pycache__" not in path.parts
        )

        self.assertNotIn("subprocess", runtime_text)
        self.assertNotIn("git ", runtime_text.lower())
        self.assertNotIn("OpenAIProvider", runtime_text)

    def test_cli_does_not_create_forbidden_runtime_paths(self) -> None:
        with create_temp_project_root() as root:
            (root / ".ai-agents").mkdir()
            commands = [
                (
                    "task",
                    "create",
                    "--type",
                    "feature",
                    "--title",
                    "Release safe",
                    "--priority",
                    "P1",
                    "--owner",
                    "zhangxia",
                    "--yes",
                ),
                ("status",),
                ("prompt", "pm"),
                ("report", "--output", "archive/runtime-report.md", "--yes"),
            ]
            for command in commands:
                code, out, _ = run_cli("--project-root", str(root), *command)
                self.assertEqual(code, 0, out)

            for forbidden in [
                ".ai-agents/a2a",
                ".cursor",
                "src",
                "app",
                "pages",
                "components",
                "services",
                "package.json",
                "package-lock.json",
                "pnpm-lock.yaml",
                "yarn.lock",
                ".github",
            ]:
                self.assertFalse((root / forbidden).exists(), forbidden)


if __name__ == "__main__":
    unittest.main()
