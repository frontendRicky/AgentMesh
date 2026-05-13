---
contract_id: HC-user-to-pm
from_agent: user
to_agent: pm
schema_version: a2a/v1
---

## required_input_artifacts

- (无 — User 是源头)

## required_output_artifacts

- artifact_type: requirement, status: ready
  - feature/refactor/permission/api-integration/ui-redesign：完整版
  - bugfix：轻量 3 段版（背景 / 影响范围 / 期望）

## required_input_messages

- (无 — User 通过 Cursor 对话直接驱动 Controller)

## required_output_messages

- file: workspace/<task-id>/messages/from-controller-001-handoff.md
  message_type: handoff
  intent: user_to_pm_handoff（由 Controller 代写）
  to_agent: pm

## required_input_review_records

- (无)

## required_output_review_records

- (无)

## acceptance_criteria

- [ ] 用户已给出 task_type / task_title / priority / human_owner / 原始需求
- [ ] Controller 已创建 task.md（仅静态元信息）
- [ ] Controller 已创建 state.md（current_status: pm_processing）
- [ ] workspace/active-task.md 已设为该 task_id
- [ ] from-controller-001-handoff message 已发出
- [ ] PM 已 Read 全部必读清单

## validation_questions

- 用户原始需求是否包含明确的 task_type？
- 用户是否给出了 scope.in_scope 与 scope.out_of_scope？
- 是否有正在运行的其他 active-task 需要先完成或显式切换？

## allowed_next_actions

- PM Agent 启动，按 product-manager.agent.md 工作流执行

## forbidden_next_actions

- 跳过 task.md / state.md 创建直接召唤 PM
- 把动态状态字段写进 task.md
- 用户原始需求严重不完整时强行创建 Task

## blocker_conditions

- 用户原始需求严重不完整或自相矛盾
- task.md 创建后 schema 校验失败（缺字段或含动态状态）
- workspace 中已有 active-task 但用户未明确要求切换或新建

## flow_variants

### task_type == bugfix

- required_output_artifacts 在 PM 阶段会替换为：requirement (lightweight) + bug-brief + regression-scope（详见 product-manager-to-architect.md 的 bugfix 变体）
- 本 contract（user → pm）内容不变
