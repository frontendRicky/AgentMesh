# API Integration Flow — 接口联调

> 用于新接口接入、旧接口替换、字段调整、错误处理、loading 和 empty 状态处理。

## 1. 适用场景

- 新接口接入（前后端联调）
- 旧接口替换（v1 → v2）
- 字段调整（增 / 删 / 改 字段）
- 错误处理增强（4xx / 5xx / 超时）
- loading / empty / error 状态补齐

## 2. A2A task_type

`api-integration`

## 3. 执行顺序

```mermaid
flowchart TD
    U[User 提接口联调目标 + API doc] --> C0[Controller 创建 Task + state + active-task]
    C0 --> PM[PM: requirement + 接口契约 + UI 状态(loading/empty/error/success) + 验收标准]
    PM --> C1[Controller -> architect_processing]
    C1 --> AR[Architect: service 层方案 + 类型定义 + 错误处理 + 严格 file-change-plan + mock 策略]
    AR --> C2[Controller -> human_review_required]
    C2 --> HR1[Human Review: 重点审'契约对齐 + 错误处理 + loading/empty/error 全覆盖']
    HR1 --> C3[Controller 双步 -> developer_processing]
    C3 --> DEV[Dev: 严格按白名单实现 service / type / hook / 状态机 + 实现日志]
    DEV --> C4[Controller -> qa_processing]
    C4 --> QA[QA: 4xx/5xx/超时/字段缺失/loading/empty/success 全覆盖 + 回归]
    QA --> C5[Controller -> final_review_required]
    C5 --> HR2[Human Review: final-review.md]
    HR2 --> C6[Controller 双步 -> completed]
    C6 --> FINAL[final-delivery.md]
```

## 4. Agent 调用顺序

User → Controller → PM → Controller → Architect → Controller → Human Review → Controller → Dev → Controller → QA → Controller → Human Review → Controller → final-delivery

## 5. Message 流转

与 feature-flow 相同；handoff message payload 增加 `api_contract_summary`（接口契约摘要）。

## 6. Artifact 产物

| 阶段 | Artifact | 说明 |
|---|---|---|
| PM | requirement.md | 接口背景 |
| PM | prd.md | **必含接口契约**（路径 / 方法 / req / res / 错误码） + 4 态 UI 定义 + 验收标准 |
| PM | task-breakdown.md | 按接口 × UI 状态 拆解 |
| Architect | tech-plan.md | service 层结构 + type 定义 + 错误处理策略 + 重试 / 降级 / 缓存 |
| Architect | file-change-plan.md | service / type / hook / 状态机相关文件 |
| Architect | risk-plan.md | 重点：契约不一致 / 性能 / 安全 |
| Human Review | architect-review.md | 重点："契约对齐 + 4 态全覆盖 + 错误处理到位" |
| Dev | implementation-log.md | 含"哪个接口对应哪个 service / hook"记录 |
| Dev | changed-files.md | 越界审计 |
| QA | test-report.md | 4xx / 5xx / 超时 / 字段缺失 / loading / empty / success 全覆盖 + 回归 |
| QA | acceptance-checklist.md | 含每个接口 × 每个 UI 状态勾选 |
| Human Review | final-review.md | 重点："4 态都对吗 + 错误真处理了吗" |
| Controller | final-delivery.md | 含接口清单 + 错误处理矩阵 |

## 7. 人工审核点

- **Architect Review**：契约对齐 + 错误处理策略 + 4 态全覆盖
- **Final Review**：4 态实测 + 错误处理实测

## 8. 允许修改范围

- service 层 / type 层 / hook 层 / 状态机
- 调用方组件的接入代码
- **禁止**改业务核心逻辑（仅接入，不改语义）

## 9. 禁止事项

- 跳过 loading / empty / error / success 任一态
- 跳过 4xx / 5xx / 超时 任一错误处理
- 把 mock 留在正式逻辑中
- 写死接口 URL / 字段名（应抽常量或来自配置）
- 不处理字段缺失 / 字段类型异常
- 不写降级方案

## 10. Blocker 条件

- 接口契约未定 → 回到 PM 追后端确认
- 后端未给错误码列表 → 回到 PM
- 字段语义不清 → 回到 PM 追后端确认
- 性能 / 并发未达标 → 回到 Architect 加缓存 / 节流

## 11. 完成条件

- 与 feature-flow 相同
- 额外要求：acceptance-checklist 中**每个接口 × 每个 UI 状态**至少 1 个用例 status ∈ { pass, manual_required+步骤 }

## 12. 启动 Prompt 模板

```
[A2A] 启动接口联调 Flow
task_type: api-integration
title: <一句话联调目标>
priority: P1
human_owner: <你的 handle>
联调目标:
- 接口列表: <GET /api/xxx / POST /api/yyy / ...>
- 接口文档: <Swagger URL / 本地 doc 路径>
- 错误码: <400 / 401 / 500 / ...>
- UI 状态: <loading / empty / error / success 的视觉与文案>
- 不允许破坏的行为: <主流程 / 旧接口 / ...>

请 Flow Controller:
1. 在 .ai-agents/workspace/T-YYYY-NNN/ 下创建 task.md 与 state.md(current_status: pm_processing)
2. 把 active_task_id 写入 .ai-agents/workspace/active-task.md
3. 生成 from-controller-001-handoff Message 召唤 PM Agent
4. 提醒 PM: PRD 必含接口契约 + 4 态 UI 定义 + 错误码处理

不允许把 mock 留正式逻辑,不允许跳过 4 态任一,不允许写源码,不允许跳过审核。
每次回复以 [A2A] 头开始。
```
