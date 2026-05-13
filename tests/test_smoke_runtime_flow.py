from __future__ import annotations

import unittest

from tests.cli_helpers import run_cli
from tests.e2e_helpers import create_minimal_a2a_protocol_tree, create_temp_project_root


class SmokeRuntimeFlowTests(unittest.TestCase):
    def test_minimal_user_path_smoke(self) -> None:
        with create_temp_project_root() as root:
            create_minimal_a2a_protocol_tree(root)

            commands = [
                (
                    "task",
                    "create",
                    "--type",
                    "feature",
                    "--title",
                    "Smoke task",
                    "--priority",
                    "P1",
                    "--owner",
                    "zhangxia",
                    "--yes",
                ),
                ("status",),
                ("prompt", "pm"),
                ("prompt", "architect"),
                ("validate", "identity"),
                ("report",),
                ("gate", "developer", "--path", "src/pages/settings/index.tsx", "--operation", "modify"),
            ]
            for command in commands:
                with self.subTest(command=command):
                    code, out, _ = run_cli("--project-root", str(root), *command)
                    expected = 1 if command[0] == "gate" else 0
                    self.assertEqual(code, expected, out)

            self.assertFalse((root / "src").exists())
            self.assertFalse((root / "app").exists())
            self.assertFalse((root / "package.json").exists())


if __name__ == "__main__":
    unittest.main()
