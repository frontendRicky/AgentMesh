# State Schema

> `state.md` 是 Task 的**唯一动态状态源**。**只有 Flow Controller 可写**，其他所有 Agent 只读。

## 1. 字段定义

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `task_id` | string | 是 | 与 task.md 同一 task_id |
| `current_status` | enum | 是 | 14 个状态之一（见 state-machine.md） |
| `previous_status` | enum | 是 | 上一次的 current_status |
| `current_agent` | enum | 是 | `pm` / `architect` / `developer` / `qa` / `controller` / `human` / `none` |
| `next_agent` | enum | 是 | 下一个预期 Agent，可为 `none` |
| `allowed_next_statuses` | string[] | 是 | 由 state-machine 推导，Controller 据此判断流转合法性 |
| `human_review_status` | enum | 是 | `not_required` / `pending` / `approved` / `rejected` |
| `final_review_status` | enum | 是 | `not_required` / `pending` / `approved` / `rejected` |
| `produced_artifacts` | string[] | 否 | 已产出的 artifact_id 列表 |
| `active_blocker` | string\|null | 否 | 当前激活的 blocker_id，无则为 null |
| `blockers_history` | string[] | 否 | 全部历史 blocker_id 列表 |
| `blocked_context` | object\|null | 否 | 仅 current_status == blocked 时填写 |
| `updated_at` | ISO8601 | 是 | 每次写入更新 |
| `schema_version` | string | 是 | 固定 `a2a/v1` |

### blocked_context 子字段

```yaml
blocked_context:
  blocker_id: B-T-2026-001-001
  blocked_from_agent: <role>           # pm/architect/developer/qa（不可为 dev）
  blocked_from_status: <status before blocked>
  resume_to_agent: <role>              # pm/architect/developer/qa
  resume_to_status: <status>           # 必须是 14 状态枚举值；通常是局部修复后能直接回到的最近上游可恢复点（详见 blocker.schema.md §6）
  blocking_reason: <one sentence>
  missing_artifacts: [<artifact-type>, ...]
  required_fix: <one sentence>
```

## 2. 关键约束

### 2.1 写权限

- **仅 Flow Controller 可写 `state.md`**
- PM / Architect / Dev / QA 都不允许写
- 即使是写自己角色相关的字段（如 `current_agent`），也必须由 Controller 代写

### 2.2 current_status 枚举（14 个，明确不含审核结果）

```
created
pm_processing      pm_completed
architect_processing  architect_completed
human_review_required
developer_processing  developer_completed
qa_processing      qa_completed
final_review_required
completed
blocked
cancelled
```

**严禁**把 `human_review_approved` / `human_review_rejected` / `final_approved` / `final_rejected` 写进 `current_status`；这些信息由独立的 `human_review_status` / `final_review_status` 字段承载。

### 2.3 审核翻转双步

`human_review_required → developer_processing` 必须分两步：

1. **第一步**：`human_review_status: pending → approved`
2. **第二步**：`current_status: human_review_required → developer_processing`

任何把这两步合并的 Controller 实现都视为违规。

### 2.4 写代码门禁

Senior FE Developer 写代码门禁：

- `current_status == developer_processing` AND `human_review_status == approved`
- 仅满足其一不算授权

### 2.5 双步流转中间态合法性 + Controller 启动恢复（F-08）

以下两组**中间态**是合法的：

| 中间态 | current_status | human_review_status | final_review_status | 含义 |
|---|---|---|---|---|
| Architect Review 双步之间 | `human_review_required` | `approved` | `not_required` 或 `pending` | 第 1 步已写，第 2 步未写 |
| Final Review 双步之间 | `final_review_required` | `approved` | `approved` | 第 1 步已写，第 2 步未写 |

**Flow Controller 启动时必须自检中间态**：

```
读 state.md →
  if (current_status == 'human_review_required' AND human_review_status == 'approved'):
      重新校验 human-reviews/architect-review.md（仍 verdict=approved 且字段完整）
      → 自动补做第 2 步：current_status = developer_processing, current_agent = developer, next_agent = qa
      → 写 from-controller-<seq>-recover-handoff.md 通知 Developer
  if (current_status == 'final_review_required' AND final_review_status == 'approved'):
      重新校验 human-reviews/final-review.md（仍 verdict=approved 且字段完整）
      → 自动补做第 2 步：current_status = completed, current_agent = controller, next_agent = none
      → 走场景 F 写 final-delivery.md
      → 写 from-controller-<seq>-final.md 通知用户
  否则: 按场景 B/C/D/E/F 正常处理
```

