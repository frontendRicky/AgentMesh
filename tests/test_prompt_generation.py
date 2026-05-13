import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import (
    ArtifactStatus,
    ArtifactType,
    ReviewStatus,
    RiskCategory,
    RiskDecisionAction,
    RiskSeverity,
    RiskStatus,
    Role,
    TaskStatus,
    ValidationOutcome,
)
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.artifact import Artifact
from a2a_runtime.models.risk import RuntimeRiskFinding
from a2a_runtime.models.risk_decision import RiskDecision
from a2a_runtime.models.state import State
from a2a_runtime.repositories.artifact_repo import ArtifactRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.services.prompt_service import PromptService
from a2a_runtime.services.risk_prompt_regeneration_service import RiskPromptRegenerationService


class PromptGenerationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.paths = A2APaths(self.root)
        self.write_profile_fixture()
        self.state_repo = StateRepo(self.paths)
        self.artifact_repo = ArtifactRepo(self.paths)
        self.service = PromptService(
            self.paths,
            state_repo=self.state_repo,
            artifact_repo=self.artifact_repo,
        )
        self.write_state()
        self.write_file_change_plan(
            """
# File Change Plan
- path: src/app.py
  operation: modify
  allowed: true
  reason: planned change
  risk: low
  owner: developer
- path: package.json
  operation: modify
  allowed: true
  reason: dependency change
  risk: high
  owner: developer
""",
        )

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
        cards = {
            "product-manager.card.md": ("pm-001", "Product Manager Agent", "pm"),
            "architect.card.md": ("architect-001", "Architect Agent", "architect"),
            "senior-frontend-developer.card.md": (
                "developer-001",
                "Senior Frontend Developer Agent",
                "developer",
            ),
            "qa-tester.card.md": ("qa-001", "QA Tester Agent", "qa"),
            "flow-controller.card.md": ("controller-001", "Flow Controller Agent", "controller"),
        }
        for filename, (agent_id, name, role) in cards.items():
            self.write_card(filename, agent_id, name, role)
        for filename in [
            "product-manager.agent.md",
            "architect.agent.md",
            "senior-frontend-developer.agent.md",
            "qa-tester.agent.md",
            "flow-controller.agent.md",
        ]:
            (self.root / ".ai-agents/agents" / filename).write_text("# Behavior\n", encoding="utf-8")
        (self.root / ".ai-agents/handoffs/developer-to-qa.md").write_text(
            """---
contract_id: HC-developer-to-qa
from_agent: developer
to_agent: qa
schema_version: a2a/v1
---

## required_output_messages
- handoff
""",
            encoding="utf-8",
        )
        (self.root / ".ai-agents/flows/feature-flow.md").write_text("# Flow\n", encoding="utf-8")
        (self.root / ".ai-agents/rules/a2a-rules.md").write_text("# Rules\n", encoding="utf-8")
        (self.root / ".ai-agents/templates/message-template.md").write_text("# Template\n", encoding="utf-8")
        (self.root / ".cursor/rules/ai-agents.mdc").write_text("# Cursor A2A\n", encoding="utf-8")
        (self.root / "归档/planner.md").write_text("需求摘要。\n", encoding="utf-8")
        (self.root / "归档/architect.md").write_text("readonly\n", encoding="utf-8")
        (self.root / "归档/implementer.md").write_text("不主动 commit / push / 创建 MR。\n", encoding="utf-8")
        (self.root / "归档/verifier.md").write_text("P0/P1 风险不得给“通过”。\n", encoding="utf-8")
        (self.root / "归档/a-to-a-workflow.mdc").write_text("A2A flow。\n", encoding="utf-8")

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

## output_artifacts
- {role}-artifact.md

