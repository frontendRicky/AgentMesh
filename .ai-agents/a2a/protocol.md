---
protocol_version: v1.0.0
schema_version: a2a/v1
frozen_at: 2026-05-11
---

# A2A Protocol — 总章

> 本地 File-based Agent-to-Agent 协议总章。所有 Agent / Controller / Human Review Actor 必须遵循。
> **当前协议版本：`v1.0.0`，已于 2026-05-11 冻结**（详 §6 v1.0.0 冻结声明）。

## 1. 设计目标

1. 所有 Agent 之间通过**文件**交接，不依赖任何运行时服务
2. **任务静态信息（task.md）与动态状态（state.md）严格分离**
3. **写权限路径级隔离**：每个 Agent 只能写自己的 `artifacts/<role>/` 与 `messages/from-<role>-*.md`
4. **强制不可跳步**：PRD → Tech Plan → Human Review → Code → QA → Final Review
5. **写代码双门禁**：`current_status == developer_processing` AND `human_review_status == approved`
6. **可审计**：所有产物含 `task_id` / `created_at` / `schema_version` / `produced_by`

## 2. 协议元素

| 元素 | Schema 文件 | 说明 |
|---|---|---|
| Agent Card | `agent-card.schema.md` | Agent 能力、读写权限、上下游声明 |
| Task | `task.schema.md` | 静态任务元信息（创建后不变） |
| State | `state.schema.md` | 动态状态源（仅 Controller 写） |
| Message | `message.schema.md` | Agent 之间的通信单元 |
| Artifact | `artifact.schema.md` | Agent 产出的内容型文件（PRD / Tech Plan / 代码改动记录等） |
| Handoff Contract | `handoff-contract.schema.md` | Agent → Agent 的交接契约 |
| Blocker | `blocker.schema.md` | 流转受阻的正式记录（仅 Controller 写） |
| Review Record | `review.schema.md` | 人工审核留痕（仅 Human Review Actor 写） |
| State Machine | `state-machine.md` | `current_status` 合法迁移与转移规则 |
| File Message Bus | `file-message-bus.md` | 文件命名约定与读写约定 |

## 3. 角色分工

| 角色 | 职责 | 写权限范围 |
|---|---|---|
| User | 提需求、做人工审核决策 | 通过 Cursor 间接驱动 |
| Flow Controller | 调度 / 校验 / 状态流转 / 创建正式 Blocker | `task.md` / `state.md` / `blockers/**` / `messages/from-controller-*.md` / `workspace/active-task.md` / 仅 final_review_status==approved 后的 `artifacts/final/**` |
| PM Agent | 产出 PRD / 任务拆解 | `artifacts/pm/**` / `messages/from-pm-*.md` |
| Architect Agent | 产出技术方案 / 文件改动白名单 / 风险方案 | `artifacts/architect/**` / `messages/from-architect-*.md` |
| Senior FE Dev Agent | 写代码（双门禁） / 实现日志 / 改动清单 | `artifacts/developer/**` / `messages/from-developer-*.md` / 项目源码命中 file-change-plan 白名单的文件 |
| QA Agent | 测试报告 / 验收清单 / qa-file-change-plan | `artifacts/qa/**` / `messages/from-qa-*.md` / 经授权的测试文件 |
| Human Review Actor | 写 review record（用户给 verdict 后由 Cursor 代写） | `human-reviews/architect-review.md` / `human-reviews/final-review.md` |

## 4. 16 条硬约束

详见 `../rules/a2a-rules.md`。最关键：

1. 没有 Task 不允许启动 Agent
2. 没有上游 Artifact 不允许下游执行
3. 没有 Handoff Message 不允许流转
4. 写代码双门禁：current_status == developer_processing AND human_review_status == approved
5. Agent 只能发 Blocker Request Message，正式 Blocker 唯一由 Controller 写
6. 下游 Agent 必须先校验上游 Artifact
7. 每个 Agent 只能写自己的 workspace 路径
8. 业务代码只能由 Senior FE Dev 修改
9. QA 默认源码只读，写测试文件须 qa-file-change-plan 授权
10. Architect 严禁任何源码 Write/StrReplace/Delete/Create
11. Controller 不能写 `artifacts/{pm,architect,developer,qa}/**`，仅在 final_review_status==approved 后写 `artifacts/final/final-delivery.md`
12. 任何审核结果必须由 Controller 校验 review record 后才能从 pending 翻转
13. Human Review Record 仅由 Human Review Actor 创建
14. task.md 创建后不得变更，运行时状态只能落 state.md（仅 Controller 写）
15. 正式 Blocker 仅 Controller 创建，且必须读取触发它的 Request Message 或自校验失败原因
16. Cursor 识别 Task 按 4 步严格优先级，多 Task 必询问

## 5. 协议版本

`schema_version: a2a/v1`

每个 Schema 文件、Card、Task、State、Message、Artifact、Blocker、Review Record 都必须含 `schema_version` 字段。

## 6. v1.0.0 冻结声明

| 字段 | 值 |
|---|---|
| protocol_version | v1.0.0 |
| schema_version | a2a/v1 |
| frozen_at | 2026-05-11 |
| frozen_after | mini regression T-2026-002 全过（F-01~F-09）|

### 冻结后的纪律（强约束）

- **Python Runtime V1 必须兼容该版本**：实现必须按本协议 schema / state-machine / handoff contract / 5 条门禁 / 两阶段 Blocker / 双步审核 / gate_failure vs blocker_request 区分 / 中间态恢复 等机制原样落地，不得自行扩展或裁剪
- **任何破坏性协议改动必须升级为 v2**：新建 `a2a/v2/**` schema 目录与 `schema_version: a2a/v2`，与 v1 并存
- **v1 Task 不强制迁移到 v2**：已存在的 `T-YYYY-NNN/` 任务可继续按 v1 跑完；新 Task 可选择 v1 或 v2
- **Python Runtime V1 阶段只能读取和执行协议，不允许修改协议结构**：Runtime 仅负责把 Markdown File-based 实现替换为 in-memory state + persistence layer，业务逻辑层零变动
- **冻结后修复**：仅允许在不破坏字段结构与状态机迁移的前提下修补文档措辞 / 例子 / 反例；任何字段增删、enum 增减、迁移路径增减都必须升 v2

### 冻结后的可写文件白名单（v1 阶段）

- 文档级修补（措辞、例子）：允许
- 新建 `examples/` 下的归档：允许
- `workspace/` 下创建新 Task：允许（按 v1 协议）
- 修改 schema / rule / agent / agent-card / handoff / template 的字段、enum、状态、转移规则：**禁止**（须 v2）

### 关联工件

- 冻结依据：[CHANGELOG.md](../CHANGELOG.md) v1.0.0 条目
- mini regression 证据链：[workspace/T-2026-002/](../workspace/T-2026-002/)
- 试运行历史归档：[examples/feature-add-settings-page/T-2026-001/](../examples/feature-add-settings-page/T-2026-001/)
