---
review_id: R-T-YYYY-NNN-architect              # architect_review 时；final_review 改 R-T-YYYY-NNN-final
task_id: T-YYYY-NNN
review_type: architect_review                  # architect_review | final_review
reviewed_artifacts:
  - A-T-YYYY-NNN-tech-plan
  - A-T-YYYY-NNN-file-change-plan
  - A-T-YYYY-NNN-risk-plan
reviewer: <真实用户 handle，不能是角色名>
reviewed_at: 2026-MM-DDTHH:MM:SS+08:00
verdict: approved | rejected | needs_changes
issues:
  - severity: blocker | major | minor
    description: <问题描述>
    affected_artifact: A-T-YYYY-NNN-<artifact-type>
followup_required: true | false
notes: <可选说明>
schema_version: a2a/v1
---

# Human Review Record: <task_title>

> **仅 Human Review Actor 创建**（用户给 verdict 后由 Cursor 按用户指令代写）。
> Controller / 任何专业 Agent 都**不允许**创建、修改、伪造本文件。
> 主键：`review_id`。**禁止**给本文件添加 artifact_id（虽然 artifact_type 算 review record，但物理路径在 human-reviews/）。

## 1. 我审阅了什么

- [artifacts/architect/tech-plan.md](../artifacts/architect/tech-plan.md)
- [artifacts/architect/file-change-plan.md](../artifacts/architect/file-change-plan.md)
- [artifacts/architect/risk-plan.md](../artifacts/architect/risk-plan.md)

## 2. 我的判断

- **verdict**：approved | rejected | needs_changes

## 3. 发现的问题（rejected / needs_changes 时必填）

### Issue 1

- **severity**: blocker | major | minor
- **description**: <详细描述>
- **affected_artifact**: A-T-YYYY-NNN-<artifact-type>
- **建议修改**: <可选>

### Issue 2

...

## 4. 我对下游 Agent 的额外要求

- <额外约束 / 提醒，可选>

## 5. 备注

<可选>

---

## 文件路径约定

- Architect Review → `workspace/<task-id>/human-reviews/architect-review.md`
- Final Review → `workspace/<task-id>/human-reviews/final-review.md`

## Controller 后续动作

- 校验本 record 字段完整 → 翻 `state.human_review_status` 或 `state.final_review_status`
- 翻状态后，独立推 `state.current_status`（**双步流转**）
