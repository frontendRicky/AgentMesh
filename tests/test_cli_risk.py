import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import RiskSeverity
from tests.cli_helpers import make_project, run_cli, write_risk


class CLIRiskTests(unittest.TestCase):
    def test_risk_list_reads_review_request(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_risk(paths, "T-2026-001")

            code, out, _ = run_cli("--project-root", str(root), "risk", "list")

            self.assertEqual(code, 0)
            self.assertIn("RISK-T-2026-001-001", out)

    def test_risk_show_displays_risk_id(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")

            code, out, _ = run_cli("--project-root", str(root), "risk", "show", risk_id)

            self.assertEqual(code, 0)
            self.assertIn(risk_id, out)

    def test_risk_review_displays_options(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")

            code, out, _ = run_cli("--project-root", str(root), "risk", "review", risk_id)

            self.assertEqual(code, 0)
            self.assertIn("send_to_architect", out)
            self.assertIn("read-only", out)

    def test_risk_prompt_outputs_risk_decision_header(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001")

            code, out, _ = run_cli("--project-root", str(root), "risk", "prompt", risk_id)

            self.assertEqual(code, 0)
            self.assertTrue(out.startswith("[A2A Risk Decision Required]"))

    def test_validate_risk_unresolved_p1_exit_code_2(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            risk_id = write_risk(paths, "T-2026-001", severity=RiskSeverity.P1_HIGH)

            code, out, _ = run_cli("--project-root", str(root), "validate", "risk")

            self.assertEqual(code, 2)
            self.assertIn(risk_id, out)

    def test_validate_risk_no_unresolved_p0_p1_exit_code_0(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = make_project(root)
            write_risk(paths, "T-2026-001", severity=RiskSeverity.P3_LOW)

            code, out, _ = run_cli("--project-root", str(root), "validate", "risk")

            self.assertEqual(code, 0)
            self.assertIn("OK: true", out)


if __name__ == "__main__":
    unittest.main()
