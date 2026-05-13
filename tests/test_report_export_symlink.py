from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from tests.cli_helpers import make_project, run_cli


class ReportExportSymlinkTests(unittest.TestCase):
    def test_archive_directory_symlink_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            task_dir = paths.task_dir("T-2026-001")
            archive = task_dir / "archive"
            outside = root / "outside"
            outside.mkdir()
            if archive.exists():
                archive.rmdir()
            try:
                archive.symlink_to(outside, target_is_directory=True)
            except OSError as exc:  # pragma: no cover - platform permission guard
                self.skipTest(str(exc))

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "report",
                "--output",
                "archive/runtime-report.md",
                "--yes",
            )

            self.assertEqual(code, 4, out)
            self.assertIn("symlink", out)
            self.assertFalse((outside / "runtime-report.md").exists())

    def test_archive_parent_symlink_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            task_dir = paths.task_dir("T-2026-001")
            archive = task_dir / "archive"
            archive.mkdir(exist_ok=True)
            outside = root / "outside"
            outside.mkdir()
            try:
                (archive / "subdir").symlink_to(outside, target_is_directory=True)
            except OSError as exc:  # pragma: no cover - platform permission guard
                self.skipTest(str(exc))

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "report",
                "--output",
                "archive/subdir/runtime-report.md",
                "--dry-run",
            )

            self.assertEqual(code, 4, out)
            self.assertIn("symlink", out)
            self.assertFalse((outside / "runtime-report.md").exists())

    def test_report_output_absolute_path_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "report",
                "--output",
                os.path.join(tmp, "outside.md"),
                "--yes",
            )

            self.assertEqual(code, 4, out)
            self.assertIn("relative", out)


if __name__ == "__main__":
    unittest.main()
