---
contract_id: HC-developer-to-qa
from_agent: developer
to_agent: qa
schema_version: a2a/v1
---

## required_input_artifacts

- artifact_type: prd, status: ready（或 bug_brief，bugfix）
- artifact_type: tech_plan, status: ready
- artifact_type: file_change_plan, status: ready
- artifact_type: risk_plan, status: ready

## required_output_artifacts

- artifact_type: implementation_log, status: ready
- artifact_type: changed_files, status: ready

## required_input_messages

- file: messages/from-controller-004-handoff.md
  message_type: handoff
  intent: human_review_to_dev_handoff

## required_output_messages

- file: messages/from-developer-<seq>-handoff.md
  message_type: handoff
  intent: developer_to_qa_handoff
  to_agent: qa
  payload 必含:
    - implementation_log_artifact_id
    - changed_files_artifact_id
    - summary_of_changes
    - risks
    - unfinished_items
    - qa_focus

## required_input_review_records

- file: human-reviews/architect-review.md
  review_type: architect_review
  verdict: approved（前置门禁，由 Controller 先校验）

## required_output_review_records

- (无)

## acceptance_criteria

- [ ] state.human_review_status == approved（双门禁前置）
- [ ] state.current_status == developer_processing 时实施
- [ ] implementation-log 每步都记录"改什么 / 为什么 / 风险 / 待办"
- [ ] changed-files 每条目含 8 字段（path / operation_actual / lines_changed / in_file_change_plan / operation_match / out_of_scope / is_dependency_file / remediation）
- [ ] changed-files 末尾汇总：越界文件数 == 0
- [ ] changed-files 中所有改动都命中 file-change-plan 白名单
- [ ] 没有触碰默认禁改集（除非 file-change-plan 显式 allowed: yes 且 owner: user-approved）
- [ ] handoff message 列出 qa_focus 与 unfinished_items
- [ ] 所有 artifact status: ready

## validation_questions

- 每个 Write / StrReplace 操作前都做了 5 条门禁自检吗？
- 所有改动都在 file-change-plan 白名单中吗？
- 是否存在大范围重构无关代码的情况？
- mock 数据是否进入了正式逻辑？
- 是否擅自删了旧逻辑？

## allowed_next_actions

- Controller 推进 state.current_status 到 qa_processing
- Controller 写 from-controller-005-handoff.md 召唤 QA
- QA 启动，按 qa-tester.agent.md 工作流执行

## forbidden_next_actions

- 在 changed-files 越界审计 != 0 的情况下推进 QA
- 跳过 implementation-log 直接交接
- Developer 在 human_review_status != approved 时写源码

## blocker_conditions

- changed-files 越界审计有未授权改动
- 实现严重偏离 tech-plan
- 必填 Artifact 缺失或字段不完整
- 任一 acceptance_criteria 未满足

## flow_variants

### task_type == bugfix

- required_input_artifacts 替换为：bug_brief + regression_scope + tech_plan + file_change_plan + risk_plan
- changed-files 越界审计标准更严：通常 ≤ 5 个文件改动
- 增加 acceptance_criteria：
  - [ ] 改动文件与 regression-scope 中受影响模块一致
- 其他不变
