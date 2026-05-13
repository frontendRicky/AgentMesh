---
artifact_id: A-T-YYYY-NNN-final-delivery
task_id: T-YYYY-NNN
artifact_type: final_delivery
produced_by: controller
consumed_by:
  - user
file_path: artifacts/final/final-delivery.md
version: 1
status: ready
summary: <Task 交付摘要>
dependencies:
  - A-T-YYYY-NNN-requirement
  - A-T-YYYY-NNN-prd                  # 或 bug_brief + regression_scope
  - A-T-YYYY-NNN-task-breakdown       # feature 等
  - A-T-YYYY-NNN-tech-plan
  - A-T-YYYY-NNN-file-change-plan
  - A-T-YYYY-NNN-risk-plan
  - A-T-YYYY-NNN-implementation-log
  - A-T-YYYY-NNN-changed-files
  - A-T-YYYY-NNN-test-report
  - A-T-YYYY-NNN-acceptance-checklist
  - R-T-YYYY-NNN-architect             # human review record
  - R-T-YYYY-NNN-final                 # final review record
validation_result: pass
created_at: 2026-MM-DDTHH:MM:SS+08:00
schema_version: a2a/v1
---

# Final Delivery: <task_title>

> **仅 Flow Controller 可写**。**仅在 state.final_review_status == approved AND state.current_status == completed 后才能写入**。**只引用上游 artifact 不修改**。

## 1. 任务概览

- **task_id**：T-YYYY-NNN
- **task_type**：feature / refactor / bugfix / ui-redesign / permission / api-integration
- **task_title**：<...>
- **human_owner**：<...>
- **创建于**：<...>
- **完成于**：<...>
- **总耗时**：<...>

## 2. 交付内容（按阶段）

### PM 阶段

- [requirement.md](../pm/requirement.md)
- [prd.md](../pm/prd.md)（或 bug-brief + regression-scope）
- [task-breakdown.md](../pm/task-breakdown.md)（如适用）

### Architect 阶段

- [tech-plan.md](../architect/tech-plan.md)
- [file-change-plan.md](../architect/file-change-plan.md)
- [risk-plan.md](../architect/risk-plan.md)

### Architect Review

- [architect-review.md](../../human-reviews/architect-review.md) — verdict: approved

### Dev 阶段

- [implementation-log.md](../developer/implementation-log.md)
- [changed-files.md](../developer/changed-files.md) — 越界审计：0

### QA 阶段

- [test-report.md](../qa/test-report.md) — pass/total: X/Y (≥ 90%)
- [acceptance-checklist.md](../qa/acceptance-checklist.md)

### Final Review

- [final-review.md](../../human-reviews/final-review.md) — verdict: approved

## 3. 改动摘要

- 新增文件：N
- 修改文件：N
- 删除文件：N
- 触碰依赖文件（user-approved）：N

## 4. 测试摘要

| 维度 | pass | fail | manual_required | not_executed | blocked |
|---|---|---|---|---|---|
| 主流程 | N | 0 | N | 0 | 0 |
| 异常流程 | N | 0 | N | 0 | 0 |
| 权限 | N | 0 | N | 0 | 0 |
| 空状态 | N | 0 | N | 0 | 0 |
| loading | N | 0 | N | 0 | 0 |
| 接口失败 | N | 0 | N | 0 | 0 |
| 边界 | N | 0 | N | 0 | 0 |
| 回归 | N | 0 | N | 0 | 0 |
| **合计** | **N** | **0** | **N** | **0** | **0** |

## 5. 已知遗留

- <若有未在本次解决的项目，列在这里 + 是否已开新 Task>
- <若无，写"无">

## 6. 后续建议

- <可选：如建议未来 Task / 优化点 / 监控点>

## 7. 人工审核留痕

- Architect Review：reviewer = <user>，reviewed_at = <...>，verdict = approved
- Final Review：reviewer = <user>，reviewed_at = <...>，verdict = approved

## 8. 写入门禁自检（Controller）

- [ ] state.final_review_status == approved
- [ ] state.current_status == completed
- [ ] human-reviews/final-review.md 存在且 verdict == approved
- [ ] test-report 中无未处理 fail
- [ ] 当前 Agent role == controller

> 任一不满足 → 拒绝写入本文件 → 在对话中明示原因。
