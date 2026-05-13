from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.cli_helpers import make_project, run_cli, write_artifact
from a2a_runtime.core.constants import ArtifactType, Role


class ReportExportTests(unittest.TestCase):
    def test_report_default_does_not_write_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)
            before = self._snapshot(root)

            code, out, _ = run_cli("--project-root", str(root), "report")

            self.assertEqual(code, 0)
            self.assertIn("Generated At:", out)
            self.assertEqual(self._snapshot(root), before)

    def test_report_output_dry_run_does_not_write(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "--json",
                "report",
                "--output",
                "archive/runtime-report.md",
                "--dry-run",
            )

            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["written_files"], [])
            self.assertIn("planned_writes", payload)
            self.assertFalse((root / ".ai-agents/workspace/T-2026-001/archive/runtime-report.md").exists())

    def test_report_output_yes_writes_archive_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "--json",
                "report",
                "--output",
                "archive/runtime-report.md",
                "--yes",
            )

            self.assertEqual(code, 0)
            payload = json.loads(out)
            target = root.resolve() / ".ai-agents/workspace/T-2026-001/archive/runtime-report.md"
            self.assertEqual(payload["written_files"], [str(target)])
            body = target.read_text(encoding="utf-8")
            self.assertIn("Risk Summary", body)
            self.assertIn("Generated At:", body)

    def test_report_output_outside_archive_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "--json",
                "report",
                "--output",
                "../outside.md",
                "--yes",
            )

            self.assertEqual(code, 4)
            payload = json.loads(out)
            self.assertFalse(payload["ok"])
            self.assertFalse((root / "outside.md").exists())

    def test_report_export_does_not_modify_state_or_artifacts(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_artifact(paths, "T-2026-001", ArtifactType.REQUIREMENT, Role.PM, body="# Requirement\n")
            state_path = root / ".ai-agents/workspace/T-2026-001/state.md"
            artifact_path = root / ".ai-agents/workspace/T-2026-001/artifacts/pm/requirement.md"
            before_state = state_path.read_text(encoding="utf-8")
            before_artifact = artifact_path.read_text(encoding="utf-8")

            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "report",
                "--output",
                "archive/runtime-report.md",
                "--yes",
            )

            self.assertEqual(code, 0)
            self.assertEqual(state_path.read_text(encoding="utf-8"), before_state)
            self.assertEqual(artifact_path.read_text(encoding="utf-8"), before_artifact)

    def _snapshot(self, root: Path) -> list[str]:
        return sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


if __name__ == "__main__":
    unittest.main()
