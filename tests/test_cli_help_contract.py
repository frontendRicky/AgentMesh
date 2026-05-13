from __future__ import annotations

import unittest

from tests.cli_helpers import run_cli


class CLIHelpContractTests(unittest.TestCase):
    def test_core_command_help_mentions_safety_and_examples(self) -> None:
        commands = [
            ("--help",),
            ("status", "--help"),
            ("validate", "--help"),
            ("task", "--help"),
            ("model", "--help"),
            ("prompt", "--help"),
            ("gate", "--help"),
            ("risk", "--help"),
            ("review", "--help"),
            ("blocker", "--help"),
            ("finalize", "--help"),
            ("report", "--help"),
        ]
        for command in commands:
            with self.subTest(command=command):
                code, out, _ = run_cli(*command)
                self.assertEqual(code, 0)
                self.assertIn("A2A Runtime does not automatically modify business source code", out)
                self.assertIn("A2A Runtime does not call a real LLM", out)
                self.assertIn("GateService", out)
                self.assertIn("Example:", out)
                self.assertIn("Business source writes: never", out)

    def test_help_lists_global_json_and_project_root_flags(self) -> None:
        code, out, _ = run_cli("--help")

        self.assertEqual(code, 0)
        self.assertIn("--project-root", out)
        self.assertIn("--json", out)


if __name__ == "__main__":
    unittest.main()