## writable_paths
- workspace/<task-id>/artifacts/{role_dir}/**

## forbidden_actions
- Do not write state.md
""",
            encoding="utf-8",
        )

    def write_state(
        self,
        *,
        status: TaskStatus = TaskStatus.DEVELOPER_PROCESSING,
        human_review_status: ReviewStatus = ReviewStatus.APPROVED,
    ) -> None:
        state = State(
            task_id="T-2026-001",
            current_status=status,
            previous_status=status,
            current_agent=Role.DEVELOPER,
            next_agent=None,
            allowed_next_statuses=[],
            human_review_status=human_review_status,
            final_review_status=ReviewStatus.NOT_REQUIRED,
            updated_at="2026-05-12T10:00:00+08:00",
        )
        self.state_repo.write("T-2026-001", state, actor=Role.CONTROLLER, body="# State")

    def write_file_change_plan(self, body: str) -> None:
        artifact = Artifact(
            artifact_id="A-T-2026-001-file_change_plan",
            task_id="T-2026-001",
            artifact_type=ArtifactType.FILE_CHANGE_PLAN,
            produced_by=Role.ARCHITECT,
            consumed_by=[Role.DEVELOPER],
            file_path="artifacts/architect/file-change-plan.md",
            version=1,
            status=ArtifactStatus.READY,
            summary="Plan",
            validation_result=ValidationOutcome.PASS,
            created_at="2026-05-12T10:00:00+08:00",
        )
        self.artifact_repo.write_artifact(artifact, body)

    def test_pm_prompt_contains_a2a_header(self) -> None:
        prompt = self.service.generate_pm_prompt("T-2026-001")

        self.assertTrue(prompt.startswith("[A2A]\n- Current Agent: pm"))

    def test_pm_prompt_may_write_code_no(self) -> None:
        prompt = self.service.generate_pm_prompt("T-2026-001")

        self.assertIn("May Write Code: no, PM Agent 不允许写源码", prompt)

    def test_architect_prompt_may_write_code_no_and_readonly(self) -> None:
        prompt = self.service.generate_architect_prompt("T-2026-001")

        self.assertIn("May Write Code: no", prompt)
        self.assertIn("readonly", prompt)
        self.assertIn("file-change-plan 是 Developer 唯一写权限白名单", prompt)

    def test_developer_prompt_without_target_path_may_write_code_no(self) -> None:
        prompt = self.service.generate_developer_prompt("T-2026-001")

        self.assertIn("May Write Code: no, 未指定目标路径与操作，必须先执行 GateService", prompt)

    def test_developer_prompt_gate_allowed_may_write_code_yes(self) -> None:
        prompt = self.service.generate_developer_prompt(
            "T-2026-001",
            target_path="src/app.py",
            operation="modify",
        )

        self.assertIn("May Write Code: yes", prompt)
        self.assertIn("GateService none", prompt)

    def test_developer_prompt_human_review_not_approved_may_write_code_no(self) -> None:
        self.write_state(human_review_status=ReviewStatus.PENDING)

        prompt = self.service.generate_developer_prompt(
            "T-2026-001",
            target_path="src/app.py",
            operation="modify",
        )

        self.assertIn("May Write Code: no", prompt)
        self.assertIn("human_review_status_not_approved", prompt)

    def test_developer_prompt_wrong_status_may_write_code_no(self) -> None:
        self.write_state(status=TaskStatus.ARCHITECT_PROCESSING)

        prompt = self.service.generate_developer_prompt(
            "T-2026-001",
            target_path="src/app.py",
            operation="modify",
        )

        self.assertIn("May Write Code: no", prompt)
        self.assertIn("current_status_not_developer_processing", prompt)

    def test_developer_prompt_package_json_default_no(self) -> None:
        prompt = self.service.generate_developer_prompt(
            "T-2026-001",
            target_path="package.json",
            operation="modify",
        )

        self.assertIn("May Write Code: no", prompt)
        self.assertIn("risk_decision_required", prompt)

    def test_developer_prompt_monorepo_ci_default_no(self) -> None:
        prompt = self.service.generate_developer_prompt(
            "T-2026-001",
            target_path="apps/web/.github/workflows/deploy.yml",
            operation="modify",
        )

        self.assertIn("May Write Code: no", prompt)
        self.assertIn("forbidden ci/cd file", prompt)

    def test_qa_prompt_may_write_code_no_and_status_enum(self) -> None:
        prompt = self.service.generate_qa_prompt("T-2026-001")

        self.assertIn("May Write Code: no", prompt)
        self.assertIn("pass / fail / blocked / not_executed / manual_required", prompt)
        self.assertIn("P0/P1 风险不得给“通过”", prompt)

    def test_controller_prompt_may_write_code_no_and_no_forge_review(self) -> None:
        prompt = self.service.generate_controller_prompt("T-2026-001")

        self.assertIn("May Write Code: no", prompt)
        self.assertIn("不能伪造 human review", prompt)

    def test_all_prompts_include_risk_trigger_and_no_auto_risk_acceptance(self) -> None:
        prompts = [
            self.service.generate_pm_prompt("T-2026-001"),
            self.service.generate_architect_prompt("T-2026-001"),
            self.service.generate_developer_prompt("T-2026-001"),
            self.service.generate_qa_prompt("T-2026-001"),
            self.service.generate_controller_prompt("T-2026-001"),
        ]

        for prompt in prompts:
            self.assertIn("## Risk Trigger", prompt)
            self.assertNotIn("自动接受风险", prompt)

    def test_risk_prompt_and_prompt_service_header_format_match(self) -> None:
        prompt = self.service.generate_pm_prompt("T-2026-001")
        state = self.state_repo.read("T-2026-001")
        risk = RuntimeRiskFinding(
            risk_id="RISK-T-2026-001-001",
            task_id="T-2026-001",
            source_agent=Role.CONTROLLER,
            category=RiskCategory.SCOPE,
            severity=RiskSeverity.P1_HIGH,
            title="Risk",
            description="Risk",
            evidence="Evidence",
            detected_at="2026-05-12T10:00:00+08:00",
            requires_human_decision=True,
            status=RiskStatus.WAITING_HUMAN_DECISION,
            recommended_options=[RiskDecisionAction.SEND_TO_ARCHITECT.value],
        )
        decision = RiskDecision(
            decision_id="RD-T-2026-001-001",
            risk_id=risk.risk_id,
            task_id="T-2026-001",
            decision_by="zhangxia",
            decision_at="2026-05-12T10:00:00+08:00",
            decision=RiskDecisionAction.SEND_TO_ARCHITECT,
            selected_option=RiskDecisionAction.SEND_TO_ARCHITECT.value,
            reason="Human selected architect replan.",
            allowed_next_action=RiskDecisionAction.SEND_TO_ARCHITECT.value,
            requires_regeneration=True,
            target_agent=Role.ARCHITECT,
            target_status=TaskStatus.ARCHITECT_PROCESSING,
        )
        risk_prompt = RiskPromptRegenerationService().generate_prompt_for_decision(
            risk=risk,
            decision=decision,
            state=state,
        )

        prompt_keys = [line.split(":", 1)[0] for line in prompt.splitlines()[:9]]
        risk_prompt_keys = [line.split(":", 1)[0] for line in risk_prompt.splitlines()[:9]]
        self.assertEqual(prompt_keys, risk_prompt_keys)


if __name__ == "__main__":
    unittest.main()
