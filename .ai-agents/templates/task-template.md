---
task_id: T-YYYY-NNN
task_type: feature | refactor | bugfix | ui-redesign | permission | api-integration
task_title: <一句话标题>
created_by: user
human_owner: <用户 handle>
priority: P0 | P1 | P2
scope:
  in_scope:
    - <明确包含>
  out_of_scope:
    - <明确排除>
constraints:
  - <技术 / 时间 / 兼容性约束>
initial_input_messages:
  - M-T-YYYY-NNN-000
required_artifacts:
  - requirement
  - prd                    # bugfix 改为 bug_brief + regression_scope,无 prd
  - task_breakdown         # bugfix 时按需
  - tech_plan
  - file_change_plan
  - risk_plan
  - implementation_log
  - changed_files
  - test_report
  - acceptance_checklist
  - human_review_record
  - final_review_record
  - final_delivery
created_at: 2026-MM-DDTHH:MM:SS+08:00
schema_version: a2a/v1
---

# Task: <task_title>

> **静态元信息**。创建后不再变更。运行时状态全部落 state.md。

## 1. 背景

<为什么要做这个 Task,业务背景与目标>

## 2. 范围

### in_scope

- <包含>

### out_of_scope

- <排除>

## 3. 约束

- <约束 1>
- <约束 2>

## 4. 原始需求

<复制用户的原始需求文本,作为留档>

---

> **禁止**在本文件添加任何动态状态字段（current_status / current_agent / human_review_status / blockers / produced_artifacts / updated_at 等）。这些字段的唯一来源是 state.md。
