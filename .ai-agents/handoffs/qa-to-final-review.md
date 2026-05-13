---
contract_id: HC-qa-to-final-review
from_agent: qa
to_agent: human-review-actor
schema_version: a2a/v1
---

## required_input_artifacts

- artifact_type: prd, status: ready（或 bug_brief，bugfix）
- artifact_type: implementation_log, status: ready
- artifact_type: changed_files, status: ready

## required_output_artifacts

- artifact_type: test_report, status: ready
- artifact_type: acceptance_checklist, status: ready
- （可选）artifact_type: qa_file_change_plan, status: ready（仅当需要新增测试文件）

## required_input_messages

- file: messages/from-controller-005-handoff.md
  message_type: handoff
  intent: developer_to_qa_handoff_relay
- file: messages/from-developer-<seq>-handoff.md
  intent: developer_to_qa_handoff

## required_output_messages

- file: messages/from-qa-<seq>-handoff.md
  message_type: handoff
  intent: qa_to_final_review_handoff
  to_agent: human-review-actor
  payload 必含:
    - test_report_artifact_id
    - acceptance_checklist_artifact_id
    - pass_rate（pass 数 / 总数）
    - fail_items
    - final_review_focus

## required_input_review_records

- (无)

## required_output_review_records

- (无 — final-review.md 由 Human Review Actor 在 final_review_required 阶段写)

## acceptance_criteria

- [ ] test-report 7 维测试每维都有用例（即使"无适用"也明示）
- [ ] 每条用例 status 字段非空且为 5 枚举之一（pass / fail / blocked / not_executed / manual_required）
- [ ] 没有在未执行情况下写 pass
- [ ] manual_required 用例都给出可被人工执行的具体步骤
- [ ] acceptance-checklist 每项都可被人工勾选
- [ ] pass 数 + manual_required 数 ≥ 用例总数 × 90%
- [ ] 如新增测试文件，已先写 qa-file-change-plan 并经用户批准
- [ ] handoff message 列出 final_review_focus
- [ ] 所有 artifact status: ready

## validation_questions

- 测试用例覆盖了 7 维吗？
- 是否存在伪造的 pass？
- fail 用例是否给了根因分析？
- manual_required 用例的"人工步骤"是否可被一个不熟悉项目的人执行？

## allowed_next_actions

- Controller 推进 state.current_status 到 final_review_required
- Controller 设置 state.final_review_status = pending
- Controller 写 from-controller-006-handoff.md 通知用户进入最终验收
- 等待 Human Review Actor 写入 human-reviews/final-review.md

## allowed_next_actions（Human Review Actor 写完 final-review.md 且 verdict == approved 后，**严格双步**）

- Controller 第一步：state.final_review_status = approved
- Controller 第二步（独立写入）：state.current_status = completed
- Controller 第三步（条件门禁）：写 artifacts/final/final-delivery.md（仅前两步完成后）

## allowed_next_actions（verdict == rejected）

- Controller：state.final_review_status = rejected
- Controller：state.current_status = developer_processing
- Controller 写 from-controller-<seq>-status.md 通知 Dev 按 issues 修复

## forbidden_next_actions

- 把双步审核流转合并成一步
- 在 final_review_status != approved 时写 final-delivery.md
- Controller 创建、修改、伪造 final-review.md
- QA 跳过 7 维任一维度

## blocker_conditions

- 必填 Artifact 缺失或字段不完整
- 测试用例 status 字段缺失或非 5 枚举
- 越界审计 != 0（应回退到 Dev）
- pass 数 + manual_required 数 < 用例总数 × 90%
- 任一 acceptance_criteria 未满足

## flow_variants

### task_type == bugfix

- required_input_artifacts 替换为：bug_brief + regression_scope + implementation_log + changed_files
- 7 维测试中"回归"维度权重提高（必须覆盖 regression-scope 中所有受影响模块）
- 其他不变
