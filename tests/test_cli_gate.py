import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from dataclasses import replace

from a2a_runtime.core.constants import ReviewStatus, Role
from a2a_runtime.repositories.state_repo import StateRepo
from tests.cli_helpers import make_project, run_cli, write_state


class CLIGateTests(unittest.TestCase):
    def test_gate_developer_allowed_true(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "gate",
                "developer",
                "--path",
                "src/app.py",
                "--operation",
                "modify",
            )

            self.assertEqual(code, 0)
            self.assertIn("Allowed: true", out)

    def test_gate_developer_unapproved_returns_gate_failure(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_state(paths, "T-2026-001", human_review_status=ReviewStatus.PENDING)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "gate",
                "developer",
                "--path",
                "src/app.py",
                "--operation",
                "modify",
            )

            self.assertEqual(code, 1)
            self.assertIn("Failure Type: gate_failure", out)

    def test_gate_uses_state_current_agent_not_cli_command_name(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            state_repo = StateRepo(paths)
            state = state_repo.read("T-2026-001")
            state_repo.write(
                "T-2026-001",
                replace(state, current_agent=Role.ARCHITECT),
                actor=Role.CONTROLLER,
                body="# State\n",
            )

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "gate",
                "developer",
                "--path",
                "src/app.py",
                "--operation",
                "modify",
            )

            self.assertEqual(code, 1)
            self.assertIn("Failure Type: gate_failure", out)
            self.assertIn("state.current_agent must be developer", out)

    def test_gate_developer_path_missing_returns_blocker_request(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "gate",
                "developer",
                "--path",
                "src/missing.py",
                "--operation",
                "modify",
            )

            self.assertEqual(code, 1)
            self.assertIn("Failure Type: blocker_request", out)

    def test_gate_developer_package_json_returns_risk_decision_required(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "gate",
                "developer",
                "--path",
                "package.json",
                "--operation",
                "modify",
            )

            self.assertEqual(code, 1)
            self.assertIn("Failure Type: risk_decision_required", out)

    def test_gate_developer_monorepo_ci_json_returns_not_allowed(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)

            code, out, _ = run_cli(
                "--project-root",
                str(root),
                "--json",
                "gate",
                "developer",
                "--path",
                "apps/web/.github/workflows/deploy.yml",
                "--operation",
                "modify",
            )

            self.assertEqual(code, 1)
            self.assertIn('"allowed": false', out)
            self.assertIn("forbidden ci/cd file", out)

    def test_gate_command_is_dry_run_and_writes_no_messages_or_blockers_or_source(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)

            code, _, _ = run_cli(
                "--project-root",
                str(root),
                "gate",
                "developer",
                "--path",
                "src/app.py",
                "--operation",
                "modify",
            )

            self.assertEqual(code, 0)
            self.assertFalse((root / "src/app.py").exists())
            self.assertEqual(list(paths.messages_dir("T-2026-001").glob("*.md")), [])
            self.assertFalse(paths.blockers_dir("T-2026-001").exists())


if __name__ == "__main__":
    unittest.main()
