"""Runtime prompt generation for the five A2A agents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from a2a_runtime.core import frontmatter
from a2a_runtime.core.constants import (
    ArtifactType,
    FileOperation,
    GateFailureType,
    QAStatus,
    Role,
    RiskSeverity,
    normalize_role,
    parse_enum,
)
from a2a_runtime.core.errors import RepositoryError, SchemaError
from a2a_runtime.core.paths import A2APaths
from a2a_runtime.models.agent_profile import AgentProfile
from a2a_runtime.models.file_change_plan import FileChangePlan, FileChangePlanEntry
from a2a_runtime.repositories.agent_card_repo import AgentCardRepo
from a2a_runtime.repositories.artifact_repo import ArtifactRepo
from a2a_runtime.repositories.message_repo import MessageRepo
from a2a_runtime.repositories.risk_repo import RiskRepo
from a2a_runtime.repositories.state_repo import StateRepo
from a2a_runtime.services.agent_profile_service import AgentProfileService
from a2a_runtime.services.gate_service import GateCheckResult, GateService
from a2a_runtime.services.model_selection_service import ModelSelectionService
from a2a_runtime.services.prompt_sections import (
    MayWriteCodeDecision,
    inert_state,
    render_a2a_header,
    render_bullets,
    render_expected_outputs,
    render_forbidden_actions,
    render_risk_triggers,
    render_state_machine_requirements,
)


@dataclass(frozen=True)
class PromptBuildContext:
    profile: AgentProfile
    may_write_code: MayWriteCodeDecision
    reading_artifacts: list[str]
    producing_artifacts: list[str]
    expected_messages: list[str]
    gate_result: GateCheckResult | None = None


class PromptService:
    def __init__(
        self,
        paths: A2APaths,
        *,
        profile_service: AgentProfileService | None = None,
        state_repo: StateRepo | None = None,
        artifact_repo: ArtifactRepo | None = None,
        message_repo: MessageRepo | None = None,
        risk_repo: RiskRepo | None = None,
        gate_service: GateService | None = None,
        model_selection_service: ModelSelectionService | None = None,
        agent_card_repo: AgentCardRepo | None = None,
    ) -> None:
        self.paths = paths
        self.profile_service = profile_service or AgentProfileService(paths)
        self.state_repo = state_repo or StateRepo(paths)
        self.artifact_repo = artifact_repo or ArtifactRepo(paths)
        self.message_repo = message_repo or MessageRepo(paths)
        self.risk_repo = risk_repo or RiskRepo(self.message_repo)
        self.gate_service = gate_service or GateService()
        self.model_selection_service = model_selection_service or ModelSelectionService()
        self.agent_card_repo = agent_card_repo or AgentCardRepo(paths)

    def generate(
        self,
        role: Role | str,
        task_id: str,
        *,
        tool_context: str = "cursor",
        risk_level: RiskSeverity | str | None = None,
        target_path: str | None = None,
        operation: FileOperation | str | None = None,
        model_override: str | None = None,
    ) -> str:
        parsed = normalize_role(role, field_name="role")
        if parsed == Role.PM:
            return self.generate_pm_prompt(
                task_id,
                tool_context=tool_context,
                risk_level=risk_level,
                model_override=model_override,
            )
        if parsed == Role.ARCHITECT:
            return self.generate_architect_prompt(
                task_id,
                tool_context=tool_context,
                risk_level=risk_level,
                model_override=model_override,
            )
        if parsed == Role.DEVELOPER:
            return self.generate_developer_prompt(
                task_id,
                target_path=target_path,
                operation=operation,
                tool_context=tool_context,
                risk_level=risk_level,
                model_override=model_override,
            )
        if parsed == Role.QA:
            return self.generate_qa_prompt(
                task_id,
                tool_context=tool_context,
                risk_level=risk_level,
                model_override=model_override,
            )
        if parsed == Role.CONTROLLER:
            return self.generate_controller_prompt(
                task_id,
                tool_context=tool_context,
                risk_level=risk_level,
                model_override=model_override,
            )
        raise SchemaError("PromptService only generates pm, architect, developer, qa, and controller prompts")

    def generate_pm_prompt(
        self,
        task_id: str,
        *,
        tool_context: str = "cursor",
        risk_level: RiskSeverity | str | None = None,
        model_override: str | None = None,
    ) -> str:
        profile = self.profile_service.build_profile(Role.PM, task_id=task_id)
        context = PromptBuildContext(
            profile=profile,
            may_write_code=MayWriteCodeDecision(False, "PM Agent 不允许写源码"),
            reading_artifacts=["task.md", "state.md", "messages/from-controller-*-handoff.md"],
            producing_artifacts=["requirement.md", "prd.md", "task-breakdown.md"],
            expected_messages=["messages/from-pm-<seq>-handoff.md"],
        )
        return self._render_prompt(
            task_id,
            Role.PM,
            context,
            body_sections=[
                "## PM Output Shape\n- 需求摘要\n- 范围界定\n- 验收标准\n- 风险与边界\n- 待确认项\n- 是否需要人工决策\n- 信息不足时最多 3 个澄清问题；信息足够时写“无需追问”",
            ],
            tool_context=tool_context,
            risk_level=risk_level,
            model_override=model_override,
        )

    def generate_architect_prompt(
        self,
        task_id: str,
        *,
        tool_context: str = "cursor",
        risk_level: RiskSeverity | str | None = None,
        model_override: str | None = None,
    ) -> str:
        profile = self.profile_service.build_profile(Role.ARCHITECT, task_id=task_id)
        context = PromptBuildContext(
            profile=profile,
            may_write_code=MayWriteCodeDecision(False, "Architect Agent readonly; 禁止源码 Write / Delete / Create"),
            reading_artifacts=["requirement.md", "prd.md or bug-brief.md", "task-breakdown.md", "state.md"],
            producing_artifacts=["tech-plan.md", "file-change-plan.md", "risk-plan.md"],
            expected_messages=["messages/from-architect-<seq>-handoff.md"],
        )
        return self._render_prompt(
            task_id,
            Role.ARCHITECT,
            context,
            body_sections=[
                "## Architect Output Shape\n- 推荐方案\n- 备选方案与取舍\n- 影响范围\n- 风险清单\n- 实施建议\n- 需要人工选择的方案点",
                "## Architect Write Boundary\n- May Write Code: no\n- readonly\n- 禁止源码 Write / Delete / Create\n- file-change-plan 是 Developer 唯一写权限白名单\n- 多个风险接近的方案不得自行选择，触发 Human Risk Decision Gate",
            ],
            tool_context=tool_context,
            risk_level=risk_level,
            model_override=model_override,
        )

    def generate_developer_prompt(
        self,
        task_id: str,
        target_path: str | None = None,
        operation: FileOperation | str | None = None,
        tool_context: str = "cursor",
        risk_level: RiskSeverity | str | None = None,
        model_override: str | None = None,
    ) -> str:
        profile = self.profile_service.build_profile(Role.DEVELOPER, task_id=task_id)
        state = self._read_state(task_id)
        gate_result: GateCheckResult | None = None
        if target_path is None or operation is None:
            may_write = MayWriteCodeDecision(
                False,
                "未指定目标路径与操作，必须先执行 GateService",
            )
        else:
            plan = self._load_file_change_plan(task_id)
            gate_result = self.gate_service.check_developer_write(
                state=state,
                target_path=target_path,
                operation=operation,
                file_change_plan=plan,
            )
            may_write = MayWriteCodeDecision(
                gate_result.allowed,
                f"GateService {gate_result.failure_type.value}: {gate_result.reason}",
            )
        context = PromptBuildContext(
            profile=profile,
            may_write_code=may_write,
            reading_artifacts=[
                "tech-plan.md",
                "file-change-plan.md",
                "risk-plan.md",
                "human-reviews/architect-review.md",
                "state.md",
            ],
            producing_artifacts=["implementation-log.md", "changed-files.md"],
            expected_messages=["messages/from-developer-<seq>-handoff.md"],
            gate_result=gate_result,
        )
        gate_lines = [
            "## Developer GateService Self Check",
            f"- target_path: {target_path or 'not specified'}",
            f"- operation: {operation or 'not specified'}",
            f"- allowed: {str(gate_result.allowed).lower() if gate_result else 'false'}",
            f"- failure_type: {gate_result.failure_type.value if gate_result else 'not_evaluated'}",
            f"- failed_conditions: {', '.join(gate_result.failed_conditions) if gate_result else 'target_path_or_operation_missing'}",
            f"- reason: {gate_result.reason if gate_result else may_write.reason}",
            "- 状态或审核门禁失败：写 gate_failure。",
            "- file-change-plan 缺路径或上游 Artifact 缺失：写 blocker_request。",
            "- 范围扩大、依赖/CI 修改、多方案选择：触发 risk_decision_required。",
        ]
        return self._render_prompt(
            task_id,
            Role.DEVELOPER,
            context,
            body_sections=[
                "## Developer Output Shape\n- 实施前确认\n- 实际改动\n- 验证结果\n- 遗留风险\n- GateService 自检结果\n- 是否触发 gate_failure / blocker_request / risk_decision_required",
                "\n".join(gate_lines),
            ],
            tool_context=tool_context,
            risk_level=risk_level,
            model_override=model_override,
        )

    def generate_qa_prompt(
        self,
        task_id: str,
        *,
        tool_context: str = "cursor",
        risk_level: RiskSeverity | str | None = None,
        model_override: str | None = None,
    ) -> str:
        profile = self.profile_service.build_profile(Role.QA, task_id=task_id)
        qa_statuses = " / ".join(status.value for status in QAStatus)
        context = PromptBuildContext(
            profile=profile,
            may_write_code=MayWriteCodeDecision(False, "QA 默认不允许修改主业务代码"),
            reading_artifacts=[
                "prd.md or bug-brief.md",
                "tech-plan.md",
                "implementation-log.md",
                "changed-files.md",
                "human-reviews/architect-review.md",
            ],
            producing_artifacts=["test-report.md", "acceptance-checklist.md"],
            expected_messages=["messages/from-qa-<seq>-handoff.md"],
        )
        return self._render_prompt(
            task_id,
            Role.QA,
            context,
            body_sections=[
                f"## QA Output Shape\n- 验收结论\n- 已通过项\n- 未通过或未验证项\n- 风险提示\n- P0/P1 风险是否阻塞\n- 需要人工确认的风险\n- QA status enum: {qa_statuses}",
                "## QA Risk Rules\n- P0/P1 风险不得给“通过”结论，必须触发 Human Risk Decision Gate。\n- 若 changed-files 包含 Java 文件，建议运行 Java risk scanner。\n- 前端任务默认启用 frontend risk checklist。",
            ],
            tool_context=tool_context,
            risk_level=risk_level,
            model_override=model_override,
        )

    def generate_controller_prompt(
        self,
        task_id: str,
        *,
        tool_context: str = "cursor",
        risk_level: RiskSeverity | str | None = None,
        model_override: str | None = None,
    ) -> str:
        profile = self.profile_service.build_profile(Role.CONTROLLER, task_id=task_id)
        state = self._read_state(task_id)
        open_risks = [risk.risk_id for risk in self.risk_repo.list_open_risks(task_id)]
        context = PromptBuildContext(
            profile=profile,
            may_write_code=MayWriteCodeDecision(False, "Flow Controller 不允许写业务源码"),
            reading_artifacts=["task.md", "state.md", "messages/**", "artifacts/**", "human-reviews/**", "blockers/**"],
            producing_artifacts=["state.md", "messages/from-controller-*.md", "blockers/B-*.md", "final-delivery.md when gate passes"],
            expected_messages=["messages/from-controller-<seq>-*.md"],
        )
        return self._render_prompt(
            task_id,
            Role.CONTROLLER,
            context,
            body_sections=[
                f"## Controller Status\n- current_status: {state.current_status.value}\n- current_agent: {state.current_agent.value if state.current_agent else 'none'}",
                f"## Pending Runtime Items\n- 待处理 RiskFinding: {', '.join(open_risks) if open_risks else 'none'}\n- 待处理 Review: check human-reviews/*.md\n- 待处理 Blocker: check active_blocker and blockers/**\n- 当前可执行动作: validate handoff, recover, transition, request review, request risk decision, finalize only after gate\n- 下一步推荐: choose only legal state-machine action",
                "## Controller Boundaries\n- 不能伪造 human review。\n- 不能替用户做风险决定。\n- 不能写 PM / Architect / Developer / QA artifacts。\n- Final-delivery only after final_review_status == approved and current_status == completed and final gate passes.",
            ],
            tool_context=tool_context,
            risk_level=risk_level,
            model_override=model_override,
        )

    def _resolve_model_override_inputs(self, role: Role) -> tuple[str | None, str | None]:
        """Look up agent-card frontmatter and overrides-file values for role.

        Returns (overrides_file_value, agent_card_value). Either may be None.
        Repository / IO failures are swallowed so a broken file never crashes
        prompt generation; warnings are not propagated here because the
        ModelSelectionService already surfaces override_source / warnings in
        the rendered prompt section.
        """

        overrides_file_value: str | None = None
        agent_card_value: str | None = None
        try:
            overrides, _ = self.agent_card_repo.read_model_overrides()
            overrides_file_value = overrides.get(role.value)
        except RepositoryError:
            overrides_file_value = None
        except SchemaError:
            overrides_file_value = None
        try:
            card, _ = self.agent_card_repo.try_read_agent_card(role)
            if card is not None:
                agent_card_value = card.model
        except (RepositoryError, SchemaError):
            agent_card_value = None
        return overrides_file_value, agent_card_value

    def _render_prompt(
        self,
        task_id: str,
        role: Role,
        context: PromptBuildContext,
        *,
        body_sections: list[str],
        tool_context: str = "cursor",
        risk_level: RiskSeverity | str | None = None,
        model_override: str | None = None,
    ) -> str:
        state = self._read_state(task_id)
        parsed_risk = parse_enum(RiskSeverity, risk_level, "risk_level") if risk_level else None
        overrides_file_value, agent_card_value = self._resolve_model_override_inputs(role)
        model_result = self.model_selection_service.recommend_for_role(
            role,
            tool_context=tool_context,
            risk_level=parsed_risk,
            cli_override=model_override,
            overrides_file_value=overrides_file_value,
            agent_card_value=agent_card_value,
        )
        model_section = self.model_selection_service.render_prompt_section(model_result)
        header = render_a2a_header(
            role=role,
            task_id=task_id,
            state=state,
            reading_artifacts=context.reading_artifacts,
            producing_artifacts=context.producing_artifacts,
            may_write_code=context.may_write_code,
        )
        return f"""{header}

