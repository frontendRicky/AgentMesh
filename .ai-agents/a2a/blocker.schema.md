# Blocker Schema

> 流转受阻的正式记录。**两阶段创建**：触发 Agent 只发 Blocker Request Message，正式 `blockers/B-*.md` 仅由 Flow Controller 创建。

## 1. 两阶段流程

### 阶段 A：Blocker Request（由触发 Agent 发起）

PM / Architect / Dev / QA 在自检失败、上游缺漏、自身条件不满足时：

- **只能创建 `messages/from-<role>-<seq>-blocker-request.md`**（按 Message Schema，`message_type: blocker`，`intent: blocker_request`）
- **不允许**直接写 `blockers/B-*.md`
- **不允许**写 `state.md` 任何字段

### 阶段 B：正式 Blocker（仅 Flow Controller 创建）

Controller 监听到 Blocker Request 或自身校验失败后：

1. 读取 Blocker Request Message（或记录自校验失败原因）
2. 校验 / 调整 proposed 字段（必要时改 resume_to_agent）
3. 创建 `blockers/B-<task-id>-<seq>.md`（按下方 11 字段 Schema）
4. 同步更新 `state.md`：
   - `previous_status = current_status`
   - `current_status = blocked`
   - `blocked_context` 镜像 11 字段
   - `active_blocker = blocker_id`
   - `blockers_history` 追加
5. 写一条 `messages/from-controller-<seq>-blocker.md` 通知 `resume_to_agent`

## 2. 字段定义（11 字段）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `blocker_id` | string | 是 | 全局唯一，格式 `B-<task_id>-<seq>` |
| `task_id` | string | 是 | 所属 Task |
| `blocked_from_agent` | enum | 是 | 触发它的 Agent role |
| `blocked_from_status` | enum | 是 | 被阻塞前的 `state.current_status` |
| `resume_to_agent` | enum | 是 | 谁来修复 |
| `resume_to_status` | enum | 是 | 修复后该跳到的 status |
| `blocking_reason` | string | 是 | 一句话根因 |
| `missing_artifacts` | string[] | 是 | 缺失的 artifact_type 列表（无则 `[]`） |
| `required_fix` | string | 是 | 一句话修复指引 |
| `created_by` | string | 是 | **永远是 `controller`**；原始触发 Agent 记录在 `blocked_from_agent` |
| `source_request_message` | string\|null | 是 | 引用触发它的 blocker request message_id；若 Controller 自校验失败则 `null` |
| `created_at` | ISO8601 | 是 | 创建时间 |
| `schema_version` | string | 是 | 固定 `a2a/v1` |

## 3. 示例 Frontmatter

### 3.1 来自 Dev 的 Blocker Request → Controller 创建正式 Blocker

```yaml
---
blocker_id: B-T-2026-001-001
task_id: T-2026-001
blocked_from_agent: developer
blocked_from_status: developer_processing
resume_to_agent: architect
resume_to_status: developer_processing            # 见 §6 resume_to_status 语义说明：局部修复后回 developer_processing,不必无谓回 architect_processing
blocking_reason: file-change-plan 缺 src/services/settings.ts 但 PRD 要求新接口
missing_artifacts: [file_change_plan]
required_fix: 重新出 file-change-plan,补 src/services/settings.ts 条目(operation: create, allowed: yes)
created_by: controller
source_request_message: M-T-2026-001-007
created_at: 2026-05-09T15:30:00+08:00
schema_version: a2a/v1
---
```

### 3.2 Controller 自校验失败（无 Request 来源）

```yaml
---
blocker_id: B-T-2026-001-002
task_id: T-2026-001
blocked_from_agent: pm
blocked_from_status: pm_completed
resume_to_agent: pm
resume_to_status: pm_processing
blocking_reason: pm-to-architect handoff message 缺失,无法推进 architect_processing
missing_artifacts: []
required_fix: PM 补充 messages/from-pm-002-handoff.md,列出 Architect 必须回答的问题
created_by: controller
source_request_message: null
created_at: 2026-05-09T11:30:00+08:00
schema_version: a2a/v1
---
```

