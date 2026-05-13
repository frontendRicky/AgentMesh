# File Message Bus

> 基于本地文件的"消息总线"：所有 Agent 通过约定的文件路径与命名规则交接。

## 1. Workspace 结构

```
.ai-agents/workspace/
  active-task.md                 当前活动 Task 标记(仅 Controller 写)
  <task-id>/                     单个 Task 工作目录
    task.md                      静态元信息(仅创建时写一次)
    state.md                     动态状态源(仅 Controller 写)
    messages/                    所有 Agent 间通信
      from-<role>-<seq>-<intent>.md
    artifacts/                   按 role 分子目录,每个 role 只能写自己的
      pm/        artifacts/pm/<artifact-type>.md
      architect/ artifacts/architect/<artifact-type>.md
      developer/ artifacts/developer/<artifact-type>.md
      qa/        artifacts/qa/<artifact-type>.md
      final/     artifacts/final/final-delivery.md(仅 Controller 写)
    human-reviews/               人工审核留痕(仅 Human Review Actor 写)
      architect-review.md
      final-review.md
    blockers/                    正式 Blocker 文件(仅 Controller 写)
      B-<task-id>-<seq>.md
    archive/                     被 superseded 的 artifact 副本归档
```

## 2. 文件命名约定

### 2.1 Task ID 与目录名（F-01 强约束）

格式：`T-YYYY-NNN`，例如 `T-2026-001`。

- `YYYY`：4 位年份
- `NNN`：3 位序号，从 001 开始
- 必须匹配正则 `^T-\d{4}-\d{3}$`（task.schema.md 强制）
- **目录名 必须 与 task_id 严格一致**：例如 task_id `T-2026-002` → 目录 `workspace/T-2026-002/`
- **禁止**使用 `example-task` / `demo-task` / `test-task` 作为运行目录名（仅 `examples/` 下作为示例归档可保留）
- **禁止**使用 `T-2026-EXAMPLE` / `T-YYYY-XXX` 等不符合正则的 task_id

### 2.2 Message 文件名

格式：`messages/from-<role>-<seq>-<intent>.md`

- `<role>`：**严格 5 选 1** → `pm` / `architect` / `developer` / `qa` / `controller`
  - **禁止** 使用 `dev` 作为 `<role>`（必须 `developer`）
  - **禁止** 使用 `from-dev-*.md` 文件名（必须 `from-developer-*.md`）
- `<seq>`：3 位序号，全 Task 范围内递增（001, 002, ...）
- `<intent>`：短 kebab-case 描述（如 handoff、blocker-request、gate-failure、status、ready-for-review）

示例（**全部使用 developer**）：
- `messages/from-controller-001-handoff.md`
- `messages/from-pm-002-handoff.md`
- `messages/from-architect-003-handoff.md`
- `messages/from-controller-004-handoff.md`
- `messages/from-developer-005-handoff.md`
- `messages/from-qa-006-handoff.md`
- `messages/from-developer-007-blocker-request.md`     # 流程阻塞,需要正式 Blocker
- `messages/from-developer-008-gate-failure-request.md` # 门禁失败,**不**创建 Blocker、**不**改 state
- `messages/from-controller-009-blocker.md`

### 2.3 Artifact 文件名

格式：`artifacts/<role>/<artifact-type>.md`

每个 Task 同一 type 默认只有 1 个版本；如需 v2，将 v1 移到 `archive/<artifact-type>.v1.md`，再写新版本。

示例：
- `artifacts/pm/requirement.md`
- `artifacts/pm/prd.md`
- `artifacts/pm/task-breakdown.md`
- `artifacts/pm/bug-brief.md`（bugfix-flow）
- `artifacts/pm/regression-scope.md`（bugfix-flow）
- `artifacts/architect/tech-plan.md`
- `artifacts/architect/file-change-plan.md`
- `artifacts/architect/risk-plan.md`
- `artifacts/developer/implementation-log.md`
- `artifacts/developer/changed-files.md`
- `artifacts/qa/test-report.md`
- `artifacts/qa/acceptance-checklist.md`
- `artifacts/qa/qa-file-change-plan.md`（如需新增测试文件）
- `artifacts/final/final-delivery.md`（仅 Controller 在 final_review_status==approved 后写）

### 2.4 Blocker 文件名

格式：`blockers/B-<task-id>-<seq>.md`

- 仅 Flow Controller 创建
- `<seq>`：3 位序号，全 Task 范围内递增

示例：`blockers/B-T-2026-001-001.md`

### 2.5 Human Review Record 文件名

固定两个文件名：

- `human-reviews/architect-review.md`（架构审核）
- `human-reviews/final-review.md`（最终验收）

仅 Human Review Actor 创建。

## 3. 读写约定

### 3.1 Agent 启动前必读

每个 Agent 在执行任何动作前，按以下顺序读：

1. `.cursor/rules/ai-agents.mdc`（行为约束）
2. `.ai-agents/workspace/active-task.md`（识别当前 Task）
3. `.ai-agents/workspace/<task-id>/task.md`（静态元信息）
4. `.ai-agents/workspace/<task-id>/state.md`（动态状态）
5. `.ai-agents/agent-cards/<current_agent>.card.md`（自身权限）
6. `.ai-agents/agents/<current_agent>.agent.md`（自身行为）
7. `.ai-agents/handoffs/<from-to>.md`（自身 Handoff Contract）
8. 上游 artifacts 与 messages（按 Card 的 input_artifacts）

### 3.2 Agent 写入约定

- **每次写入前**：先 Read 自身 Card 的 writable_paths，自检目标路径在白名单内
- **写入 frontmatter**：必含 `task_id` / `schema_version: a2a/v1` / `created_at`，按文件类型补对应主键（artifact_id / message_id / blocker_id / review_id / contract_id）
- **写入完成后**：在对话中报告写了哪些文件，让用户与 Controller 可校验

### 3.3 Controller 推进约定

Controller 推进 state 前必须：

1. 读 `state.md` 当前状态
2. 读对应 Handoff Contract
3. 校验上游 Artifact / Message / Review Record 是否齐全
4. 通过：写 state.md → 写 from-controller-*-handoff Message → 召唤下游
5. 不通过：进入 Blocker 创建流程（见 `blocker.schema.md`）

## 4. 并发与冲突

当前为单 active-task 模式：

- `workspace/active-task.md` 一次只指向一个 Task
- 多 Task 并存时，Cursor 必须按 4 步优先级识别（详见 `cursor-rules.md`）
- 切换 active-task 必须由 Controller 显式更新 `active-task.md`

## 5. 反例（禁止）

- 把 message 文件命名为 `artifacts/pm/handoff.md`（应是 `messages/from-pm-*-handoff.md`）
- 把 review record 写到 `artifacts/<role>/`（应是 `human-reviews/`）
- Agent 直接写 `blockers/**` 或 `state.md`（仅 Controller）
- Controller 写 `human-reviews/*.md`（仅 Human Review Actor）
- 跨 Task 共用 message_id / artifact_id / blocker_id（每个 ID 必须含 task_id 前缀）
- 目录名与 task_id 不一致（如 task_id `T-2026-002` 对应目录 `workspace/example-task/`）— 见 §2.1
- 使用 `dev` 作为 `<role>` 或在文件名中使用 `from-dev-*.md` — 见 §2.2
- 把 gate_failure 当成 blocker（用 `message_type: blocker` + `intent: blocker_request`），导致 Controller 误创建正式 Blocker — 见 `message.schema.md §2.1`
