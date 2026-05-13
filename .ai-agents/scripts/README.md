# A2A Agent Orchestrator

通过 `@cursor/sdk` 在终端自动编排 A2A 五个 Agent（PM → Architect → Developer → QA → Controller），按状态机自动连跑，遇到 Human Review / Blocker / 模糊需求时智能暂停。

## 前置

```bash
export CURSOR_API_KEY=cursor_你的_key
```

API Key 从 [cursor.com/dashboard/cloud-agents](https://cursor.com/dashboard/cloud-agents) 获取。

可选环境变量：

| 变量 | 说明 |
|---|---|
| `A2A_MODEL_ID` | 覆盖 SDK 自动选模型；默认通过 `Cursor.models.list()` 找 sonnet 4.6，找不到兜底 `claude-4.6-sonnet` |

## 三种使用方式

### 1. 全自动编排（推荐）

新建并启动 Task：

```bash
./start-task
# 进入交互式输入：task_type / 需求描述 / title / priority / owner
```

或一行启动：

```bash
./start-task --type feature --priority P2 --owner zhangxia "需求：为后台新增角色权限管理模块"
```

编排器会：
- 召唤 Controller 创建 Task（生成 `T-YYYY-NNN`、写 `state.md` / `task.md` / `active-task.md`）
- 按状态机自动连跑 PM → Architect → Developer → QA
- 在 `human_review_required` 和 `final_review_required` 暂停等你审核
- 在 Agent 触发"澄清问题"时暂停等你回答
- 在 `blocked` 时暂停等你裁决

### 2. 从中断处继续

```bash
./resume-task                  # 自动读 active-task.md 的 active_task_id
./resume-task T-2026-001       # 显式指定
```

### 3. 手动单步调用

```bash
./pm "分析需求：..."
./architect "为 XXX 出技术方案"
./developer "按 file-change-plan 实现 XXX"
./qa "对 XXX 做 7 维测试"
./controller "推进状态"
```

## 自动化流程图

```
./start-task "需求..."
       ↓
[编排器] 召唤 Controller 创建 Task
[编排器] state = pm_processing
[PM]      → 写 PM artifacts ←─────── 遇模糊点写 clarification-questions.md → 暂停
[编排器] state = pm_completed
[Ctrl]    → 推进到 architect_processing
[Arch]    → 写 Architect artifacts
[编排器] state = architect_completed
[Ctrl]    → 推进到 human_review_required
[编排器] ⏸ 暂停 — 终端问 verdict + 评论
                  → 自动写 architect-review.md
                  → 召唤 Controller 双步推进
[编排器] state = developer_processing
[Dev]     → 5 条门禁自检 → 写代码 + implementation-log + changed-files
[编排器] state = developer_completed
[Ctrl]    → 推进到 qa_processing
[QA]      → 写 test-report + acceptance-checklist
[编排器] state = qa_completed
[Ctrl]    → 推进到 final_review_required
[编排器] ⏸ 暂停 — 终端问最终 verdict
                  → 自动写 final-review.md
                  → 召唤 Controller 双步推进 + 写 final-delivery.md
[编排器] state = completed ✨
```

## 模糊需求澄清机制

每个 Agent 启动时都被注入硬约束：**遇到模糊需求严禁猜测**，必须写 `clarification-questions.md` 并退出。

编排器检测到该文件后会：

1. **方式 A（推荐）** — 提示你去 Cursor 聊天窗发：
   ```
   回答 architect 的澄清问题（任务 T-2026-XXX），逐条问我并把答案写回 clarification-questions.md
   ```
   AI 会逐条用 `AskQuestion` 问你 → 把答案写回文件
2. **方式 B** — 在终端直接逐条回答（用 `inquirer` 的 select / input）

回答完后编排器重新召唤对应 Agent 继续工作。

## Human Review 流程

```
[编排器] ⏸ 等待 Human Review（architect_review）

  待审产物：
    - A-T-2026-001-tech-plan
    - A-T-2026-001-file-change-plan
    - A-T-2026-001-risk-plan

? 请选择 verdict：
    > approved — 通过
      rejected — 拒绝
      needs_changes — 需修改
      暂不审核，退出（之后用 resume-task 继续）

? 评论 / notes：同意方案，按此执行
? reviewer：zhangxia

✓ 已写 .ai-agents/workspace/T-2026-001/human-reviews/architect-review.md
[Controller] 校验 review record 字段...
[Controller] 第 1 步：state.human_review_status = approved
[Controller] 第 2 步：state.current_status = developer_processing
✓ Controller 双步推进完毕
```

## 暂停与恢复

任何时候按 `Ctrl+C` 中断后：

```bash
./resume-task   # 从当前 state 继续
```

特殊情况：

- **state 进入 blocked**：编排器会显示 `active_blocker`，引导你查看 `blockers/B-*.md`，处理后召唤 Controller 校验恢复
- **state 处于双步中间态**（如 `human_review_required` + `human_review_status=approved`）：Controller 启动自检场景 0 会自动补做第 2 步

## 文件结构

```
.ai-agents/scripts/
├── start-task.ts           # 一键启动
├── resume-task.ts          # 从 state 继续
├── orchestrator.ts         # 主编排循环
├── run-agent.ts            # 单 Agent 执行器
├── start-task / resume-task / pm / architect / developer / qa / controller   # bash 快捷脚本
├── lib/
│   ├── paths.ts                  # 工作区路径常量
│   ├── state-reader.ts           # 解析 state.md
│   ├── next-agent-picker.ts      # state → 下一个 action
│   ├── clarification-detector.ts # 检测 + 写答澄清问题
│   ├── review-prompter.ts        # 终端 verdict 交互
│   ├── review-writer.ts          # 写 architect-review.md / final-review.md
│   ├── controller-invoker.ts     # 调 Controller 推进
│   ├── model-config.ts           # 模型 id 自动解析
│   └── terminal-ui.ts            # 彩色输出
└── package.json
```

## 设计要点

1. **Agent 间通过文件系统传递**，编排器不复制粘贴任何内容
2. **state.md 仅 Controller 可写**，编排器只写 review record 和 clarification 答案
3. **Human Review 双步流转禁止合并**，由 Controller 严格执行 §3.6 / §3.12
4. **遇模糊需求强制澄清**，所有 Agent prompt 头部都注入"严禁猜测"约束
5. **支持中断恢复**，state.md 是唯一动态状态源

## 故障排查

| 现象 | 可能原因 | 处理 |
|---|---|---|
| `CURSOR_API_KEY 未设置` | 没 export | `export CURSOR_API_KEY=cursor_xxx` |
| `models.list() 失败` | API Key 无效或网络问题 | 检查 key；编排器会兜底用 `claude-4.6-sonnet` |
| `state.current_status` 连续 3 轮不变 | Agent 卡住或未实际推进 | 编排器询问是否继续；如反复则人工排查 |
| `blocked` 状态恢复无效 | `state.blocked_context.missing_artifacts` 未补齐 | 按 blocker.md 逐条补齐再恢复 |
| review record 已存在但流程未推进 | 双步流转中间态 | 编排器会复用并召唤 Controller 场景 0 补做 |
