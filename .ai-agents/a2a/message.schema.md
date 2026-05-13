# Message Schema

> Agent 之间通信的最小单元。文件路径 `messages/from-<role>-<seq>-<intent>.md`。

## 1. 字段定义

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `message_id` | string | 是 | 全局唯一，格式 `M-<task_id>-<seq>` |
| `task_id` | string | 是 | 所属 Task |
| `from_agent` | enum | 是 | `pm` / `architect` / `developer` / `qa` / `controller` / `human` |
| `to_agent` | enum | 是 | 同上 |
| `message_type` | enum | 是 | `request` / `response` / `handoff` / `review` / `blocker` / `gate_failure` / `status` / `final` |
| `intent` | string | 是 | 短 kebab-case，如 `pm_to_architect_handoff`、`blocker_request` |
| `summary` | string | 是 | 1-2 句话 |
| `payload` | object | 是 | 结构化主体；空 payload 拒收 |
| `referenced_artifacts` | string[] | 否 | 引用的 artifact_id 列表 |
| `required_response` | bool | 是 | 是否需要下游回应 |
| `blockers` | string[] | 否 | 触发的 blocker_id 列表 |
| `created_at` | ISO8601 | 是 | 创建时间 |
| `schema_version` | string | 是 | 固定 `a2a/v1` |

## 2. message_type 枚举

| message_type | 用途 | 典型 from → to |
|---|---|---|
| `request` | 请求下游执行 | controller → pm/architect/developer/qa |
| `response` | 回应上游 request | pm/architect/developer/qa → controller |
| `handoff` | 阶段交接 | pm → architect / architect → controller / developer → qa / qa → controller |
| `review` | 审核相关通知 | controller → human |
| `blocker` | Blocker Request（intent: blocker_request）或 Blocker 通知（controller → role） | `<role>` → controller / controller → `<role>` |
| `gate_failure` | **门禁失败说明**（**不**触发正式 Blocker，**不**改 state） | `<role>` → controller |
| `status` | 状态变化广播 | controller → all |
| `final` | 最终交付通知 | controller → user |

### 2.1 `blocker` vs `gate_failure` — 严格区分

| 维度 | `message_type: blocker` (intent: blocker_request) | `message_type: gate_failure` (intent: write_gate_failed) |
|---|---|---|
| 触发 | 上游缺漏 / 缺少 artifact / file-change-plan 缺路径 / 自身条件不满足 | Agent 在错误状态下尝试写代码（5 条门禁未达） |
| 是否需要修复 | **是**（必须由 resume_to_agent 修复） | **否**（state 已合规处于审核中，等待审核完成即可） |
| Controller 是否创建正式 Blocker | **是**（创建 `blockers/B-*.md`，写 `state.current_status = blocked` + `blocked_context`） | **否**（**禁止**创建 Blocker，**禁止**改 state） |
| 是否改 state.current_status | 是（blocked） | 否（保持原状态，本质是 Agent 误启动） |
| 用途 | 真实流程阻塞 | 自检失败留痕 + 在对话中提示用户"先完成审核 / 等待 state 推进到对应阶段" |
| 必填字段 | proposed_resume_to_agent / proposed_resume_to_status / proposed_missing_artifacts / proposed_required_fix | five_gate_conditions（5 条门禁逐项 pass/fail）/ attempted_action / state_at_attempt / decision: refuse_to_write |

## 3. 示例 Frontmatter

### 3.1 Handoff Message（PM → Architect）

```yaml
---
message_id: M-T-2026-001-002
task_id: T-2026-001
from_agent: pm
to_agent: architect
message_type: handoff
intent: pm_to_architect_handoff
summary: PRD/任务拆解已完成,主要待确认点为主题切换是否需要跟随系统
payload:
  prd_artifact_id: A-T-2026-001-prd
  task_breakdown_artifact_id: A-T-2026-001-task-breakdown
  open_questions:
    - 主题切换是否需要跟随系统?
    - 用户偏好是否要同步到后端?
  architect_must_answer:
    - 状态管理放页面级还是全局?
    - localStorage key 命名约定?
referenced_artifacts:
  - A-T-2026-001-requirement
  - A-T-2026-001-prd
  - A-T-2026-001-task-breakdown
required_response: true
blockers: []
created_at: 2026-05-09T11:00:00+08:00
schema_version: a2a/v1
---
```

### 3.2 Blocker Request Message（Developer 触发，需要正式 Blocker）

```yaml
---
message_id: M-T-2026-001-007
task_id: T-2026-001
from_agent: developer
to_agent: controller
message_type: blocker
intent: blocker_request
summary: file-change-plan 缺 src/services/settings.ts 条目,无法创建 service
payload:
  proposed_blocked_from_agent: developer
  proposed_blocked_from_status: developer_processing
  proposed_resume_to_agent: architect
  proposed_resume_to_status: developer_processing      # 局部修复后回开发态(详见 blocker.schema.md §6 resume_to_status 语义)
  proposed_blocking_reason: file-change-plan 未列出 src/services/settings.ts
  proposed_missing_artifacts: [file_change_plan]
  proposed_required_fix: 重新出 file-change-plan,补 src/services/settings.ts 条目
referenced_artifacts:
  - A-T-2026-001-file-change-plan
required_response: true
blockers: []
created_at: 2026-05-09T15:00:00+08:00
schema_version: a2a/v1
---
```

