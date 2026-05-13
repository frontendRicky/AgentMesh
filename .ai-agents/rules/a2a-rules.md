# A2A Rules — 16 条硬约束

> 本系统的"宪法"。任何 Agent / Controller / Cursor 行为必须满足以下 16 条；违反任一条即视为系统级违规。

## R-A2A-1：没有 Task 不允许启动 Agent

任何专业 Agent（PM / Architect / Developer / QA）启动前，`workspace/<task-id>/task.md` 与 `state.md` 必须存在且 schema 校验通过。

- 违规示例：用户对话"PM 你写一份 PRD" → Cursor 直接写 `prd.md` 而未先创建 task / state
- 正确做法：Cursor 先召唤 Controller 创建 task / state / active-task，再让 PM 启动

### R-A2A-1.1：task_id 与目录名严格一致（F-01）

- task_id 必须匹配 `^T-\d{4}-\d{3}$`（详 task.schema.md）
- 目录名必须严格 == task_id（如 task_id `T-2026-002` → 目录 `workspace/T-2026-002/`）
- **禁止** 使用 `example-task` / `demo-task` / `test-task` 作为运行目录名
- **禁止** 使用 `T-2026-EXAMPLE` / `T-YYYY-XXX` 等不符合正则的 task_id
- 仅 `examples/` 下作为示例归档可保留任意命名（如 `examples/feature-add-settings-page/T-2026-001/`）

### R-A2A-1.2：task_id 正则 Cursor 启动时强制校验（F-03）

Cursor 启动每个 Task 前必须自检：

```
读 active_task_id →
  if not match ^T-\d{4}-\d{3}$:
      在对话中明示"task_id 违反 schema",拒绝继续,要求 Controller 重建 task
```

也适用于读 task.md frontmatter 时的 task_id 字段。

## R-A2A-2：没有上游 Artifact 不允许下游执行

下游 Agent 启动前，必须 Read 上游 Card 中声明的 input_artifacts，且每个 artifact 的 `status == ready`。

- 违规示例：Architect 在 PRD 还是 draft 时启动
- 正确做法：Architect 启动前自检 PRD.status == ready，否则发 blocker-request

## R-A2A-3：没有 Handoff Message 不允许流转

每次 state 推进必须有对应的 `from-controller-<seq>-handoff.md` 或上游 Agent 的 handoff message。

## R-A2A-4：写代码双门禁（最重要）

Senior FE Developer Agent 写源码必须**同时**满足：