## 4. 文件正文要求

frontmatter 之后，正文必须包含：

```markdown
## 已读取的上游 Artifact 与缺漏点
- A-T-2026-001-prd: ready
- A-T-2026-001-tech-plan: ready
- A-T-2026-001-file-change-plan: ready,但缺 src/services/settings.ts 条目

## 给 resume_to_agent 的具体修复指引
1. 重新打开 artifacts/architect/file-change-plan.md
2. 在白名单表追加一行:
   - path: src/services/settings.ts
   - operation: create
   - allowed: yes
   - reason: 实现 Settings 持久化需要 service
   - risk: 低,新增独立文件
     - owner: developer
   - notes: 与 useSettings hook 配合
3. 把 file_change_plan 的 status 设为 ready,version 升到 2,把 v1 移到 archive/

## 估计修复成本(可选)
- 5 分钟
```

## 5. 校验规则

- `blocker_id` 必须符合 `^B-T-\d{4}-\d{3}-\d{3}$`
- `created_by` 必须是 `controller`，任何其他值视为越权
- `resume_to_status` 必须是 state-machine 中合法的状态值
- `source_request_message` 必须真实存在或为 `null`
- 同一时间 `state.active_blocker` 只能有一个；如要触发新 Blocker，先恢复或显式作废上一个

## 6. resume_to_status 语义（F-06）

`resume_to_status` 表示 **修复完成后 Controller 应推进到的目标状态**，不要求等于 `blocked_from_status`：

| 场景 | blocked_from_status | resume_to_status | 说明 |
|---|---|---|---|
| 局部修复（如 file-change-plan 补条目） | `developer_processing` | `developer_processing` | Architect 局部补完即可，**禁止**无谓地把 state 退回 `architect_processing` |
| 全局返工（如 tech-plan 重做） | `developer_processing` | `architect_processing` | 必须重走完整 architect 阶段 |
| Architect Review 必须重审 | `developer_processing` | `human_review_required` | Controller 同步把 `human_review_status` 重置为 `pending` |
| PM handoff 缺 message | `architect_processing` | `pm_completed` | PM 阶段补完 handoff 即可 |

**Controller 决策流程**：

1. Read blocker request 的 `proposed_resume_to_status`
2. 评估 `required_fix` 范围：
   - 仅修复 1 个 artifact 且不影响下游决策 → 选最近的"可继续"状态（通常 == `blocked_from_status`）
   - 修复涉及多个 artifact 或改变上游决策 → 选更早的状态
3. 在正式 `blockers/B-*.md` 的 `resume_to_status` 字段中**记录最终决策**（可与 proposed 不同）
4. 在 `blocker.md` 正文 §"resume 决策" 中说明取舍原因

## 7. 常见违规示例

### 反例 1：Agent 直接写 blockers/

```
developer 写了 blockers/B-T-2026-001-001.md   # 错误!Agent 只能发 from-developer-*-blocker-request.md
```

### 反例 2：created_by 写成 developer

```yaml
created_by: developer   # 错误!永远是 controller
```

### 反例 3：source_request_message 引用不存在的 message_id

```yaml
source_request_message: M-T-2026-001-099   # 错误!该 message 不存在
```

### 反例 4：resume_to_status 不合法

```yaml
resume_to_status: human_review_approved   # 错误!这不是 14 状态枚举之一
```

### 反例 5：误把 gate_failure 当 blocker 处理

如果 Agent 用 `message_type: gate_failure` + `intent: write_gate_failed` 报告"5 条门禁未达"，Controller **不应**创建正式 Blocker，**不应**改 `state.current_status` 为 `blocked`。详 `message.schema.md §2.1`。

## 8. 下游使用方式

- Controller 创建 Blocker 后，写 `from-controller-*-blocker.md` 通知 `resume_to_agent`
- 被通知的 Agent 按 `required_fix` 行动，完成后通知 Controller
- Controller 校验缺失 artifact 已补齐 → 推进 `state.current_status` 到 `blocked_context.resume_to_status`，清空 `blocked_context` 与 `active_blocker`
- `blockers_history` 永久保留所有 blocker_id，用于审计
