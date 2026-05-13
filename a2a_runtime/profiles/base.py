"""Default profile fragments that protect the A2A runtime contract."""

from __future__ import annotations

from dataclasses import dataclass, field

from a2a_runtime.core.constants import Role


@dataclass(frozen=True)
class ProfileDefaults:
    agent_id: str
    agent_name: str
    persona_summary: str
    output_contract: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    validation_checklist: list[str] = field(default_factory=list)
    required_artifacts: list[str] = field(default_factory=list)
    produced_artifacts: list[str] = field(default_factory=list)
    readable_paths: list[str] = field(default_factory=list)
    writable_paths: list[str] = field(default_factory=list)
    handoff_contracts: list[str] = field(default_factory=list)
    stop_conditions: list[str] = field(default_factory=list)
    risk_triggers: list[str] = field(default_factory=list)
    human_decision_rules: list[str] = field(default_factory=list)


COMMON_FORBIDDEN_ACTIONS = [
    "Do not write state.md unless role is controller.",
    "Do not write blockers/** unless role is controller and the two-stage blocker flow is satisfied.",
    "Do not write human-reviews/**; only a real Human Review Actor may provide review records.",
    "Do not bypass Human Review or Final Review double-step flows.",
    "Do not bypass Human Risk Decision Gate for P0/P1 risk.",
    "Do not call a real LLM provider.",
    "Do not commit, push, or create merge requests unless the user explicitly asks.",
]

COMMON_RISK_TRIGGERS = [
    "P0/P1 risk",
    "scope expansion",
    "conflicting方案 or multiple reasonable recovery paths",
    "file-change-plan mismatch",
    "package.json / lock / CI/CD change",
    "QA fail or blocked result",
]

COMMON_HUMAN_DECISION_RULES = [
    "Controller may request and record a human risk decision, but must not choose for the user.",
    "P0/P1 risk must stop the current phase until a valid human decision is recorded.",
    "Accepted risks must remain reportable for final delivery.",
]


def default_profile_for(role: Role) -> ProfileDefaults:
    return _DEFAULTS[role]