### 3.2b Gate Failure Message（Developer 在错误状态下尝试写代码，**不**需要正式 Blocker）

```yaml
---
message_id: M-T-2026-002-002
task_id: T-2026-002
from_agent: developer
to_agent: controller
message_type: gate_failure
intent: write_gate_failed
summary: Developer 在 current_status==human_review_required 时尝试写源码，5 条门禁条件 1+2+3 失败,立即停止
payload:
  attempted_action:
    operation: Write
    target_path: src/services/settings.ts
    tool: Write
  state_at_attempt:
    current_status: human_review_required
    human_review_status: pending
    final_review_status: not_required
    current_agent: human
  five_gate_conditions:
    cond_1_current_status_developer_processing: { expected: developer_processing, actual: human_review_required, pass: false }
    cond_2_human_review_status_approved:        { expected: approved,             actual: pending,                pass: false }
    cond_3_agent_role_developer:                { expected: developer,            actual: human,                  pass: false }
    cond_4_path_in_file_change_plan:            { expected: yes, actual: yes, pass: true }
    cond_5_not_in_default_forbidden:            { expected: yes, actual: yes, pass: true }
  decision: refuse_to_write
  controller_action_required: none      # 本质是合规等待,无需 Controller 创建 Blocker / 改 state
  reason_for_user: |
    Developer 误启动；写代码门禁未达；请先完成 Architect Review,
    Cursor 不会创建正式 Blocker,也不会改 state.
referenced_artifacts: []
required_response: false
blockers: []
created_at: 2026-05-11T16:00:00+08:00
schema_version: a2a/v1
---
```

### 3.3 Controller Handoff（推进到下游）

```yaml
---
message_id: M-T-2026-001-004
task_id: T-2026-001
from_agent: controller
to_agent: developer
message_type: handoff
intent: human_review_to_developer_handoff
summary: architect-review.md verdict=approved,state 已推进到 developer_processing
payload:
  human_review_record: human-reviews/architect-review.md
  state_snapshot:
    current_status: developer_processing
    human_review_status: approved
  expected_artifacts:
    - implementation_log
    - changed_files
referenced_artifacts:
  - A-T-2026-001-tech-plan
  - A-T-2026-001-file-change-plan
  - A-T-2026-001-risk-plan
required_response: true
blockers: []
created_at: 2026-05-09T14:05:00+08:00
schema_version: a2a/v1
---
```

## 4. 校验规则

- `message_id` 必须符合 `^M-T-\d{4}-\d{3}-\d{3}$`
- `payload` 必须非空（空 payload 视为形式主义，Controller 拒收）
- `from_agent` 必须与文件名中的 `<role>` 一致
- `intent` 应使用 kebab-case 或 snake_case，避免长描述
- `referenced_artifacts` 中的 artifact_id 必须真实存在

## 5. 常见违规示例

### 反例 1：把 handoff message 当 artifact

```yaml
# messages/from-pm-002-handoff.md 的 frontmatter
artifact_id: A-T-2026-001-handoff   # 错误!这是 message,不是 artifact
```

### 反例 2：payload 空

```yaml
payload: ""   # 错误!Controller 拒收
payload: {}   # 错误!至少要有 1 个有意义字段
```

### 反例 3：from_agent 与文件名不一致

```
文件名: messages/from-pm-002-handoff.md
但 frontmatter: from_agent: architect   # 错误!不一致
```

### 反例 4：Agent 直接写 message_type: blocker 但意图是创建正式 Blocker

```yaml
from_agent: developer
to_agent: developer
message_type: blocker
intent: blocker_creation              # 错误!Agent 只能发 blocker_request,不能自创建 Blocker
```

### 反例 5：把 gate_failure 当 blocker_request 发，导致 Controller 误创建正式 Blocker

```yaml
from_agent: developer
to_agent: controller
message_type: blocker                 # 错误!此时 5 条门禁未达,本质是 Agent 误启动,不是真实流程阻塞
intent: blocker_request               # 应改为 message_type: gate_failure, intent: write_gate_failed
```

正确做法：用 `message_type: gate_failure` + `intent: write_gate_failed`，Controller 不创建 Blocker、不改 state，仅在对话中提示用户原因。

## 6. 下游使用方式

- Controller 监听所有 `from-<role>-*-handoff` 与 `from-<role>-*-blocker-request` 与 `from-<role>-*-gate-failure-*`
- 按 message_type 路由到不同处理逻辑：
  - `handoff` → 走 Handoff Contract 校验 → 推 state
  - `blocker` (intent: blocker_request) → 走两阶段 Blocker 创建（场景 D）
  - `gate_failure` (intent: write_gate_failed) → **不**创建 Blocker、**不**改 state，仅在对话中向用户说明门禁未达的原因
  - `status` / `final` → 留痕 + 在对话中通知
- referenced_artifacts 用于校验上游产物完整性
- required_response: true 时，Controller 必须在合理时间内回写一条 response 或 status message
