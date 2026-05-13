from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.clock import A2A_DEFAULT_TZ, FixedClock
from a2a_runtime.core.constants import ReviewStatus, Role, TaskStatus
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.state import State
from a2a_runtime.repositories.state_repo import StateRepo


class StateHistoryArchiveTests(unittest.TestCase):
    def test_write_history_archives_after_threshold(self) -> None:
        with TemporaryDirectory() as tmp:
            paths = A2APaths(Path(tmp))
            repo = StateRepo(
                paths,
                clock=FixedClock(fixed_at=datetime(2026, 5, 12, 10, 30, 0, tzinfo=A2A_DEFAULT_TZ)),
            )
            task_id = "T-2026-001"
            state = State(
                task_id=task_id,
                current_status=TaskStatus.PM_PROCESSING,
                previous_status=TaskStatus.CREATED,
                current_agent=Role.PM,
                next_agent=Role.ARCHITECT,
                allowed_next_statuses=[],
                human_review_status=ReviewStatus.PENDING,
                final_review_status=ReviewStatus.NOT_REQUIRED,
                blockers_history=[f"B-{task_id}-{idx:03d}" for idx in range(1, 61)],
                updated_at="2026-05-12T10:00:00+08:00",
            )
            repo.write(task_id, state, actor=Role.CONTROLLER, body="# State\n")
            for index in range(60):
                state = replace(state, updated_at=f"2026-05-12T10:{index:02d}:00+08:00")
                repo.write_with_history(
                    task_id,
                    state,
                    {
                        "at": state.updated_at,
                        "previous_status": "pm_processing",
                        "current_status": "pm_processing",
                        "actor": "controller",
                        "reason": f"transition {index}",
                    },
                    actor=Role.CONTROLLER,
                )

            _, body = repo.read_with_body(task_id)
            self.assertLessEqual(repo.count_runtime_write_history(body), 20)
            archives = list(paths.archive_dir(task_id).glob("state-history-*.md"))
            self.assertTrue(archives)
            self.assertTrue(any("20260512T103000" in path.name for path in archives))
            blocker_archives = list(paths.archive_dir(task_id).glob("blockers-history-*.md"))
            self.assertTrue(blocker_archives)
            state_after = repo.read(task_id)
            self.assertEqual(len(state_after.blockers_history), 50)
            self.assertTrue(state_after.blockers_history)
            self.assertFalse((Path(tmp) / "src").exists())


if __name__ == "__main__":
    unittest.main()
