from __future__ import annotations

import unittest

from a2a_runtime.core import frontmatter
from a2a_runtime.core.constants import Role, TaskStatus
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.state_repo import StateRepo

from tests.cli_helpers import run_cli
from tests.e2e_helpers import (
    create_minimal_a2a_protocol_tree,
    create_task_with_cli,
    create_temp_project_root,
)


class E2ETaskLifecycleTests(unittest.TestCase):
    def test_task_create_status_prompt_pm_task_list_and_report(self) -> None:
        with create_temp_project_root() as root:
            create_minimal_a2a_protocol_tree(root)

            task_id = create_task_with_cli(root, title="新增设置页")
            paths = A2APaths(root)

            self.assertEqual((root / f".ai-agents/workspace/{task_id}").name, task_id)
            task_doc = frontmatter.load(paths.task_md(task_id))
            for dynamic_field in [
                "current_status",
                "previous_status",
                "current_agent",
                "next_agent",
                "blockers",
                "updated_at",
            ]:
                self.assertNotIn(dynamic_field, task_doc.data)

            state = StateRepo(paths).read(task_id)
            self.assertEqual(state.current_status, TaskStatus.PM_PROCESSING)
            self.assertEqual(state.previous_status, TaskStatus.CREATED)
            self.assertEqual(state.current_agent, Role.PM)
            self.assertIn(f"active_task_id: {task_id}", paths.active_task_path.read_text(encoding="utf-8"))
            self.assertTrue(any("user-to-pm-handoff" in path.name for path in MessageRepo(paths).list_messages(task_id)))

            code, out, _ = run_cli("--project-root", str(root), "status")
            self.assertEqual(code, 0)
            self.assertIn("Current Status: pm_processing", out)

            code, out, _ = run_cli("--project-root", str(root), "prompt", "pm")
            self.assertEqual(code, 0)
            self.assertTrue(out.startswith("[A2A]"))

            code, out, _ = run_cli("--project-root", str(root), "task", "list")
            self.assertEqual(code, 0)
            self.assertIn(task_id, out)

            code, out, _ = run_cli("--project-root", str(root), "report")
            self.assertEqual(code, 0)
            self.assertIn("Command: report", out)
            self.assertIn("Title:", out)


if __name__ == "__main__":
    unittest.main()