{model_section}

# {context.profile.agent_name} Prompt

## Agent Card Summary
{context.profile.agent_name}: {context.profile.agent_id}

## Persona Summary
{context.profile.persona_summary}

## Required Reads
{render_bullets(context.reading_artifacts)}

## Need Output Artifacts
{render_bullets(context.producing_artifacts)}

## Need Output Messages
{render_bullets(context.expected_messages)}

## Forbidden Actions
{render_forbidden_actions(context.profile.forbidden_actions)}

## Current Handoff Requirements
{render_bullets(context.profile.handoff_contracts)}

## Current State Machine Requirements
{render_state_machine_requirements(role)}

## State Summary
- final_review_status: {state.final_review_status.value}

## Risk Trigger
{render_risk_triggers(context.profile.risk_triggers)}

## Expected Outputs
{render_expected_outputs(context.producing_artifacts, context.expected_messages)}

{chr(10).join(body_sections)}
"""

    def _read_state(self, task_id: str):
        try:
            return self.state_repo.read(task_id)
        except RepositoryError:
            return inert_state(task_id)

    def _load_file_change_plan(self, task_id: str) -> FileChangePlan:
        artifact = self.artifact_repo.find_artifact(task_id, ArtifactType.FILE_CHANGE_PLAN)
        if artifact is None:
            return FileChangePlan([])
        path = self.paths.task_dir(task_id) / artifact.file_path
        try:
            document = frontmatter.load(path)
        except (OSError, RepositoryError, SchemaError):
            return FileChangePlan([])
        raw_entries = document.data.get("entries")
        if isinstance(raw_entries, list):
            entries = []
            for item in raw_entries:
                if isinstance(item, dict):
                    try:
                        entries.append(FileChangePlanEntry.from_dict(item))
                    except SchemaError:
                        continue
            return FileChangePlan(entries)
        return FileChangePlan(self._parse_entries_from_body(document.body))

    def _parse_entries_from_body(self, body: str) -> list[FileChangePlanEntry]:
        entries: list[FileChangePlanEntry] = []
        current: dict[str, object] | None = None
        for raw_line in body.splitlines():
            line = raw_line.strip().strip("|").strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("- path:"):
                if current:
                    self._append_plan_entry(entries, current)
                current = {"path": line.split(":", 1)[1].strip()}
                continue
            if current is not None and ":" in line:
                key, value = line.split(":", 1)
                current[key.strip()] = self._coerce_plan_value(key.strip(), value.strip())
        if current:
            self._append_plan_entry(entries, current)
        return entries

    def _append_plan_entry(self, entries: list[FileChangePlanEntry], data: dict[str, object]) -> None:
        try:
            entries.append(FileChangePlanEntry.from_dict(data))
        except SchemaError:
            return

    def _coerce_plan_value(self, key: str, value: str) -> object:
        if key == "allowed":
            return value.lower() in {"true", "yes", "y", "1"}
        return value
