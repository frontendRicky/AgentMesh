---
contract_id: HC-architect-to-human-review
from_agent: architect
to_agent: human-review-actor
schema_version: a2a/v1
---

## required_input_artifacts

- artifact_type: prd, status: ready（或 bug_brief，bugfix）
- artifact_type: task_breakdown, status: ready（feature 等）

## required_output_artifacts

- artifact_type: tech_plan, status: ready
- artifact_type: file_change_plan, status: ready
- artifact_type: risk_plan, status: ready

## required_input_messages

- file: messages/from-controller-002-handoff.md
  message_type: handoff
  intent: pm_to_architect_handoff_relay
- file: messages/from-pm-<seq>-handoff.md
  intent: pm_to_architect_handoff

## required_output_messages

- file: messages/from-architect-<seq>-handoff.md
  message_type: handoff
  intent: architect_to_human_review_handoff
  to_agent: human-review-actor
  payload 必含:
    - tech_plan_artifact_id
    - file_change_plan_artifact_id
    - risk_plan_artifact_id
    - key_decisions
    - human_review_focus

## required_input_review_records

- (无)

## required_output_review_records

- (无 — review record 由 Human Review Actor 在审核阶段写)

## acceptance_criteria

- [ ] tech-plan 含全部 11 节
- [ ] tech-plan 含"最小可行方案"（非空）
- [ ] tech-plan 回答了 PM handoff 中的 architect_must_answer
- [ ] file-change-plan 每条目含 7 字段（path / operation / allowed / reason / risk / owner / notes）
- [ ] file-change-plan 已列出所有"将要新增"的文件
- [ ] file-change-plan 中默认禁改集（package.json / lock / .github/** / .gitlab-ci.yml / Dockerfile / CI 配置）operation: forbidden（除非用户批准）
- [ ] risk-plan 含至少 1 个风险及其回滚方案
- [ ] handoff message 列出 human_review_focus
- [ ] 所有 artifact status: ready

## validation_questions

- tech-plan 是否做了"最小可行方案"评估，还是过度设计？
- file-change-plan 中的每个文件改动是否都有清晰 reason？
- 是否存在 file-change-plan 之外的隐藏改动需求？
- risk-plan 的回滚方案是否真的可执行？

## allowed_next_actions

- Controller 推进 state.current_status 到 human_review_required
- Controller 设置 state.human_review_status = pending
- Controller 写 from-controller-003-handoff.md 通知用户进入审核
- 等待 Human Review Actor 写入 human-reviews/architect-review.md

## forbidden_next_actions

- 跳过审核直接进入 developer_processing
- Architect 自己写 architect-review.md
- Controller 写 architect-review.md
- 把 architect-review.md 当 artifact 而不是 review record

## blocker_conditions

- 必填 Artifact 缺失或字段不完整
- file-change-plan 缺 7 字段任一
- handoff message 缺 human_review_focus
- 任一 acceptance_criteria 未满足

## flow_variants

### task_type == bugfix

- required_input_artifacts 替换为：bug_brief + regression_scope
- file-change-plan 仍要求 7 字段，但通常只列受影响的少数文件
- acceptance_criteria 增加：
  - [ ] file-change-plan 与 regression-scope 中的回归模块一致
- 其他不变
