from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

import a2a_runtime


class ReleaseMetadataTests(unittest.TestCase):
    def test_versions_are_synchronized(self) -> None:
        pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

        self.assertEqual(pyproject["project"]["version"], a2a_runtime.__version__)
        self.assertEqual(a2a_runtime.__version__, "0.1.0rc5")

    def test_release_docs_exist(self) -> None:
        for path in [
            Path("CHANGELOG.md"),
            Path("docs/release-checklist.md"),
            Path("docs/manual-acceptance-guide.md"),
            Path("docs/real-project-onboarding.md"),
            Path("docs/release-notes-0.1.0rc5.md"),
            Path("docs/release-candidate-gating.md"),
            Path("docs/project-root-safety.md"),
            Path("docs/file-change-plan-authoring.md"),
            Path("docs/cli-exit-codes.md"),
            Path("docs/real-project-pilot-checklist.md"),
            Path("docs/clean-environment-validation.md"),
            Path("docs/smoke-commands.md"),
            Path("docs/safety-boundaries.md"),
            Path("docs/known-limitations.md"),
            Path("docs/model-policy.md"),
            Path("docs/risk-decide-by-handle.md"),
            Path("docs/symlink-policy.md"),
            Path("docs/test-quality.md"),
            Path("docs/risk-decision-matrix.md"),
            Path("docs/state-history-archive.md"),
            Path("docs/pilot-stage-checklist.md"),
            Path("docs/forbidden-paths.md"),
        ]:
            self.assertTrue(path.exists(), str(path))

    def test_release_docs_contain_required_markers(self) -> None:
        self.assertIn("V1 Release Candidate", Path("README.md").read_text(encoding="utf-8"))
        self.assertIn("0.1.0rc5", Path("CHANGELOG.md").read_text(encoding="utf-8"))
        self.assertIn("Python A2A Runtime V1 Release Checklist", Path("docs/release-checklist.md").read_text(encoding="utf-8"))
        self.assertIn("Manual Acceptance Guide", Path("docs/manual-acceptance-guide.md").read_text(encoding="utf-8"))
        self.assertIn("Real Project Onboarding", Path("docs/real-project-onboarding.md").read_text(encoding="utf-8"))
        self.assertIn("Release Notes: Python A2A Runtime 0.1.0rc5", Path("docs/release-notes-0.1.0rc5.md").read_text(encoding="utf-8"))
        self.assertIn("Real Project Pilot Checklist", Path("docs/real-project-pilot-checklist.md").read_text(encoding="utf-8"))
        self.assertIn("Clean Environment Validation", Path("docs/clean-environment-validation.md").read_text(encoding="utf-8"))
        self.assertIn("Smoke Commands", Path("docs/smoke-commands.md").read_text(encoding="utf-8"))
        self.assertIn("Safety Boundaries", Path("docs/safety-boundaries.md").read_text(encoding="utf-8"))
        self.assertIn("Known Limitations", Path("docs/known-limitations.md").read_text(encoding="utf-8"))
        self.assertIn("Release Candidate Gating", Path("docs/release-candidate-gating.md").read_text(encoding="utf-8"))
        self.assertIn("Project Root Safety", Path("docs/project-root-safety.md").read_text(encoding="utf-8"))
        self.assertIn("File Change Plan Authoring", Path("docs/file-change-plan-authoring.md").read_text(encoding="utf-8"))
        self.assertIn("CLI Exit Codes", Path("docs/cli-exit-codes.md").read_text(encoding="utf-8"))
        self.assertIn("Model Policy", Path("docs/model-policy.md").read_text(encoding="utf-8"))
        self.assertIn("Risk Decide By Handle", Path("docs/risk-decide-by-handle.md").read_text(encoding="utf-8"))
        self.assertIn("Symlink Policy", Path("docs/symlink-policy.md").read_text(encoding="utf-8"))
        self.assertIn("Pilot Stage Checklist", Path("docs/pilot-stage-checklist.md").read_text(encoding="utf-8"))
        self.assertIn("Forbidden Paths", Path("docs/forbidden-paths.md").read_text(encoding="utf-8"))

    def test_changelog_lists_safety_and_test_summary(self) -> None:
        changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")

        self.assertIn("Does not modify business source code", changelog)
        self.assertIn("Does not call real LLM", changelog)
        self.assertIn("Does not accept P0/P1 risk automatically", changelog)
        self.assertIn("244+ tests passing", changelog)
        self.assertIn("251 tests OK", changelog)
        self.assertIn("317 tests OK", changelog)

    def test_safety_boundaries_lists_all_writable_paths(self) -> None:
        safety = Path("docs/safety-boundaries.md").read_text(encoding="utf-8")

        for path in [
            "workspace/<task-id>/task.md",
            "workspace/<task-id>/state.md",
            "workspace/<task-id>/messages/**",
            "workspace/<task-id>/blockers/**",
            "workspace/<task-id>/human-reviews/**",
            "workspace/<task-id>/artifacts/final/**",
            "workspace/<task-id>/archive/**",
            "workspace/active-task.md",
        ]:
            self.assertIn(path, safety)

    def test_release_checklist_lists_required_commands(self) -> None:
        checklist = Path("docs/release-checklist.md").read_text(encoding="utf-8")

        self.assertIn("python3.11 -m compileall a2a_runtime tests", checklist)
        self.assertIn("python3.11 -m unittest discover -s tests", checklist)
        self.assertIn("python3.11 -m a2a_runtime.cli --help", checklist)
        self.assertIn("python3.11 -m a2a_runtime.cli --project-root . --json status", checklist)

    def test_release_notes_contain_required_summary(self) -> None:
        notes = Path("docs/release-notes-0.1.0rc5.md").read_text(encoding="utf-8")

        for text in [
            "0.1.0rc5",
            "Markdown File-based A2A v1.0.0",
            "Stage 0 / Stage 1 / Stage 2",
            "Monorepo CI path bypass",
            ".github",
            ".circleci",
            ".buildkite",
            "No fuzzy",
            "Subprocess CLI regression tests",
            "P2_MEDIUM + requires_human_decision == true + unresolved",
            "No real LLM call",
            "No Codex execution",
            "No git command execution",
            "No automatic business source edits",
        ]:
            self.assertIn(text, notes)


if __name__ == "__main__":
    unittest.main()
