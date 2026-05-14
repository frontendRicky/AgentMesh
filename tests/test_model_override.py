"""Tests for the per-agent model override feature."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from a2a_runtime.core.constants import RiskSeverity, Role
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.agent_card import AgentCard, parse_markdown_sections
from a2a_runtime.repositories.agent_card_repo import AgentCardRepo
from a2a_runtime.services.model_selection_service import (
    HIGH_REASONING_MODEL,
    ModelSelectionService,
)
from tests.cli_helpers import make_project, run_cli


class ModelSelectionOverrideTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ModelSelectionService()

    def test_resolve_override_returns_default_when_all_empty(self) -> None:
        model, source = self.service.resolve_override()
        self.assertIsNone(model)
        self.assertEqual(source, "default")

    def test_resolve_override_priority_cli_wins(self) -> None:
        model, source = self.service.resolve_override(
            cli_override="cli-model",
            overrides_file_value="file-model",
            agent_card_value="card-model",
        )
        self.assertEqual(model, "cli-model")
        self.assertEqual(source, "cli")

    def test_resolve_override_priority_file_then_card(self) -> None:
        model, source = self.service.resolve_override(
            overrides_file_value="file-model",
            agent_card_value="card-model",
        )
        self.assertEqual(model, "file-model")
        self.assertEqual(source, "overrides_file")

        model, source = self.service.resolve_override(agent_card_value="card-model")
        self.assertEqual(model, "card-model")
        self.assertEqual(source, "agent_card")

    def test_resolve_override_blank_strings_treated_as_no_override(self) -> None:
        model, source = self.service.resolve_override(
            cli_override="   ",
            overrides_file_value="",
            agent_card_value=None,
        )
        self.assertIsNone(model)
        self.assertEqual(source, "default")

    def test_recommend_for_role_uses_override_for_pm(self) -> None:
        result = self.service.recommend_for_role(
            Role.PM,
            tool_context="cursor",
            cli_override="claude-4.6-sonnet-medium-thinking",
        )
        self.assertEqual(result.selected_model, "claude-4.6-sonnet-medium-thinking")
        self.assertEqual(result.override_source, "cli")
        self.assertIn("Manual override", result.rationale)

    def test_recommend_for_role_card_value_picked_when_no_cli_or_file(self) -> None:
        result = self.service.recommend_for_role(
            Role.ARCHITECT,
            tool_context="cursor",
            agent_card_value="claude-4.6-sonnet-medium-thinking",
        )
        self.assertEqual(result.selected_model, "claude-4.6-sonnet-medium-thinking")
        self.assertEqual(result.override_source, "agent_card")

    def test_high_risk_supersedes_override_and_warns(self) -> None:
        result = self.service.recommend_for_role(
            Role.PM,
            tool_context="cursor",
            risk_level=RiskSeverity.P0_BLOCKER,
            cli_override="claude-4.6-sonnet-medium-thinking",
        )
        self.assertEqual(result.selected_model, HIGH_REASONING_MODEL)
        self.assertEqual(result.override_source, "policy")
        self.assertTrue(any("强制升档" in w for w in result.warnings))

    def test_high_risk_keeps_override_if_already_high_reasoning_model(self) -> None:
        result = self.service.recommend_for_role(
            Role.PM,
            tool_context="cursor",
            risk_level=RiskSeverity.P1_HIGH,
            cli_override=HIGH_REASONING_MODEL,
        )
        self.assertEqual(result.selected_model, HIGH_REASONING_MODEL)

    def test_high_risk_overrides_architect_when_override_is_weaker_model(self) -> None:
        result = self.service.recommend_for_role(
            Role.ARCHITECT,
            tool_context="cursor",
            risk_level=RiskSeverity.P0_BLOCKER,
            cli_override="claude-4.6-sonnet-medium-thinking",
        )
        self.assertEqual(result.selected_model, HIGH_REASONING_MODEL)
        self.assertEqual(result.override_source, "policy")
        self.assertTrue(any("强制升档" in w for w in result.warnings))

    def test_codex_override_warns_when_non_openai_slug(self) -> None:
        result = self.service.recommend_for_role(
            Role.DEVELOPER,
            tool_context="codex",
            cli_override="claude-4.6-sonnet-medium-thinking",
        )
        self.assertEqual(result.selected_model, "claude-4.6-sonnet-medium-thinking")
        self.assertTrue(
            any("Codex" in w and "OpenAI" in w for w in result.warnings),
            f"warnings should flag non-openai codex override; got {result.warnings}",
        )

    def test_default_path_unchanged_for_pm(self) -> None:
        result = self.service.recommend_for_role(Role.PM, tool_context="cursor")
        self.assertEqual(result.selected_model, "claude-4.6-sonnet-medium-thinking")
        self.assertEqual(result.override_source, "default")


class AgentCardModelFieldTests(unittest.TestCase):
    def test_model_field_parsed_from_frontmatter(self) -> None:
        card = AgentCard.from_frontmatter(
            {
                "agent_id": "pm-001",
                "agent_name": "PM",
                "role": "pm",
                "version": "1.0.0",
                "schema_version": "a2a/v1",
                "model": "claude-4.6-sonnet-medium-thinking",
            },
            sections={},
        )
        self.assertEqual(card.model, "claude-4.6-sonnet-medium-thinking")

    def test_missing_model_field_is_none(self) -> None:
        card = AgentCard.from_frontmatter(
            {
                "agent_id": "pm-001",
                "agent_name": "PM",
                "role": "pm",
                "version": "1.0.0",
                "schema_version": "a2a/v1",
            },
            sections={},
        )
        self.assertIsNone(card.model)

    def test_empty_string_model_is_treated_as_none(self) -> None:
        card = AgentCard.from_frontmatter(
            {
                "agent_id": "pm-001",
                "agent_name": "PM",
                "role": "pm",
                "version": "1.0.0",
                "schema_version": "a2a/v1",
                "model": "",
            },
            sections={},
        )
        self.assertIsNone(card.model)


class AgentCardRepoOverridesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".ai-agents/agent-cards").mkdir(parents=True)
        self.paths = A2APaths(self.root)
        self.repo = AgentCardRepo(self.paths)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_overrides(self, body: str) -> None:
        (self.root / ".ai-agents/agent-cards/model-overrides.md").write_text(
            body,
            encoding="utf-8",
        )

    def test_no_file_returns_empty(self) -> None:
        overrides, warnings = self.repo.read_model_overrides()
        self.assertEqual(overrides, {})
        self.assertEqual(warnings, [])

    def test_reads_overrides_mapping(self) -> None:
        self.write_overrides(
            """---
