from __future__ import annotations

import unittest

from a2a_runtime.core.constants import ReviewStatus, Role, TaskStatus
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.repositories.message_repo import MessageRepo

from tests.cli_helpers import run_cli, write_risk
from tests.e2e_helpers import (
    create_clean_final_review_preconditions,
    create_minimal_a2a_protocol_tree,
    create_ready_architect_artifacts,
    create_task_with_cli,
    create_temp_project_root,
    set_state,
)


BUSINESS_DIRS = ["src", "app", "pages", "components", "services", "utils", "hooks", "types"]


class E2ESafetyBoundaryTests(unittest.TestCase):
    def test_cli_does_not_write_outside_project_root_or_business_dirs(self) -> None:
        with create_temp_project_root() as tmp:
            root = tmp / "project"
            root.mkdir()
            (root / ".ai-agents").mkdir()
            outside = tmp / "outside.txt"
            outside.write_text("unchanged", encoding="utf-8")

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "task",
                "create",
                "--type",
                "feature",
                "--title",
                "Sandbox task",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
                "--yes",
            )

            self.assertEqual(code, 0, out)
            self.assertEqual(outside.read_text(encoding="utf-8"), "unchanged")
            self.assertEqual(sorted(path.name for path in tmp.iterdir()), ["outside.txt", "project"])
            self._assert_no_business_dirs(root)

    def test_gate_developer_is_read_only(self) -> None:
        with create_temp_project_root() as root:
            create_minimal_a2a_protocol_tree(root)
            task_id = create_task_with_cli(root)
            paths = A2APaths(root)
            create_ready_architect_artifacts(paths, task_id)
            set_state(
                paths,
                task_id,
                current_status=TaskStatus.DEVELOPER_PROCESSING,
                previous_status=TaskStatus.HUMAN_REVIEW_REQUIRED,
                current_agent=Role.DEVELOPER,
                human_review_status=ReviewStatus.APPROVED,
            )
            before_messages = sorted(path.name for path in MessageRepo(paths).list_messages(task_id))
            before_blockers = sorted(path.name for path in paths.blockers_dir(task_id).glob("*.md"))

            code, _, _ = run_cli("--project-root", str(root), "gate", "developer", "--path", "src/app.py", "--operation", "modify")

            self.assertEqual(code, 0)
            self.assertEqual(sorted(path.name for path in MessageRepo(paths).list_messages(task_id)), before_messages)
            self.assertEqual(sorted(path.name for path in paths.blockers_dir(task_id).glob("*.md")), before_blockers)
            self._assert_no_business_dirs(root)

    def test_risk_review_prompt_status_validate_report_are_read_only(self) -> None:
        with create_temp_project_root() as root:
            create_minimal_a2a_protocol_tree(root)
            task_id = create_task_with_cli(root)
            paths = A2APaths(root)
            risk_id = write_risk(paths, task_id)
            before = self._snapshot(root)

            for args in [
                ("status",),
                ("validate",),
                ("report",),
                ("risk", "review", risk_id),
                ("risk", "prompt", risk_id),
            ]:
                code, _, _ = run_cli("--project-root", str(root), *args)
                self.assertIn(code, {0, 2})

            self.assertEqual(self._snapshot(root), before)

    def test_mutating_commands_require_yes_and_dry_run_does_not_write(self) -> None:
        with create_temp_project_root() as root:
            (root / ".ai-agents").mkdir()
            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "task",
                "create",
                "--type",
                "feature",
                "--title",
                "No write",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
            )
            self.assertEqual(code, 2)
            self.assertFalse((root / ".ai-agents/workspace").exists())

            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "task",
                "create",
                "--type",
                "feature",
                "--title",
                "Dry run",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
                "--dry-run",
            )
            self.assertEqual(code, 0)
            self.assertFalse((root / ".ai-agents/workspace").exists())

    def test_finalize_does_not_modify_upstream_artifacts(self) -> None:
        with create_temp_project_root() as root:
            create_minimal_a2a_protocol_tree(root)
            task_id = create_task_with_cli(root)
            paths = A2APaths(root)
            create_clean_final_review_preconditions(paths, task_id)
            code, out, _ = run_cli("--project-root", str(root), "review", "approve", "--stage", "final", "--step", "1", "--reviewer", "zhangxia", "--yes")
            self.assertEqual(code, 0, out)
            code, out, _ = run_cli("--project-root", str(root), "review", "approve", "--stage", "final", "--step", "2", "--reviewer", "zhangxia", "--yes")
            self.assertEqual(code, 0, out)
            upstream = root / f".ai-agents/workspace/{task_id}/artifacts/pm/requirement.md"
            before = upstream.read_text(encoding="utf-8")

            code, out, _ = run_cli("--project-root", str(root), "finalize", "--yes")

            self.assertEqual(code, 0, out)
            self.assertEqual(upstream.read_text(encoding="utf-8"), before)

    def test_task_create_does_not_modify_protocol_files_or_create_cursor(self) -> None:
        with create_temp_project_root() as root:
            protocol = root / ".ai-agents/a2a/protocol.md"
            protocol.parent.mkdir(parents=True)
            protocol.write_text("protocol frozen", encoding="utf-8")

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "task",
                "create",
                "--type",
                "feature",
                "--title",
                "Protocol safe",
                "--priority",
                "P1",
                "--owner",
                "zhangxia",
                "--yes",
            )

            self.assertEqual(code, 0, out)
            self.assertEqual(protocol.read_text(encoding="utf-8"), "protocol frozen")
            self.assertFalse((root / ".cursor").exists())

    def _snapshot(self, root) -> list[tuple[str, str]]:
        return sorted(
            (str(path.relative_to(root)), path.read_text(encoding="utf-8"))
            for path in root.rglob("*")
            if path.is_file()
        )

    def _assert_no_business_dirs(self, root) -> None:
        for directory in BUSINESS_DIRS:
            self.assertFalse((root / directory).exists(), directory)


if __name__ == "__main__":
    unittest.main()
