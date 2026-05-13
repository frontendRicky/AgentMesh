---
contract_id: HC-human-review-to-developer
from_agent: human-review-actor
to_agent: developer
schema_version: a2a/v1
---

## required_input_artifacts

- artifact_type: tech_plan, status: ready
- artifact_type: file_change_plan, status: ready
- artifact_type: risk_plan, status: ready

## required_output_artifacts

- (无 — Human Review Actor 不产 artifact，只产 review record)

## required_input_messages

- file: messages/from-architect-<seq>-handoff.md
  message_type: handoff
  intent: architect_to_human_review_handoff

## required_output_messages

- (无 — review record 写完后由 Controller 校验并写 from-controller-004-handoff.md 召唤 Dev)

## required_input_review_records

- (无 — 此 contract 的输入是 Architect 的 artifacts；review record 是本 contract 的输出)

## required_output_review_records

- file: human-reviews/architect-review.md
  review_type: architect_review
  reviewer: <用户 handle>
  verdict: approved | rejected | needs_changes
  必含字段（按 review.schema.md）：
    - review_id: R-<task_id>-architect
    - reviewed_artifacts: [tech_plan_id, file_change_plan_id, risk_plan_id]
    - reviewed_at
    - issues（rejected / needs_changes 时必填）
    - followup_required

## acceptance_criteria

- [ ] human-reviews/architect-review.md 存在
- [ ] review record 字段完整（review_id / review_type / reviewed_artifacts / reviewer / reviewed_at / verdict / followup_required / schema_version）
- [ ] verdict ∈ { approved, rejected, needs_changes }
- [ ] verdict == approved 时，所有 reviewed_artifacts 在 file_change_plan / tech_plan 中均可被定位
- [ ] verdict ∈ { rejected, needs_changes } 时，issues 非空且每条 issue 含 severity / description / affected_artifact

## validation_questions

- review record 是不是真人写的（reviewer 不是角色名）？
- verdict == approved 是否基于实际审阅而非象征性同意？
- 如果 verdict == needs_changes，是否给出了足够具体的修改建议？

## allowed_next_actions（verdict == approved，**严格双步**）

- Controller 第一步：state.human_review_status = approved
- Controller 第二步（独立写入）：state.current_status = developer_processing，current_agent = developer，next_agent = qa
- Controller 写 from-controller-004-handoff.md 召唤 Developer
- Developer Agent 启动，按 senior-frontend-developer.agent.md 工作流执行（含 5 条门禁自检）

> **F-08 中间态恢复**：若 Controller 启动时发现 `human_review_status == approved` 但 `current_status` 仍是 `human_review_required`，必须重新校验 review record（仍 verdict=approved）后**自动补做第 2 步**，详 state.schema.md §2.5。

## allowed_next_actions（verdict == rejected 或 needs_changes）

- Controller：state.human_review_status = rejected
- Controller：state.current_status = architect_processing
- Controller 写 from-controller-<seq>-status.md 通知 Architect 按 issues 修订

## forbidden_next_actions

- 把双步审核流转合并成一步（如 state.current_status 直接跳到 developer_processing 而 human_review_status 还是 pending）
- Controller 创建、修改、伪造 architect-review.md
- 在 review record 缺失时翻 human_review_status
- Developer 在 human_review_status != approved 时写源码（**双门禁**违规）
- Developer 误启动时直接发 `message_type: blocker`（应发 `message_type: gate_failure`，避免 Controller 误创建正式 Blocker）

## blocker_conditions

- review record 缺失或字段不完整
- verdict == rejected / needs_changes 但 issues 为空
- reviewer 字段是角色名而非真实用户 handle
- review record 引用了不存在的 artifact_id

## flow_variants

### task_type == bugfix

- 与 feature 流程相同，仍走 Architect Review 与 Final Review
- 不裁审核
- review record 中的 reviewed_artifacts 改为 bug_brief + regression_scope + tech_plan + file_change_plan + risk_plan
