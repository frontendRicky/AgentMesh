---
contract_id: HC-pm-to-architect
from_agent: pm
to_agent: architect
schema_version: a2a/v1
---

## required_input_artifacts

- artifact_type: requirement, status: ready

## required_output_artifacts

> 默认（feature/refactor/permission/api-integration/ui-redesign）：

- artifact_type: requirement, status: ready
- artifact_type: prd, status: ready
- artifact_type: task_breakdown, status: ready

## required_input_messages

- file: messages/from-controller-001-handoff.md
  message_type: handoff
  intent: user_to_pm_handoff

## required_output_messages

- file: messages/from-pm-<seq>-handoff.md
  message_type: handoff
  intent: pm_to_architect_handoff
  to_agent: architect
  payload 必含:
    - prd_artifact_id（或 bug_brief_artifact_id，bugfix 时）
    - task_breakdown_artifact_id（feature 等时）
    - open_questions
    - architect_must_answer

## required_input_review_records

- (无)

## required_output_review_records

- (无)

## acceptance_criteria

- [ ] PRD 含 用户角色 / 核心流程 / 页面交互 / 权限规则（5 层） / 异常状态 / 边界场景
- [ ] PRD 含 loading / empty / error / success 四态显式定义
- [ ] PRD 含验收标准（可被 QA 直接转测试用例）
- [ ] PRD 列出所有"待确认"问题（不假设、不臆断）
- [ ] task-breakdown 每个子任务可独立估期且依赖明确
- [ ] handoff message 列出 architect_must_answer
- [ ] 所有 artifact status: ready

## validation_questions

- PRD 是否覆盖所有"待确认"标记？
- 验收标准是否可被 QA 直接转为测试用例？
- 是否定义了所有页面状态（loading / empty / error / success）？
- task-breakdown 是否明确每个子任务的依赖与估期？

## allowed_next_actions

- Controller 推进 state.current_status 到 architect_processing
- Architect 读取 PRD，启动 architect_processing

## forbidden_next_actions

- 跳过 PRD 直接写 Tech Plan
- 直接写代码
- 把 handoff message 归类为 Artifact

## blocker_conditions

- 必填 Artifact 缺失或字段不完整
- 必填 Message 缺失或 payload 缺 architect_must_answer
- 任一 acceptance_criteria 未满足

## flow_variants

### task_type == bugfix

- **PM 不裁不跳**：仍由 PM Agent 出产物，但产物形态变为轻量
- required_output_artifacts 替换为：
  - artifact_type: requirement (lightweight，3 段：背景 / 影响范围 / 期望)
  - artifact_type: bug_brief（4 段：复现步骤 / 根因假设 / 预期修复点 / 优先级）
  - artifact_type: regression_scope（受影响模块 / 需回归角色）
- **不要求**完整 prd
- **不要求** task_breakdown（除非 bugfix 实际跨多个模块）
- required_output_messages 不变（仍发 from-pm-<seq>-handoff.md，payload 中 prd_artifact_id 改为 bug_brief_artifact_id）
- acceptance_criteria 替换为：
  - [ ] bug-brief 含 复现步骤 / 根因假设 / 预期修复点 / 优先级 4 段
  - [ ] regression-scope 至少列 1 个回归模块
  - [ ] handoff message 列出"Architect 必须回答的最小修复方案问题"
  - [ ] requirement (lightweight) 已写
- blocker_conditions 替换为：根因不明、无复现步骤、bug-brief 缺"预期修复点"
- **不跳过** Architect → 仍走 architect_processing
- **不跳过** Architect Review → 仍走 human_review_required
- **不跳过** Final Review → 仍走 final_review_required
