# Cursor Rules — Cursor 操作规则

> 规范 Cursor 在本系统中的操作。**完整可执行版本写在 `.cursor/rules/ai-agents.mdc`**（alwaysApply: true）。本文件是人类可读的同源规范。

## 1. 识别当前 Agent

Cursor 启动每次任务前必须 Read：

1. `.ai-agents/workspace/active-task.md` → 拿到 active_task_id
2. `.ai-agents/workspace/<task-id>/state.md` → 拿到 current_agent
3. `.ai-agents/agent-cards/<current_agent>.card.md` → 加载该 Agent 的能力与权限
4. `.ai-agents/agents/<current_agent>.agent.md` → 加载该 Agent 的工作流

## 2. 识别当前 Task（4 步严格优先级）

1. 用户 Prompt 中显式指定的 task_id（最高优先级，覆盖其他）
2. `.ai-agents/workspace/active-task.md` 中的 active_task_id
3. workspace 中只有一个 Task → 使用该 Task
4. 多个 Task 且无 active-task → **必须询问用户**，不允许猜测

不允许跳过任一步骤。

## 3. 读取 Artifact

按 `agent-cards/<current_agent>.card.md` 的 `input_artifacts` 列表逐个 Read：

- 每个 artifact 文件的 frontmatter `status` 必须是 `ready`
- 任一 status != ready → 拒绝启动 → 发 blocker-request

## 4. 是否允许写代码（5 条门禁）

Cursor 在执行任何 Write / StrReplace / Delete 前**必须**逐项自检：

1. `state.current_status == developer_processing` ✓
2. `state.human_review_status == approved` ✓
3. 当前 Agent role == `developer` ✓
4. 待修改路径在 `file-change-plan.md` 白名单中且 `operation` ∈ {create, modify, delete} 且 `allowed == yes` ✓
5. 待修改路径不属于默认禁改集（除非 file-change-plan 显式 allowed: yes 且 owner: user-approved） ✓

任一不满足 → **立即停止** → 在对话中明示原因 → 发 blocker-request。

## 5. 阻止跳过人工审核

- `state.current_status == human_review_required` 时 Cursor 不允许召唤 Dev Agent
- `state.current_status == final_review_required` 时 Cursor 不允许写 final-delivery
- 用户口头说"我同意" → Cursor 必须先**代写** `human-reviews/architect-review.md` 或 `final-review.md`，再让 Controller 校验 → 才能翻 *_status → 才能推 current_status
- 不允许任何"跳过审核直接进开发"的捷径

## 6. 每次回复以 [A2A] 头开始

每次 Cursor 回复必须以以下格式开头：

```
[A2A]
- Current Agent: <role>
- Current Task: <task_id>
- Current Status: <state.current_status>
- Human Review Status: <state.human_review_status>
- Reading Artifacts: [<artifact-id>, ...]
- Producing Artifacts: [<artifact-id>, ...]
- May Write Code: yes | no, 原因
```

例：

```
[A2A]
- Current Agent: developer
- Current Task: T-2026-001
- Current Status: developer_processing
- Human Review Status: approved
- Reading Artifacts: [A-T-2026-001-tech-plan, A-T-2026-001-file-change-plan]
- Producing Artifacts: [A-T-2026-001-implementation-log, A-T-2026-001-changed-files]
- May Write Code: yes, 5 条门禁全过
```

## 7. Blocker Request 规则

Cursor 代表任意 Agent（PM / Architect / Dev / QA）发现问题时：

- 不允许直接写 `blockers/B-*.md`
- 不允许写 `state.md`
- 必须写 `messages/from-<role>-<seq>-blocker-request.md`（按 message.schema.md，message_type: blocker，intent: blocker_request）
- 在对话中明示"已发 blocker-request，等待 Controller 创建正式 Blocker"

## 8. Human Review 规则

Cursor 在审核阶段：

- **不允许**自行翻 `state.human_review_status` / `state.final_review_status`
- 用户必须先给出明确 verdict（approved / rejected / needs_changes）
- Cursor 按用户指令**代写** `human-reviews/architect-review.md` 或 `final-review.md`（按 review.schema.md）
- 然后召唤 Controller 校验 review record → 双步翻状态

## 9. final-delivery 写入门禁

Cursor 在写 `artifacts/final/final-delivery.md` 前必须确认：

- `state.final_review_status == approved`
- `state.current_status == completed`
- `human-reviews/final-review.md` 存在且 verdict == approved
- 当前 Agent role == `controller`

任一不满足 → **拒绝写入** → 在对话中明示原因。

## 10. 多 Task 不猜测规则

- workspace 中存在多个 Task 且 active-task.md 缺失或为空 → Cursor **必须**通过对话询问用户
- 不允许"猜测最近的 Task" / "猜测最新创建的 Task"
- 不允许在多 Task 之间隐式切换

## 11. State 读取规则

- 每次 Cursor 操作前**必须**重新 Read `state.md`（不能依赖上次缓存的状态）
- state.md 与 task.md 字段冲突时，以 state.md 为准（task.md 仅静态元信息）
- state.md 缺失 → 拒绝任何写操作 → 在对话中明示

## 12. Agent Card 加载规则

- 加载 `agent-cards/<current_agent>.card.md` 后严格按 `writable_paths` 校验
- 写入路径不在 writable_paths → 拒绝写入 → 发 blocker-request

## 13. 复用 vs 新建文件

- 优先复用现有 component / hook / util / type / service
- 新建文件必须**预先**在 file-change-plan 中（operation: create + allowed: yes）
- 实施过程中发现需要新建白名单外的文件 → 发 blocker-request

## 14. Agent Model Selection（手动 Override）

每个子 Agent 的模型默认由 `a2a_runtime/services/model_selection_service.py` 的 `DEFAULT_MODEL_PREFERENCES` 推荐，但用户可以通过 markdown 文档手动选择，不需要改 Python 代码。

### 解析优先级（高 → 低）

1. **CLI 一次性**：`a2a-agent prompt <role> --model <slug>`、`a2a-agent model recommend --agent <role> --model <slug>`
2. **md 文档勾选**：`.ai-agents/agent-cards/model-overrides.md` 中 `## <role>` section 下勾 `- [x] <slug>`
3. **per-card frontmatter**：`agent-cards/<role>.card.md` 的 `model:` 字段
4. **Runtime 默认**：`DEFAULT_MODEL_PREFERENCES`

### model-overrides.md 主要 UX

```markdown
## pm

- [ ] gpt-5.5
- [x] claude-4.6-sonnet-medium-thinking  -- 我的常用
- [ ] claude-opus-4-7-thinking-high
```

- `## <role>` 用 6 个 role enum：`pm` / `architect` / `developer` / `qa` / `controller` / `risk`
- 每个 section 最多勾 1 个；多勾 → 取第一个并发 warning
- 不勾 = 走默认；清单外 slug 直接加一行 `- [x] your-slug`，runtime 不校验

### 高风险升档（不可关闭）

- P0/P1 任务强制升档到高推理模型（cursor → `claude-opus-4-7-thinking-high`，codex → `gpt-5.5`）
- 你的 override 在升档时会被覆盖，`Recommended Model.Warnings` 会明示

### 不变安全边界

- Runtime 仅生成 prompt 段落，**不自动**切换 Cursor 模型 / 执行 Codex
- 用户始终需要在 Cursor 模型选择器手动选，或手动 `codex --model <slug>`
- model-overrides.md 在 `.ai-agents/agent-cards/` 下，**仅用户可改**，不在任何 Agent 写权限白名单内