恢复时禁止：
- 跳过重新校验 review record
- 修改 review record 内容
- 把第 2 步与 Blocker 创建混在一起

### 2.6 写入历史滚动归档（F-04）

`state.md` 文件正文中的"写入历史"表是审计依据：

- 单文件历史条目数 > 50 时，由 Controller 滚动归档
- 归档路径：`workspace/<task-id>/archive/state-history-<from-seq>-to-<to-seq>.md`
- 归档时保留 frontmatter + 当前态字段，正文历史只保留最近 20 条 + 一行"早于 #N 的历史已归档至 archive/state-history-XXX.md"
- 归档动作本身**也写一行**到当前历史（actor=controller, intent=archive_history）

## 3. 示例 Frontmatter

### 3.1 初始状态

```yaml
---
task_id: T-2026-001
current_status: created
previous_status: created
current_agent: controller
next_agent: pm
allowed_next_statuses: [pm_processing]
human_review_status: not_required
final_review_status: not_required
produced_artifacts: []
active_blocker: null
blockers_history: []
blocked_context: null
updated_at: 2026-05-09T10:00:00+08:00
schema_version: a2a/v1
---
```

### 3.2 审核通过后（双步流转之间的中间态）

```yaml
---
task_id: T-2026-001
current_status: human_review_required          # 第一步只翻 status,current 还没推
previous_status: human_review_required
current_agent: human
next_agent: developer
allowed_next_statuses: [developer_processing, architect_processing]
human_review_status: approved                  # 第一步:翻 status
final_review_status: not_required
produced_artifacts: [A-T-2026-001-prd, A-T-2026-001-tech-plan, ...]
active_blocker: null
blockers_history: []
blocked_context: null
updated_at: 2026-05-09T14:00:00+08:00
schema_version: a2a/v1
---
```

第二步独立写入：

```yaml
current_status: developer_processing
previous_status: human_review_required
current_agent: developer
next_agent: qa
```

### 3.3 Blocked 状态

```yaml
---
task_id: T-2026-001
current_status: blocked
previous_status: developer_processing
current_agent: controller
next_agent: architect
allowed_next_statuses: [architect_processing]
human_review_status: approved
final_review_status: not_required
produced_artifacts: [...]
active_blocker: B-T-2026-001-001
blockers_history: [B-T-2026-001-001]
blocked_context:
  blocker_id: B-T-2026-001-001
  blocked_from_agent: developer
  blocked_from_status: developer_processing
  resume_to_agent: architect
  resume_to_status: developer_processing      # 局部修复（仅补 file-change-plan）后回开发态
  blocking_reason: file-change-plan 缺 src/services/settings.ts 但实现需要
  missing_artifacts: [file_change_plan]
  required_fix: 重新出 file-change-plan,补 src/services/settings.ts 条目
updated_at: 2026-05-09T15:30:00+08:00
schema_version: a2a/v1
---
```

## 4. 校验规则

- `current_status` 与 `allowed_next_statuses` 必须符合 state-machine.md 转移图
- `current_status == blocked` 时 `blocked_context` 必须非空且 11 字段完整
- `current_status != blocked` 时 `blocked_context` 应为 null
- `human_review_status == approved` 但 `current_status` 仍是 `human_review_required` 是合法中间态（双步流转之间）
- `current_status == developer_processing` 时 `human_review_status` 必须是 `approved`，否则写代码门禁不通过

## 5. 常见违规示例

### 反例 1：跳过双步流转

```yaml
# 错误!直接从 human_review_required 推到 developer_processing 但没翻 human_review_status
current_status: developer_processing
human_review_status: pending          # 不一致!
```

### 反例 2：current_status 含审核结果

```yaml
current_status: human_review_approved   # 错误!这个值不在 14 状态枚举中
```

### 反例 3：Agent 自己写 state.md

任何 PM / Architect / Dev / QA 写 state.md 都视为越权。Controller 应拒绝该写入并发 Blocker。

### 反例 4：blocked 但 blocked_context 为 null

```yaml
current_status: blocked
blocked_context: null    # 错误!必须填 11 字段
```

## 6. 下游使用方式

- 所有 Agent 启动前先 Read `state.md`
- Cursor 在每次回复的 `[A2A]` 头中输出 `Current Status` 与 `Human Review Status`
- Controller 推进前必须读 `state.md` 当前值，校验 `allowed_next_statuses` 含目标值
