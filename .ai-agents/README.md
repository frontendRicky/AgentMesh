# .ai-agents — 本地 File-based A2A AI Agents 工作流系统

> 4 核心 Agent + 1 Flow Controller + 8 套 A2A Schema + 6 条 Flow + 7 套 Rule + 16 套 Template + Cursor 集成。
> 通过本地文件交接，无 HTTP，无 server，零运行时依赖。

---

## 1. 系统组成

- **4 核心 Agent**
  - Product Manager Agent（产品经理）
  - Architect Agent（架构师）
  - Senior Frontend Developer Agent（高级前端开发）
  - QA Tester Agent（测试）
- **1 Flow Controller Agent**：仅调度、校验、状态流转
- **1 Human Review Actor**：用户给出 verdict 后由 Cursor 按指令代写 review record

---

## 2. 关键约束（必须先记住）

1. **task.md 与 state.md 严格分离**
   - `task.md` 仅静态元信息，创建后不再变更
   - `state.md` 是唯一动态状态源，**只能由 Flow Controller 写**
2. **写代码双门禁**
   - `state.current_status == developer_processing` AND
   - `state.human_review_status == approved`
   - 同时满足才能让 Senior FE Dev 写源码
3. **Blocker 两阶段**
   - PM / Architect / Dev / QA 只能写 `messages/from-<role>-*-blocker-request.md`
   - 正式 `blockers/B-*.md` 与 `state.md` 唯一由 Controller 写
4. **Human Review 双角色**
   - `human-reviews/*.md` 仅由 Human Review Actor 创建
   - Controller 只读取并校验，禁止伪造、修改
5. **审核翻转双步**
   - 第一步：Controller 翻 `state.human_review_status` 或 `state.final_review_status`
   - 第二步：Controller 独立推 `state.current_status`
6. **路径写权限隔离**
   - 每个 Agent 只能写自己的 `artifacts/<role>/` 与 `messages/from-<role>-*.md`
   - 业务源码只能由 Senior FE Dev 修改，且必须命中 `file-change-plan.md` 白名单

---

## 3. 目录索引

```
.ai-agents/
  README.md                  本文件
  CHANGELOG.md               协议版本变更
  a2a/                       8 套 Schema + 协议总章 + State Machine + File Bus
  agents/                    5 份 Agent 行为定义（人类可读）
  agent-cards/               5 份机器可读 Agent Card + model-overrides.md（手动模型切换）
  handoffs/                  6 份 Handoff Contract
  flows/                     6 条 Flow（feature/refactor/bugfix/ui-redesign/permission/api-integration）
  rules/                     7 份规则
  templates/                 16 份可复制模板
  workspace/                 实际 Task 工作目录
    active-task.md           当前活动 Task 标记
    T-YYYY-NNN/              实际 Task 目录(目录名 == task_id,F-01 强制)
  examples/                  完整跑通的样例 Task(参考;含 feature-add-settings-page/T-2026-001/ 归档)
```

---

## 4. 快速开始

### 启动一个 A2A Task（最常见用法）

把以下 Prompt 贴给 Cursor：

```
[A2A] 启动新 Task
task_type: feature
title: <一句话需求>
priority: P1
human_owner: <你的 handle>
原始需求:
<把需求贴这里>

请 Flow Controller:
1. 在 .ai-agents/workspace/T-YYYY-NNN/ 下创建 task.md(仅静态元信息) 与 state.md(current_status: created)
2. 把 active_task_id 写入 .ai-agents/workspace/active-task.md
3. 生成 from-controller-001-handoff Message 召唤 PM Agent
不允许写源码。
```

后续 Cursor 会按 Flow 推进，每次回复都以 `[A2A]` 头开始。

### 进入开发阶段

参见 [.ai-agents/agents/senior-frontend-developer.agent.md](agents/senior-frontend-developer.agent.md) 与 [.ai-agents/rules/code-change-rules.md](rules/code-change-rules.md)。

### 处理 Blocker

参见 [.ai-agents/a2a/blocker.schema.md](a2a/blocker.schema.md)。

---

## 5. 设计原则

- **不绑定技术栈**：所有 Rule 与 Template 都是前端通用级，不写具体 React/Vue 语法
- **不可跳步**：PRD → Tech Plan → Human Review → Code → QA → Final Review
- **可审计**：所有产物含 `task_id` / `created_at` / `schema_version` / `produced_by`
- **轻量模式**：仅允许缩短模板，不允许合并 Agent 职责，不裁审核

---

## 6. 模型选择（Per-Agent Model Override）

各 Agent 默认模型见 `a2a_runtime/services/model_selection_service.py` 中的 `DEFAULT_MODEL_PREFERENCES`。手动切换走 4 级优先级（高 → 低）：

1. CLI `--model <slug>`（一次性）
2. [agent-cards/model-overrides.md](agent-cards/model-overrides.md) 的 body checklist `- [x] <slug>`，未勾选则 fallback frontmatter `overrides:` 映射
3. 各 `agent-cards/<role>.card.md` frontmatter 的可选 `model: <slug>` 字段
4. 默认偏好

不变项：

- A2A schema 与冻结声明全部不变
- P0/P1 高风险强制升级到 high-reasoning 模型，**不可被 override 绕过**
- Codex tool context 仍拒绝非 codex-compatible slug
- Runtime 仍不调用 LLM、不切换 Cursor 模型、不执行 Codex

详 [.cursor/rules/ai-agents.mdc](../.cursor/rules/ai-agents.mdc) §16、[rules/cursor-rules.md](rules/cursor-rules.md) §14。

---

## 7. 协议版本

当前：`a2a/v1`，**版本号 `v1.0.0`，已于 2026-05-11 冻结**。

### v1.0.0 冻结声明

当前 Markdown File-based A2A Protocol 已冻结为 v1.0.0。
后续 Python Agents Runtime 必须以该协议为实现基准。
Python Runtime 在 V1 阶段只能读取和执行协议，不允许修改协议结构。

任何破坏性协议改动必须升级为 v2；v1 Task 不强制迁移到 v2。

详 [a2a/protocol.md](a2a/protocol.md) §6 v1.0.0 冻结声明。变更见 [CHANGELOG.md](CHANGELOG.md)。