- `state.current_status == developer_processing`
- `state.human_review_status == approved`
- 当前 Agent role == `developer`
- 目标路径在 `file-change-plan.md` 白名单中且 `operation` ∈ {create, modify, delete} 且 `allowed == yes`
- 目标路径不属于默认禁改集（package.json / lock / .github/** / .gitlab-ci.yml / Dockerfile / CI 配置），除非 file-change-plan 显式 `allowed: yes` 且 `owner: user-approved`

**任一不满足 → 立即停止 → 按以下分类处理**：

| 失败条件类型 | 报告方式 |
|---|---|
| 条件 4 失败（路径不在白名单或 operation 不匹配） — **真实流程阻塞** | 发 `from-developer-<seq>-blocker-request.md`（`message_type: blocker`，`intent: blocker_request`），Controller 创建正式 Blocker、改 state 为 blocked |
| 条件 1 / 2 / 3 失败（state 处于错误阶段、Agent 误启动） — **门禁失败留痕** | 发 `from-developer-<seq>-gate-failure-request.md`（`message_type: gate_failure`，`intent: write_gate_failed`），Controller **不**创建 Blocker、**不**改 state |
| 条件 5 失败（默认禁改集，缺 user-approved） | 发 `from-developer-<seq>-blocker-request.md`，proposed_resume_to_agent: architect / user |

## R-A2A-5：Agent 只能发 Blocker Request；正式 Blocker 唯一由 Controller 写

PM / Architect / Developer / QA 发现问题时只能创建 `messages/from-<role>-<seq>-blocker-request.md`（`message_type: blocker`，`intent: blocker_request`）。

正式 `blockers/B-<task-id>-<seq>.md` 的创建权限**只属于 Flow Controller**，且必须：
- 读取触发它的 blocker request message，或
- 记录 Controller 自校验失败原因

`state.current_status = blocked` / `state.blocked_context` / `state.active_blocker` / `state.blockers_history` 也只能由 Controller 写。

### R-A2A-5.1：gate_failure 不触发正式 Blocker（F-05）

`message_type: gate_failure`（`intent: write_gate_failed`）专用于"Agent 在错误状态下被误启动"场景：

- Controller 收到 gate_failure → **不**创建 `blockers/B-*.md`、**不**写 `state.current_status = blocked`、**不**改 state 任何字段
- Controller 仅在对话中提示用户原因（如"先完成 Architect Review"）
- 误把 `gate_failure` 写成 `message_type: blocker` + `intent: blocker_request` → 视为 R-A2A-5.1 违规，须改用正确 message_type

详 `message.schema.md §2.1`、`blocker.schema.md §6`。

## R-A2A-6：下游 Agent 必须先校验上游 Artifact

下游启动前先按 Handoff Contract 的 acceptance_criteria 逐项校验。任一未通过 → 发 blocker-request。

## R-A2A-7：每个 Agent 只能写自己允许的 workspace 路径

按对应 `agent-cards/<role>.card.md` 的 `writable_paths` 严格执行。写错位 → 拒绝执行 → 发 blocker-request。

## R-A2A-8：业务代码只能由 Senior FE Developer 修改

PM / Architect / QA / Controller 都禁止写业务源码（含新建空文件、重命名、移动）。QA 仅在 qa-file-change-plan 授权下可写测试文件（不算业务源码）。

## R-A2A-9：QA 默认源码只读，写测试文件须 qa-file-change-plan 授权

QA 不能擅自创建任何项目源码文件（含 `*.test.*` / `*.spec.*` / `__tests__/` 等）；如需新增，先写 `artifacts/qa/qa-file-change-plan.md`，owner 字段为 `qa` 或 `developer+qa-approved`，提交用户批准后再创建。

## R-A2A-10：Architect 严禁任何源码 Write/StrReplace/Delete/Create

含新建空文件、重命名、移动。Architect 仅可 Read 源码以理解上下文。

## R-A2A-11：Controller 不能写 `artifacts/{pm,architect,developer,qa}/**`

Controller 仅可在 `state.final_review_status == approved` AND `state.current_status == completed` 后写 `artifacts/final/final-delivery.md`，且只引用上游 artifact 不修改。

## R-A2A-12：任何审核结果必须由 Controller 校验 review record 后才能从 pending 翻转

`state.human_review_status` / `state.final_review_status` 不能凭空翻为 approved / rejected；必须先存在对应的 `human-reviews/architect-review.md` 或 `human-reviews/final-review.md` 且字段完整。

## R-A2A-13：Human Review Record 仅由 Human Review Actor 创建

Controller 与所有专业 Agent 都不能创建、修改、伪造 `human-reviews/*.md`。Human Review Actor = 用户给 verdict 后由 Cursor 按用户指令代写。

## R-A2A-14：task.md 创建后不得变更

task.md 仅静态元信息，创建时一次性写定。运行时状态全部落 `state.md`，且仅 Controller 可写。

## R-A2A-15：正式 Blocker 仅 Controller 创建，且必须读取触发它的 Request Message 或自校验失败原因

`blockers/B-*.md` 的 frontmatter 必含 `created_by: controller` 与 `source_request_message`（指向 Request Message ID 或 null 表示 Controller 自校验失败）。

## R-A2A-16：Cursor 识别 Task 按 4 步严格优先级，多 Task 必询问

Cursor 在每次操作前按以下顺序识别当前 Task：

1. 用户 Prompt 中显式指定的 task_id
2. `.ai-agents/workspace/active-task.md` 中的 active_task_id
3. workspace 中只有一个 Task → 使用该 Task
4. 多个 Task 且无 active-task → **必须询问用户**，不允许猜测

## 17（补充）：审核翻转必须双步

- `human_review_required → developer_processing`：必须先翻 `human_review_status: pending → approved`，再独立推 `current_status`
- `final_review_required → completed`：必须先翻 `final_review_status: pending → approved`，再独立推 `current_status`

把双步合并视为 R-A2A-4 / R-A2A-12 的衍生违规。

## 18（补充）：双步流转中间态恢复（F-08）

当 Controller 启动时检测到以下中间态，**必须自动补做第 2 步**而不要重做第 1 步、不要走 Blocker 流程：

| 中间态 | 应补做的第 2 步 |
|---|---|
| `current_status == human_review_required` AND `human_review_status == approved` | `current_status = developer_processing`，`current_agent = developer`，`next_agent = qa`，写 `from-controller-<seq>-recover-handoff.md` |
| `current_status == final_review_required` AND `final_review_status == approved` | `current_status = completed`，`current_agent = controller`，`next_agent = none`，走场景 F 写 final-delivery |

补做第 2 步前必须**重新校验** review record（仍 verdict=approved 且字段完整）。详 state.schema.md §2.5、flow-controller.agent.md §11。

## 19（补充）：state.md 写入历史滚动归档（F-04）

当 state.md 正文中"写入历史"表条目数 > 50 时，由 Controller 滚动归档至 `archive/state-history-<from-seq>-to-<to-seq>.md`，state.md 仅保留最近 20 条 + 一行归档指引。归档动作本身也写一行进当前历史（actor=controller, intent=archive_history）。

## 20（补充）：试运行模式下 not_executed 是预期（F-07）

当 `task_type == dry_run`（或 task.md 的 constraints 含 `dry-run: true`）时，QA 用例大量出现 `not_executed`/`manual_required` 是预期，不视为覆盖率不足；但仍**禁止**把 `not_executed` 标成 `pass`。详 test-rules.md §试运行特例。

---

## 违规处理

任何 Agent 发现自己即将违反上述任一条 → 立即停止 → 发对应 blocker-request → 等待 Controller 处理。

任何 Agent 发现其他 Agent / Controller / Cursor 已经违反 → 在对话中明示，并要求回滚相关写入。
