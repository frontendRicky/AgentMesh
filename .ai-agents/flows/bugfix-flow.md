# Bugfix Flow — Bug 修复

> 用于线上问题、本地复现问题、接口异常、交互异常、状态异常。**PM 不裁不跳，但产物形态轻量化**。

## 1. 适用场景

- 线上 P0 / P1 故障
- 本地稳定复现的 bug
- 接口字段不一致 / 接口失败处理不对
- 交互不符合预期（如点击无响应）
- 状态异常（如 loading 卡住、error 未消除）

## 2. A2A task_type

`bugfix`

## 3. 执行顺序

```mermaid
flowchart TD
    U[User 报告 bug] --> C0[Controller 创建 Task + state + active-task]
    C0 --> PM[PM: requirement(轻量) + bug-brief + regression-scope]
    PM --> C1[Controller -> architect_processing]
    C1 --> AR[Architect: 最小修复方案 + 严格 file-change-plan(通常 ≤5 文件) + 回滚方案]
    AR --> C2[Controller -> human_review_required]
    C2 --> HR1[Human Review: 重点审'根因是否抓准 + 修复是否最小']
    HR1 --> C3[Controller 双步 -> developer_processing]
    C3 --> DEV[Dev: 严格按白名单小步实现 + 实现日志 + 越界审计]
    DEV --> C4[Controller -> qa_processing]
    C4 --> QA[QA: 重点测'回归' + bug 复现路径 + 受影响模块]
    QA --> C5[Controller -> final_review_required]
    C5 --> HR2[Human Review: final-review.md 重点审'bug 真消除了吗']
    HR2 --> C6[Controller 双步 -> completed]
    C6 --> FINAL[final-delivery.md]
```

## 4. Agent 调用顺序

User → Controller → PM → Controller → Architect → Controller → Human Review → Controller → Dev → Controller → QA → Controller → Human Review → Controller → final-delivery

**完整 4 Agent + 2 Human Review 流程，不裁任何一步**。

## 5. Message 流转

与 feature-flow 相同，payload 中的 `prd_artifact_id` 替换为 `bug_brief_artifact_id`。

## 6. Artifact 产物

| 阶段 | Artifact | 说明 |
|---|---|---|
| PM | requirement.md | 轻量 3 段（背景 / 影响范围 / 期望） |
| PM | bug-brief.md | **必含** 4 段（复现步骤 / 根因假设 / 预期修复点 / 优先级） |
| PM | regression-scope.md | **必含** 受影响模块清单 + 需回归角色 |
| Architect | tech-plan.md | 含"最小修复方案" |
| Architect | file-change-plan.md | 通常 ≤ 5 文件，必须与 regression-scope 对应 |
| Architect | risk-plan.md | 重点：会不会引入新 bug |
| Human Review | architect-review.md | 重点："根因抓准了吗 + 修复是否最小" |
| Dev | implementation-log.md | 含 bug 复现 → 修复 → 验证的链路 |
| Dev | changed-files.md | 越界审计严格 ≤ 5 文件 |
| QA | test-report.md | "回归"维度权重最高 |
| QA | acceptance-checklist.md | 必含"按 bug-brief 复现步骤验证不再复现"项 |
| Human Review | final-review.md | 重点："bug 真消除了吗" |
| Controller | final-delivery.md | 引用所有上游产物 |

## 7. 人工审核点

- **Architect Review**：**根因 + 最小修复方案** 双重审核
- **Final Review**：**bug 实际消除验证**

## 8. 允许修改范围

- file-change-plan 必须与 regression-scope 严格对应
- 通常 ≤ 5 文件改动
- **禁止顺手修无关 bug**（应另开 Task）

## 9. 禁止事项

- 跳过 PM Agent（PM 必须出 bug-brief 与 regression-scope）
- 跳过 Architect Review
- 跳过 Final Review
- 在不知道根因的情况下"试试看"修代码（应回到 PM 澄清）
- 修复范围扩大到 regression-scope 之外
- 同时修多个 bug（应拆 N 个 Task）

## 10. Blocker 条件

- bug 无法复现 → 回到 PM，要求用户提供更详细复现步骤
- 根因不明 → 回到 Architect 加诊断方案
- 修复后回归测试发现新 bug → 回到 Dev / Architect
- changed-files 越界（修了不在 file-change-plan 的文件）

## 11. 完成条件

- `state.current_status == completed`
- final-review.md verdict == approved
- test-report 中"按 bug-brief 复现步骤验证"用例 status == pass
- regression-scope 中所有受影响模块 status == pass 或 manual_required 且步骤已执行

## 12. 启动 Prompt 模板

```
[A2A] 启动 Bug 修复 Flow
task_type: bugfix
title: <一句话 bug 描述>
priority: <P0/P1/P2>
human_owner: <你的 handle>
Bug 描述:
- 复现步骤: <step by step>
- 期望表现: <...>
- 实际表现: <...>
- 影响范围: <哪些用户 / 模块>
- 已知线索: <error log / 截图 / 接口返回>

请 Flow Controller:
1. 在 .ai-agents/workspace/T-YYYY-NNN/ 下创建 task.md 与 state.md(current_status: pm_processing)
2. 把 active_task_id 写入 .ai-agents/workspace/active-task.md
3. 生成 from-controller-001-handoff Message 召唤 PM Agent
4. 提醒 PM: 走 bugfix 变体,出 requirement(轻量) + bug-brief + regression-scope,不出完整 PRD

不裁 PM,不跳 Architect Review,不跳 Final Review,不允许写源码。
每次回复以 [A2A] 头开始。
```
