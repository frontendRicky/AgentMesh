import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import Role
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.services.agent_profile_service import AgentProfileService


class AgentProfileMergeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.paths = A2APaths(self.root)
        self.write_profile_fixture()
        self.service = AgentProfileService(self.paths)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_profile_fixture(self) -> None:
        for directory in [
            ".ai-agents/agent-cards",
            ".ai-agents/agents",
            ".ai-agents/handoffs",
            ".ai-agents/flows",
            ".ai-agents/rules",
            ".ai-agents/templates",
            ".cursor/rules",
            "归档",
        ]:
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        self.write_card("product-manager.card.md", "pm-001", "Product Manager Agent", "pm")
        self.write_card("architect.card.md", "architect-001", "Architect Agent", "architect")
        self.write_card(
            "senior-frontend-developer.card.md",
            "developer-001",
            "Senior Frontend Developer Agent",
            "developer",
        )
        self.write_card("qa-tester.card.md", "qa-001", "QA Tester Agent", "qa")
        self.write_card("flow-controller.card.md", "controller-001", "Flow Controller Agent", "controller")
        for filename in [
            "product-manager.agent.md",
            "architect.agent.md",
            "senior-frontend-developer.agent.md",
            "qa-tester.agent.md",
            "flow-controller.agent.md",
        ]:
            (self.root / ".ai-agents/agents" / filename).write_text(
                f"# {filename}\n\nBehavior definition.\n",
                encoding="utf-8",
            )
        (self.root / ".ai-agents/handoffs/product-manager-to-architect.md").write_text(
            """---
contract_id: HC-pm-to-architect
from_agent: pm
to_agent: architect
schema_version: a2a/v1
---

## required_output_artifacts
- prd
""",
            encoding="utf-8",
        )
        (self.root / ".ai-agents/flows/feature-flow.md").write_text("# Flow\n", encoding="utf-8")
        (self.root / ".ai-agents/rules/a2a-rules.md").write_text("# Rules\n", encoding="utf-8")
        (self.root / ".ai-agents/templates/message-template.md").write_text("# Template\n", encoding="utf-8")
        (self.root / ".cursor/rules/ai-agents.mdc").write_text("# Cursor A2A\n", encoding="utf-8")
        (self.root / "归档/planner.md").write_text("最多 3 个澄清问题。\n", encoding="utf-8")
        (self.root / "归档/architect.md").write_text("readonly\n最小可行改动。\n", encoding="utf-8")
        (self.root / "归档/implementer.md").write_text(
            "不主动 commit / push / 创建 MR。\n",
            encoding="utf-8",
        )
        (self.root / "归档/verifier.md").write_text(
            "P0/P1 风险不得给“通过”。\n",
            encoding="utf-8",
        )
        (self.root / "归档/a-to-a-workflow.mdc").write_text(
            "planner → architect → implementer → verifier。\n",
            encoding="utf-8",
        )

    def write_card(self, filename: str, agent_id: str, name: str, role: str) -> None:
        role_dir = "developer" if role == "developer" else role
        (self.root / ".ai-agents/agent-cards" / filename).write_text(
            f"""---
agent_id: {agent_id}
agent_name: {name}
role: {role}
version: 1.0.0
schema_version: a2a/v1
---

## description
{name} card.

## output_artifacts
- {role}-artifact.md

## writable_paths
- workspace/<task-id>/artifacts/{role_dir}/**

## forbidden_actions
- Do not write state.md

## validation_checklist
- [ ] ready
""",
            encoding="utf-8",
        )

    def test_can_read_agent_card(self) -> None:
        profile = self.service.build_profile(Role.PM)

        self.assertEqual(profile.agent_id, "pm-001")
        self.assertEqual(profile.agent_name, "Product Manager Agent")

    def test_can_read_agent_behavior_definition(self) -> None:
        profile = self.service.build_profile(Role.PM)

        self.assertTrue(any(path.endswith("product-manager.agent.md") for path in profile.source_files))

    def test_can_read_colleague_persona(self) -> None:
        profile = self.service.build_profile(Role.DEVELOPER)

        self.assertTrue(any(path.endswith("implementer.md") for path in profile.source_files))
        self.assertIn("不主动 commit / push / 创建 MR", profile.persona_summary)

    def test_a2a_hard_rules_beat_persona(self) -> None:
        (self.root / "归档/planner.md").write_text(
            "请写 state.md 并直接修改 blockers/**。\n",
            encoding="utf-8",
        )

        profile = self.service.build_profile(Role.PM)

        self.assertFalse(any("state.md" == path for path in profile.writable_paths))
        self.assertTrue(profile.conflict_matrix)
        self.assertTrue(profile.conflict_matrix[0].needs_human_decision)

    def test_persona_cannot_override_writable_paths(self) -> None:
        (self.root / "归档/planner.md").write_text(
            "writable_paths: src/**\n",
            encoding="utf-8",
        )

        profile = self.service.build_profile(Role.PM)

        self.assertFalse(any(path == "src/**" for path in profile.writable_paths))

    def test_implementer_no_commit_push_is_preserved(self) -> None:
        profile = self.service.build_profile(Role.DEVELOPER)

        text = "\n".join([profile.persona_summary, *profile.forbidden_actions])
        self.assertIn("不主动 commit / push / 创建 MR", text)

    def test_architect_readonly_is_preserved(self) -> None:
        profile = self.service.build_profile(Role.ARCHITECT)

        text = "\n".join([profile.persona_summary, *profile.forbidden_actions])
        self.assertIn("readonly", text)
        self.assertIn("Do not Write / Delete / Create business source files.", text)

    def test_verifier_p0_p1_no_pass_is_preserved(self) -> None:
        profile = self.service.build_profile(Role.QA)

        self.assertIn("P0/P1 风险不得给“通过”", profile.persona_summary)

    def test_dev_alias_normalizes_to_developer(self) -> None:
        profile = self.service.build_profile("dev")

        self.assertEqual(profile.role, Role.DEVELOPER)
        self.assertEqual(profile.to_dict()["role"], "developer")

    def test_missing_colleague_persona_warns_not_fatal(self) -> None:
        (self.root / "归档/planner.md").unlink()

        profile = self.service.build_profile(Role.PM)

        self.assertTrue(any("missing colleague persona" in warning for warning in profile.warnings))
        self.assertEqual(profile.role, Role.PM)


if __name__ == "__main__":
    unittest.main()
