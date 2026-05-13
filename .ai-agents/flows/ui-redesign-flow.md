# UI Redesign Flow — UI 改版

> 用于页面视觉调整、组件样式调整、布局调整、响应式适配。

## 1. 适用场景

- 页面整体视觉刷新
- 主题色 / 字体 / 圆角 / 间距规范统一
- 已有组件样式调整（不改行为）
- 布局/响应式适配
- 设计稿（Figma 等）→ 代码

## 2. A2A task_type

`ui-redesign`

## 3. 执行顺序

```mermaid
flowchart TD
    U[User 提改版目标 + 设计稿] --> C0[Controller 创建 Task + state + active-task]
    C0 --> PM[PM: requirement + 视觉/交互拆解 + 验收标准(以设计稿为基准)]
    PM --> C1[Controller -> architect_processing]
    C1 --> AR[Architect: 样式方案 + token 映射 + 严格 file-change-plan + 行为不变性证明]
    AR --> C2[Controller -> human_review_required]
    C2 --> HR1[Human Review: 重点审'token映射 + 行为不变']
    HR1 --> C3[Controller 双步 -> developer_processing]
    C3 --> DEV[Dev: 严格按白名单改样式 + 实现日志]
    DEV --> C4[Controller -> qa_processing]
    C4 --> QA[QA: 视觉对比 + 主流程不变 + 响应式 + 暗黑模式(如适用)]
    QA --> C5[Controller -> final_review_required]
    C5 --> HR2[Human Review: final-review.md]
    HR2 --> C6[Controller 双步 -> completed]
    C6 --> FINAL[final-delivery.md]
```

## 4. Agent 调用顺序

User → Controller → PM → Controller → Architect → Controller → Human Review → Controller → Dev → Controller → QA → Controller → Human Review → Controller → final-delivery

## 5. Message 流转

与 feature-flow 相同；handoff message payload 增加 `design_source`（如 Figma URL）。

## 6. Artifact 产物

| 阶段 | Artifact | 说明 |
|---|---|---|
| PM | requirement.md | 含设计稿引用 |
| PM | prd.md | 视觉 + 交互 + 验收标准 |
| PM | task-breakdown.md | 按页面 / 组件拆解 |
| Architect | tech-plan.md | 含**token 映射方案** + 行为不变性证明 |
| Architect | file-change-plan.md | 通常以样式文件为主 |
| Architect | risk-plan.md | 重点：是否有视觉回归风险 |
| Human Review | architect-review.md | 重点："token 映射对吗 + 行为真不变" |
| Dev | implementation-log.md | 含"对照设计稿调整"记录 |
| Dev | changed-files.md | 越界审计 |
| QA | test-report.md | 含视觉对比 / 响应式 / 暗黑模式（如适用） |
| QA | acceptance-checklist.md | 含每页面对设计稿勾选 |
| Human Review | final-review.md | 重点："视觉对齐 + 主流程不变" |
| Controller | final-delivery.md | 含"前后对比截图"位（用户可补充） |

## 7. 人工审核点

- **Architect Review**：token 映射 + 行为不变性证明
- **Final Review**：视觉对齐 + 主流程没破坏

## 8. 允许修改范围

- 优先改样式文件 / 主题 token / 组件 className
- **禁止**改业务逻辑（任何 hooks / services / state 修改都视为越界）
- 改组件结构（如增删 wrapper）必须列入 file-change-plan 并标 risk

## 9. 禁止事项

- 改样式时顺手改业务逻辑
- 引入新 UI 库（除非用户批准并写入 file-change-plan owner: user-approved）
- 重构 className 体系（应另开 refactor Task）
- 跳过响应式 / 暗黑模式测试（如适用）

## 10. Blocker 条件

- 设计稿与现有 token 体系冲突 → 回到 Architect 决策
- 改版需要破坏行为 → 回到 PM 澄清优先级
- 设计稿不完整（缺空状态 / loading / error 视觉） → 回到 PM

## 11. 完成条件

- 与 feature-flow 相同
- 额外要求：acceptance-checklist 中"对设计稿"项全部 pass 或 manual_required+提供步骤

## 12. 启动 Prompt 模板

```
[A2A] 启动 UI 改版 Flow
task_type: ui-redesign
title: <一句话改版目标>
priority: P1
human_owner: <你的 handle>
改版目标:
- 页面/组件: <Settings 页 / Button 组件 / ...>
- 设计稿来源: <Figma URL 或本地路径>
- 改版范围: <仅样式 / 含布局 / 含响应式 / 含暗黑模式>
- 不允许破坏的行为: <主流程 / 权限 / 接口调用 / ...>

请 Flow Controller:
1. 在 .ai-agents/workspace/T-YYYY-NNN/ 下创建 task.md 与 state.md(current_status: pm_processing)
2. 把 active_task_id 写入 .ai-agents/workspace/active-task.md
3. 生成 from-controller-001-handoff Message 召唤 PM Agent
4. 提醒 Architect: 必须给"token 映射"与"行为不变性证明",file-change-plan 严禁含业务逻辑文件

不允许改业务逻辑,不允许写源码,不允许跳过审核。
每次回复以 [A2A] 头开始。
```
