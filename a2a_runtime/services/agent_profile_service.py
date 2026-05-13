"""Agent profile fusion for runtime prompt generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from a2a_runtime.core.constants import Role, role_to_wire
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.agent_card import AgentCard
from a2a_runtime.models.agent_profile import AgentProfile, ProfileConflict, normalize_profile_role
from a2a_runtime.profiles.a2a_profile import PERSONA_MARKERS as A2A_PERSONA_MARKERS
from a2a_runtime.profiles.architect_profile import PERSONA_MARKERS as ARCHITECT_PERSONA_MARKERS
from a2a_runtime.profiles.base import ProfileDefaults, default_profile_for
from a2a_runtime.profiles.implementer_profile import PERSONA_MARKERS as IMPLEMENTER_PERSONA_MARKERS
from a2a_runtime.profiles.planner_profile import PERSONA_MARKERS as PLANNER_PERSONA_MARKERS
from a2a_runtime.profiles.verifier_profile import PERSONA_MARKERS as VERIFIER_PERSONA_MARKERS
from a2a_runtime.repositories.agent_card_repo import AgentCardRepo
from a2a_runtime.repositories.handoff_repo import HandoffRepo
from a2a_runtime.repositories.reference_repo import ReferenceDocument, ReferenceRepo
from a2a_runtime.repositories.template_repo import TemplateRepo
from a2a_runtime.services.validation_service import ValidationResult


ROLE_PERSONA_MARKERS = {
    Role.PM: PLANNER_PERSONA_MARKERS,
    Role.ARCHITECT: ARCHITECT_PERSONA_MARKERS,
    Role.DEVELOPER: IMPLEMENTER_PERSONA_MARKERS,
    Role.QA: VERIFIER_PERSONA_MARKERS,
    Role.CONTROLLER: A2A_PERSONA_MARKERS,
}

SENSITIVE_CONFLICT_TERMS = (
    "writable_paths",
    "write permission",
    "state.md",
    "blockers",
    "human-reviews",
    "review",
    "risk",
    "final-delivery",
    "package.json",
    "commit",
    "push",
)


@dataclass(frozen=True)
class ProfileSourceBundle:
    role: Role
    defaults: ProfileDefaults
    agent_card: AgentCard | None
    agent_behavior: ReferenceDocument | None
    colleague_persona: ReferenceDocument | None
    cursor_rule: ReferenceDocument | None
    flow_documents: list[ReferenceDocument]
    rule_documents: list[ReferenceDocument]
    handoff_contracts: list[str]
    source_files: list[str]
    warnings: list[str]


class AgentProfileService:
    def __init__(
        self,
        paths: A2APaths,
        *,
        agent_card_repo: AgentCardRepo | None = None,
        handoff_repo: HandoffRepo | None = None,
        template_repo: TemplateRepo | None = None,
        reference_repo: ReferenceRepo | None = None,
    ) -> None:
        self.paths = paths
        self.agent_card_repo = agent_card_repo or AgentCardRepo(paths)
        self.handoff_repo = handoff_repo or HandoffRepo(paths)
        self.template_repo = template_repo or TemplateRepo(paths)
        self.reference_repo = reference_repo or ReferenceRepo(paths)

    def build_profile(self, role: Role | str, task_id: str | None = None) -> AgentProfile:
        parsed = normalize_profile_role(role)
        bundle = self._load_sources(parsed)
        return self.merge_sources(bundle, task_id=task_id)

    def merge_sources(
        self,
        sources: ProfileSourceBundle,
        *,
        task_id: str | None = None,
    ) -> AgentProfile:
        card = sources.agent_card
        defaults = sources.defaults
        source_files = list(sources.source_files)
        warnings = list(sources.warnings)
        conflicts = self.detect_conflicts(sources)

        agent_id = card.agent_id if card else defaults.agent_id
        agent_name = card.agent_name if card else defaults.agent_name
        persona_summary = self._persona_summary(sources.role, sources.colleague_persona)
        output_contract = self._unique(
            [*defaults.output_contract, *(card.output_artifacts if card else [])],
        )
        forbidden_actions = self._unique(
            [*defaults.forbidden_actions, *(card.forbidden_actions if card else [])],
        )
        allowed_actions = self._unique(
            [*defaults.allowed_actions, *(card.allowed_actions if card else [])],
        )
        validation_checklist = self._unique(
            [*defaults.validation_checklist, *(card.validation_checklist if card else [])],
        )
        required_artifacts = self._unique(
            [*defaults.required_artifacts, *(card.input_artifacts if card else [])],
        )
        produced_artifacts = self._unique(
            [*defaults.produced_artifacts, *(card.output_artifacts if card else [])],
        )
        readable_paths = self._unique(
            [*defaults.readable_paths, *(card.readable_paths if card else [])],
        )
        writable_paths = self._unique(
            [*defaults.writable_paths, *(card.writable_paths if card else [])],
        )
        handoff_contracts = self._unique([*defaults.handoff_contracts, *sources.handoff_contracts])
        stop_conditions = self._unique(
            [*defaults.stop_conditions, *(card.stop_conditions if card else [])],
        )
        risk_triggers = self._unique(defaults.risk_triggers)
        human_decision_rules = self._unique(defaults.human_decision_rules)

        profile = AgentProfile(
            role=sources.role,
            agent_id=agent_id,
            agent_name=agent_name,
            system_prompt="",
            persona_summary=persona_summary,
            output_contract=output_contract,
            forbidden_actions=forbidden_actions,
            allowed_actions=allowed_actions,
            validation_checklist=validation_checklist,
            required_artifacts=required_artifacts,
            produced_artifacts=produced_artifacts,
            readable_paths=readable_paths,
            writable_paths=writable_paths,
            handoff_contracts=handoff_contracts,
            stop_conditions=stop_conditions,
            risk_triggers=risk_triggers,
            human_decision_rules=human_decision_rules,
            source_files=source_files,
            conflict_matrix=conflicts,
            warnings=warnings,
        )
        return AgentProfile(
            **{
                **profile.to_dict(),
                "role": profile.role,
                "system_prompt": self.render_system_prompt(profile, task_id=task_id),
                "conflict_matrix": profile.conflict_matrix,
            },
        )

    def detect_conflicts(self, sources: ProfileSourceBundle) -> list[ProfileConflict]:
        conflicts: list[ProfileConflict] = []
        persona = sources.colleague_persona
        if persona is None:
            return conflicts
        text = persona.content.lower()
        for protected in self._protected_writable_targets(sources.role):
            if protected.lower() in text and not self._contains_negative_guard(text, protected.lower()):
                conflicts.append(
                    ProfileConflict(
                        field_name="writable_paths",
                        high_priority_source="A2A hard rules",
                        low_priority_source=str(persona.path),
                        high_priority_value="protected target is not writable by this role",
                        low_priority_value=protected,
                        needs_human_decision=True,
                    ),
                )
        if sources.role == Role.DEVELOPER and (
            "主动提交" in persona.content or "主动 commit" in text or "push" in text and "不主动" not in persona.content
        ):
            conflicts.append(
                ProfileConflict(
                    field_name="forbidden_actions",
                    high_priority_source="A2A hard rules",
                    low_priority_source=str(persona.path),
                    high_priority_value="do not commit or push unless explicitly requested",
                    low_priority_value="persona references commit/push",
                    needs_human_decision=False,
                ),
            )
        return conflicts

    def render_system_prompt(self, profile: AgentProfile, task_id: str | None = None) -> str:
        task_line = f"Task: {task_id}" if task_id else "Task: runtime-selected"
        return "\n".join(
            [
                f"{profile.agent_name} ({role_to_wire(profile.role)})",
                task_line,
                "",
                "Persona Summary:",
                profile.persona_summary,
                "",
                "Output Contract:",
                *[f"- {item}" for item in profile.output_contract],
                "",
                "Forbidden Actions:",
                *[f"- {item}" for item in profile.forbidden_actions],
                "",
                "Risk Triggers:",
                *[f"- {item}" for item in profile.risk_triggers],
            ],
        )

    def get_output_contract(self, role: Role | str) -> list[str]:
        return self.build_profile(role).output_contract

    def get_forbidden_actions(self, role: Role | str) -> list[str]:
        return self.build_profile(role).forbidden_actions

    def get_risk_triggers(self, role: Role | str) -> list[str]:
        return self.build_profile(role).risk_triggers

    def validation_for_profile(self, role: Role | str) -> ValidationResult:
        profile = self.build_profile(role)
        result = ValidationResult()
        for warning in profile.warnings:
            result.add_warning(warning)
        for conflict in profile.conflict_matrix:
            if conflict.needs_human_decision:
                result.add_warning(
                    f"profile conflict needs human decision: {conflict.field_name}",
                )
        return result

    def _load_sources(self, role: Role) -> ProfileSourceBundle:
        warnings: list[str] = []
        source_files: list[str] = []
        defaults = default_profile_for(role)

        card, card_path = self.agent_card_repo.try_read_agent_card(role)
        if card is None:
            warnings.append(f"missing agent card: {card_path}")
        else:
            source_files.append(str(card_path))

        behavior = self.reference_repo.read_agent_behavior(role)
        if behavior is None:
            warnings.append(f"missing agent behavior definition for {role.value}")
        else:
            source_files.append(str(behavior.path))

        persona = self.reference_repo.read_colleague_persona(role)
        if persona is None:
            warnings.append(f"missing colleague persona for {role.value}")
        else:
            source_files.append(str(persona.path))

        cursor_rule = self.reference_repo.read_cursor_ai_agents_rule()
        if cursor_rule is None:
            warnings.append("missing .cursor/rules/ai-agents.mdc")
        else:
            source_files.append(str(cursor_rule.path))

        flow_documents = self.reference_repo.list_flow_documents()
        rule_documents = self.reference_repo.list_rule_documents()
        source_files.extend(str(document.path) for document in flow_documents)
        source_files.extend(str(document.path) for document in rule_documents)
        source_files.extend(str(path) for path in self.template_repo.list_templates())

        handoff_names: list[str] = []
        for contract in self.handoff_repo.list_handoffs(role):
            handoff_names.append(contract.contract_id)
        return ProfileSourceBundle(
            role=role,
            defaults=defaults,
            agent_card=card,
            agent_behavior=behavior,
            colleague_persona=persona,
            cursor_rule=cursor_rule,
            flow_documents=flow_documents,
            rule_documents=rule_documents,
            handoff_contracts=handoff_names,
            source_files=self._unique(source_files),
            warnings=warnings,
        )

    def _persona_summary(self, role: Role, persona: ReferenceDocument | None) -> str:
        markers = ROLE_PERSONA_MARKERS.get(role, [])
        lines = [*markers]
        if persona is not None:
            lines.append(self._compact_excerpt(persona.content))
        return "\n".join(f"- {line}" for line in self._unique(lines))

    def _compact_excerpt(self, text: str, *, limit: int = 600) -> str:
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("---") and not line.strip().startswith("model:")
        ]
        excerpt = " ".join(lines)
        return excerpt[:limit].rstrip()

    def _protected_writable_targets(self, role: Role) -> list[str]:
        common = ["state.md", "blockers", "human-reviews", "artifacts/final"]
        if role != Role.CONTROLLER:
            common.append("final-delivery")
        if role in {Role.PM, Role.ARCHITECT, Role.QA, Role.CONTROLLER}:
            common.extend(["src/", "app/", "components/", "services/", "utils/"])
        if role == Role.CONTROLLER:
            common.extend(["artifacts/pm", "artifacts/architect", "artifacts/developer", "artifacts/qa"])
        return common

    def _contains_negative_guard(self, text: str, protected: str) -> bool:
        index = text.find(protected)
        if index < 0:
            return False
        window = text[max(0, index - 16) : index + len(protected) + 16]
        return any(marker in window for marker in ["禁止", "不得", "不允许", "do not", "must not"])

    def _unique(self, values: Iterable[str | Path]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            item = str(value).strip()
            if not item or item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result