schema_version: a2a/v1
overrides:
  pm: claude-4.6-sonnet-medium-thinking
  architect: claude-4.6-sonnet-medium-thinking
  developer: gpt-5.5
  qa: ""
---

# overrides
""",
        )
        overrides, warnings = self.repo.read_model_overrides()
        self.assertEqual(overrides["pm"], "claude-4.6-sonnet-medium-thinking")
        self.assertEqual(overrides["architect"], "claude-4.6-sonnet-medium-thinking")
        self.assertEqual(overrides["developer"], "gpt-5.5")
        self.assertNotIn("qa", overrides)
        self.assertEqual(warnings, [])

    def test_invalid_role_emits_warning(self) -> None:
        self.write_overrides(
            """---
schema_version: a2a/v1
overrides:
  designer: claude-4.6-sonnet-medium-thinking
---

# overrides
""",
        )
        overrides, warnings = self.repo.read_model_overrides()
        self.assertEqual(overrides, {})
        self.assertTrue(warnings)

    def test_checklist_body_single_selection(self) -> None:
        self.write_overrides(
            """---
schema_version: a2a/v1
---

# Agent Model Selection

## pm

- [ ] gpt-5.5
- [x] claude-4.6-sonnet-medium-thinking  -- 我的常用
- [ ] claude-opus-4-7-thinking-high

## architect

- [x] claude-opus-4-7-thinking-high  -- 默认推荐
- [ ] claude-4.6-sonnet-medium-thinking
""",
        )
        overrides, warnings = self.repo.read_model_overrides()
        self.assertEqual(overrides["pm"], "claude-4.6-sonnet-medium-thinking")
        self.assertEqual(overrides["architect"], "claude-opus-4-7-thinking-high")
        self.assertNotIn("developer", overrides)
        self.assertEqual(warnings, [])

    def test_checklist_no_selection_returns_empty(self) -> None:
        self.write_overrides(
            """---
schema_version: a2a/v1
---

## pm

- [ ] gpt-5.5
- [ ] claude-4.6-sonnet-medium-thinking
""",
        )
        overrides, warnings = self.repo.read_model_overrides()
        self.assertEqual(overrides, {})
        self.assertEqual(warnings, [])

    def test_checklist_multiple_selection_warns_and_picks_first(self) -> None:
        self.write_overrides(
            """---
schema_version: a2a/v1
---

## pm

- [x] claude-4.6-sonnet-medium-thinking
- [x] gpt-5.5
""",
        )
        overrides, warnings = self.repo.read_model_overrides()
        self.assertEqual(overrides["pm"], "claude-4.6-sonnet-medium-thinking")
        self.assertTrue(warnings)
        self.assertTrue(any("multiple models" in w for w in warnings))

    def test_checklist_overrides_take_priority_over_frontmatter(self) -> None:
        self.write_overrides(
            """---
schema_version: a2a/v1
overrides:
  pm: gpt-5.5
  developer: claude-4.6-sonnet-medium-thinking
---

## pm

- [x] claude-opus-4-7-thinking-high
""",
        )
        overrides, warnings = self.repo.read_model_overrides()
        self.assertEqual(overrides["pm"], "claude-opus-4-7-thinking-high")
        self.assertEqual(overrides["developer"], "claude-4.6-sonnet-medium-thinking")

    def test_checklist_supports_uppercase_x_and_inline_hash_comment(self) -> None:
        self.write_overrides(
            """---
schema_version: a2a/v1
---

## pm

