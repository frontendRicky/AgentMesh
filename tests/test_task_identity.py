import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core import frontmatter
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.core.errors import TaskIdentityAmbiguousError, TaskIdentityError
from a2a_runtime.repositories.workspace_repo import WorkspaceRepo
from a2a_runtime.services.task_identity_service import TaskIdentityService
from a2a_runtime.services.validation_service import ValidationService


def write_active_task(root: Path, active_task_id: str | None) -> None:
    frontmatter.write(
        root / ".ai-agents" / "workspace" / "active-task.md",
        {
            "active_task_id": active_task_id,
            "last_switched_at": "2026-05-12T10:00:00+08:00",
            "schema_version": "a2a/v1",
        },
        "# Active Task",
    )


def make_task_dir(root: Path, task_id: str) -> None:
    (root / ".ai-agents" / "workspace" / task_id).mkdir(parents=True, exist_ok=True)


class TaskIdentityTests(unittest.TestCase):
    def service_for(self, root: Path) -> TaskIdentityService:
        return TaskIdentityService(WorkspaceRepo(A2APaths(root)))

    def test_explicit_task_id_has_highest_priority(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_task_dir(root, "T-2026-001")
            make_task_dir(root, "T-2026-002")
            write_active_task(root, "T-2026-002")

            self.assertEqual(self.service_for(root).resolve_task_id("T-2026-001"), "T-2026-001")

    def test_active_task_id_is_used_when_present(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_task_dir(root, "T-2026-001")
            write_active_task(root, "T-2026-001")

            self.assertEqual(self.service_for(root).resolve_task_id(), "T-2026-001")

    def test_single_task_is_used_when_active_is_null(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_task_dir(root, "T-2026-001")
            write_active_task(root, None)

            self.assertEqual(self.service_for(root).resolve_task_id(), "T-2026-001")

    def test_multiple_tasks_with_null_active_are_ambiguous(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_task_dir(root, "T-2026-001")
            make_task_dir(root, "T-2026-002")
            write_active_task(root, None)

            with self.assertRaises(TaskIdentityAmbiguousError):
                self.service_for(root).resolve_task_id()

    def test_invalid_or_missing_explicit_task_is_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_active_task(root, None)

            with self.assertRaises(TaskIdentityError):
                self.service_for(root).resolve_task_id("bad-task")

    def test_workspace_task_directory_must_equal_task_id(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrong_dir = root / ".ai-agents" / "workspace" / "T-2026-999"
            wrong_dir.mkdir(parents=True)

            result = ValidationService().validate_workspace_task_dir("T-2026-001", wrong_dir)

            self.assertFalse(result.ok)
            self.assertIn("workspace task directory name must equal task_id", result.errors)


if __name__ == "__main__":
    unittest.main()
