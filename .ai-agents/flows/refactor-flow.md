# Refactor Flow — 重构

> 用于组件重构、模块重构、状态管理重构、路由重构、样式重构。

## 1. 适用场景

- 组件级重构（拆/合/抽象）
- 模块级重构（如把 service 层重新分包）
- 状态管理重构（如从 Context 切到 Zustand）
- 路由重构（如 Pages Router → App Router）
- 样式重构（如 SCSS → Tailwind）

## 2. A2A task_type

`refactor`

## 3. 执行顺序

```mermaid
flowchart TD
    U[User 提重构目标 + 边界] --> C0[Controller 创建 Task + state + active-task]
    C0 --> PM[PM: 重构需求 + 影响清单 + 不破坏旧功能的验收标准]
    PM --> C1[Controller -> architect_processing]
    C1 --> AR[Architect: 重构方案(必含'最小可行') + 严格 file-change-plan + 兼容回滚方案]
    AR --> C2[Controller -> human_review_required]
    C2 --> HR1[Human Review: 重点审'有没有扩大范围']
    HR1 --> C3[Controller 双步 -> developer_processing]
    C3 --> DEV[Dev: 严格按白名单小步重构 + 实现日志 + 越界审计]
    DEV --> C4[Controller -> qa_processing]
    C4 --> QA[QA: 重点测'回归' + 旧功能不破坏]
    QA --> C5[Controller -> final_review_required]
    C5 --> HR2[Human Review: final-review.md]
    HR2 --> C6[Controller 双步 -> completed]
    C6 --> FINAL[final-delivery.md]
```

## 4. Agent 调用顺序

User → Controller → PM → Controller → Architect → Controller → Human Review → Controller → Dev → Controller → QA → Controller → Human Review → Controller → final-delivery

## 5. Message 流转

与 feature-flow 相同（7 条核心 message）。

## 6. Artifact 产物

与 feature-flow 相同（13 件 artifact + 2 份 review record + final-delivery）。

PRD 章节侧重"重构前 vs 重构后差异"与"哪些行为必须保持完全一致"。

## 7. 人工审核点

- **Architect Review**：**重点审"是否扩大重构范围"** + 兼容性回滚方案
- **Final Review**：**重点审"旧功能没被破坏"**

## 8. 允许修改范围

- file-change-plan 必须列出**所有**被重构的文件
- **禁止顺手优化无关代码**：任何 file-change-plan 之外的"小修小补"都视为越界
- Architect 必须给出"重构停止线"：哪些代码被划入本次范围，哪些被显式排除

## 9. 禁止事项

- **顺手重构无关模块**（这是 refactor 最常见违规）
- 删旧逻辑未在 file-change-plan 标 operation: delete
- 引入新依赖（除非用户批准）
- 同时改架构 + 改业务（应拆 2 个 Task）
- 用 mock 替代真实数据进入正式逻辑

## 10. Blocker 条件

- 重构边界不清（应回到 PM 阶段澄清）
- file-change-plan 与实际重构范围有出入
- 旧功能在 QA 阶段大量回归失败（应回到 Dev / Architect）
- 需要触碰 file-change-plan 之外的文件才能完成（必发 blocker-request）

## 11. 完成条件

- 与 feature-flow 相同
- 额外要求 QA 的 acceptance-checklist 中"回归项"全部 pass 或 manual_required+提供步骤

## 12. 启动 Prompt 模板

```
[A2A] 启动重构 Flow
task_type: refactor
title: <一句话重构目标>
priority: P1
human_owner: <你的 handle>
重构目标:
<重构前现状 / 重构后期望 / 不允许破坏的行为列表 / 严格的范围边界>

请 Flow Controller:
1. 在 .ai-agents/workspace/T-YYYY-NNN/ 下创建 task.md 与 state.md(current_status: pm_processing)
2. 把 active_task_id 写入 .ai-agents/workspace/active-task.md
3. 生成 from-controller-001-handoff Message 召唤 PM Agent
4. 提醒 Architect: 必须给"重构停止线",file-change-plan 不允许任何模糊条目

不允许扩大重构范围,不允许写源码,不允许跳过审核。
每次回复以 [A2A] 头开始。
```