- [X] claude-4.6-sonnet-medium-thinking # my pick
""",
        )
        overrides, _ = self.repo.read_model_overrides()
        self.assertEqual(overrides["pm"], "claude-4.6-sonnet-medium-thinking")

    def test_checklist_supports_backtick_wrapped_slug(self) -> None:
        self.write_overrides(
            """---
schema_version: a2a/v1
---

## developer

- [x] `gpt-5.5`
""",
        )
        overrides, _ = self.repo.read_model_overrides()
        self.assertEqual(overrides["developer"], "gpt-5.5")

    def test_checklist_unknown_role_heading_is_skipped(self) -> None:
        self.write_overrides(
            """---
schema_version: a2a/v1
---

## designer

- [x] claude-4.6-sonnet-medium-thinking

## pm

- [x] gpt-5.5
""",
        )
        overrides, warnings = self.repo.read_model_overrides()
        self.assertEqual(overrides, {"pm": "gpt-5.5"})
        self.assertEqual(warnings, [])


class CLIModelOverrideTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        make_project(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write_overrides(self, body: str) -> None:
        (self.root / ".ai-agents/agent-cards/model-overrides.md").write_text(
            body,
            encoding="utf-8",
        )

    def test_model_recommend_with_cli_override(self) -> None:
        code, out, _ = run_cli(
            "--project-root",
            str(self.root),
            "--json",
            "model",
            "recommend",
            "--agent",
            "pm",
            "--model",
            "claude-4.6-sonnet-medium-thinking",
        )
        self.assertEqual(code, 0, out)
        data = json.loads(out)
        self.assertEqual(data["selected_model"], "claude-4.6-sonnet-medium-thinking")
        self.assertEqual(data["override_source"], "cli")

    def test_model_recommend_picks_overrides_file_when_no_cli(self) -> None:
        self.write_overrides(
            """---
schema_version: a2a/v1
overrides:
  pm: claude-4.6-sonnet-medium-thinking
---

# overrides
""",
        )
        code, out, _ = run_cli(
            "--project-root",
            str(self.root),
            "--json",
            "model",
            "recommend",
            "--agent",
            "pm",
        )
        self.assertEqual(code, 0, out)
        data = json.loads(out)
        self.assertEqual(data["selected_model"], "claude-4.6-sonnet-medium-thinking")
        self.assertEqual(data["override_source"], "overrides_file")

    def test_model_recommend_picks_checklist_selection_in_md_body(self) -> None:
        self.write_overrides(
            """---
schema_version: a2a/v1
---

# Agent Model Selection

## pm

- [ ] gpt-5.5
- [x] claude-4.6-sonnet-medium-thinking
- [ ] claude-opus-4-7-thinking-high

## developer

- [ ] gpt-5.5
- [ ] claude-4.6-sonnet-medium-thinking
""",
        )
        code, out, _ = run_cli(
            "--project-root",
            str(self.root),
            "--json",
            "model",
            "recommend",
            "--agent",
            "pm",
        )
        self.assertEqual(code, 0, out)
        data = json.loads(out)
        self.assertEqual(data["selected_model"], "claude-4.6-sonnet-medium-thinking")
        self.assertEqual(data["override_source"], "overrides_file")

        code_dev, out_dev, _ = run_cli(
            "--project-root",
            str(self.root),
            "--json",
            "model",
            "recommend",
            "--agent",
            "developer",
        )
        self.assertEqual(code_dev, 0, out_dev)
        data_dev = json.loads(out_dev)
        self.assertEqual(data_dev["override_source"], "default")
        self.assertEqual(data_dev["selected_model"], "gpt-5.5")

    def test_model_list_marks_overrides(self) -> None:
        self.write_overrides(
            """---
schema_version: a2a/v1
overrides:
  pm: claude-4.6-sonnet-medium-thinking
---

# overrides
""",
        )
        code, out, _ = run_cli("--project-root", str(self.root), "model", "list")
        self.assertEqual(code, 0, out)
        self.assertIn("override: claude-4.6-sonnet-medium-thinking", out)
        self.assertIn("Active Overrides", out)

    def test_prompt_pm_with_cli_override(self) -> None:
        code, out, _ = run_cli(
            "--project-root",
            str(self.root),
            "prompt",
            "pm",
            "--model",
            "claude-4.6-sonnet-medium-thinking",
        )
        self.assertEqual(code, 0, out)
        self.assertIn("Primary Model: claude-4.6-sonnet-medium-thinking", out)
        self.assertIn("Override Source: cli", out)

    def test_prompt_high_risk_overrides_user_override(self) -> None:
        code, out, _ = run_cli(
            "--project-root",
            str(self.root),
            "prompt",
            "pm",
            "--risk",
            "P0_BLOCKER",
            "--model",
            "claude-4.6-sonnet-medium-thinking",
        )
        self.assertEqual(code, 0, out)
        self.assertIn(f"Primary Model: {HIGH_REASONING_MODEL}", out)
        self.assertIn("Override Source: policy", out)
        self.assertIn("强制升档", out)


if __name__ == "__main__":
    unittest.main()