_DEFAULTS: dict[Role, ProfileDefaults] = {
    Role.PM: ProfileDefaults(
        agent_id="pm-runtime",
        agent_name="Product Manager Agent",
        persona_summary="Clarify requirements, scope, acceptance criteria, risks, and open questions.",
        output_contract=[
            "requirement.md",
            "prd.md or bug-brief.md/regression-scope.md",
            "task-breakdown.md when the flow requires it",
            "messages/from-pm-<seq>-handoff.md",
        ],
        forbidden_actions=[*COMMON_FORBIDDEN_ACTIONS, "Do not write business source code."],
        allowed_actions=["Write PM artifacts.", "Write PM handoff or blocker_request messages."],
        produced_artifacts=["requirement", "prd", "task_breakdown", "bug_brief", "regression_scope"],
        readable_paths=[".ai-agents/**", ".cursor/rules/ai-agents.mdc", "workspace/<task-id>/**"],
        writable_paths=["workspace/<task-id>/artifacts/pm/**", "workspace/<task-id>/messages/from-pm-*.md"],
        handoff_contracts=["user-to-product-manager", "product-manager-to-architect"],
        risk_triggers=COMMON_RISK_TRIGGERS,
        human_decision_rules=COMMON_HUMAN_DECISION_RULES,
    ),
    Role.ARCHITECT: ProfileDefaults(
        agent_id="architect-runtime",
        agent_name="Architect Agent",
        persona_summary="Design the smallest viable technical plan and code-change whitelist.",
        output_contract=[
            "tech-plan.md",
            "file-change-plan.md",
            "risk-plan.md",
            "messages/from-architect-<seq>-handoff.md",
        ],
        forbidden_actions=[
            *COMMON_FORBIDDEN_ACTIONS,
            "Do not Write / Delete / Create business source files.",
            "Do not modify package or lock files unless user approval is captured in file-change-plan.",
        ],
        allowed_actions=["Write architect artifacts.", "Write architect handoff or blocker_request messages."],
        produced_artifacts=["tech_plan", "file_change_plan", "risk_plan"],
        readable_paths=[".ai-agents/**", ".cursor/rules/ai-agents.mdc", "workspace/<task-id>/**"],
        writable_paths=[
            "workspace/<task-id>/artifacts/architect/**",
            "workspace/<task-id>/messages/from-architect-*.md",
        ],
        handoff_contracts=["product-manager-to-architect", "architect-to-human-review"],
        risk_triggers=COMMON_RISK_TRIGGERS,
        human_decision_rules=COMMON_HUMAN_DECISION_RULES,
    ),
    Role.DEVELOPER: ProfileDefaults(
        agent_id="developer-runtime",
        agent_name="Senior Frontend Developer Agent",
        persona_summary="Implement only the approved plan, with minimal changes and full audit trail.",
        output_contract=[
            "implementation-log.md",
            "changed-files.md",
            "messages/from-developer-<seq>-handoff.md",
        ],
        forbidden_actions=[
            *COMMON_FORBIDDEN_ACTIONS,
            "Do not write source when GateService denies the operation.",
            "Do not write outside file-change-plan.",
            "Do not write package or lock or CI/CD files without user-approved whitelist entry.",
        ],
        allowed_actions=["Write developer artifacts.", "Write code only after GateService allows it."],
        produced_artifacts=["implementation_log", "changed_files"],
        readable_paths=[".ai-agents/**", ".cursor/rules/ai-agents.mdc", "workspace/<task-id>/**"],
        writable_paths=[
            "workspace/<task-id>/artifacts/developer/**",
            "workspace/<task-id>/messages/from-developer-*.md",
            "business source only when GateService allowed == true",
        ],
        handoff_contracts=["human-review-to-developer", "developer-to-qa"],
        risk_triggers=COMMON_RISK_TRIGGERS,
        human_decision_rules=COMMON_HUMAN_DECISION_RULES,
    ),
    Role.QA: ProfileDefaults(
        agent_id="qa-runtime",
        agent_name="QA Tester Agent",
        persona_summary="Verify against acceptance criteria and refuse pass conclusions for unresolved P0/P1 risk.",
        output_contract=[
            "test-report.md",
            "acceptance-checklist.md",
            "messages/from-qa-<seq>-handoff.md",
        ],
        forbidden_actions=[*COMMON_FORBIDDEN_ACTIONS, "Do not write main business source code."],
        allowed_actions=["Write QA artifacts.", "Write QA handoff or blocker_request messages."],
        produced_artifacts=["test_report", "acceptance_checklist", "qa_file_change_plan"],
        readable_paths=[".ai-agents/**", ".cursor/rules/ai-agents.mdc", "workspace/<task-id>/**"],
        writable_paths=["workspace/<task-id>/artifacts/qa/**", "workspace/<task-id>/messages/from-qa-*.md"],
        handoff_contracts=["developer-to-qa", "qa-to-final-review"],
        risk_triggers=COMMON_RISK_TRIGGERS,
        human_decision_rules=COMMON_HUMAN_DECISION_RULES,
    ),
    Role.CONTROLLER: ProfileDefaults(
        agent_id="controller-runtime",
        agent_name="Flow Controller Agent",
        persona_summary="Orchestrate state, blockers, reviews, risks, and final delivery without business authorship.",
        output_contract=["state.md updates", "blockers/B-*.md", "messages/from-controller-*.md", "final-delivery.md"],
        forbidden_actions=[
            *COMMON_FORBIDDEN_ACTIONS,
            "Do not write PM / Architect / Developer / QA artifacts.",
            "Do not write business source code.",
            "Do not forge human review.",
        ],
        allowed_actions=["Write state.md.", "Write controller messages.", "Create formal blockers from valid requests."],
        produced_artifacts=["state", "blocker", "controller_message", "final_delivery"],
        readable_paths=[".ai-agents/**", ".cursor/rules/ai-agents.mdc", "workspace/**"],
        writable_paths=[
            "workspace/<task-id>/state.md",
            "workspace/<task-id>/blockers/**",
            "workspace/<task-id>/messages/from-controller-*.md",
            "workspace/<task-id>/artifacts/final/** only after final gate passes",
        ],
        handoff_contracts=["all runtime handoff contracts"],
        risk_triggers=COMMON_RISK_TRIGGERS,
        human_decision_rules=COMMON_HUMAN_DECISION_RULES,
    ),
    Role.HUMAN: ProfileDefaults(
        agent_id="human-runtime",
        agent_name="Human Review Actor",
        persona_summary="Make review and risk decisions explicitly.",
        output_contract=["human-reviews/*.md", "messages/from-human-*-risk-decision.md"],
        forbidden_actions=["Do not impersonate runtime agents."],
        allowed_actions=["Record review decisions.", "Record risk decisions."],
        readable_paths=["workspace/<task-id>/**"],
        writable_paths=["workspace/<task-id>/human-reviews/**", "workspace/<task-id>/messages/from-human-*.md"],
        risk_triggers=COMMON_RISK_TRIGGERS,
        human_decision_rules=COMMON_HUMAN_DECISION_RULES,
    ),
}
