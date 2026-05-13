# AgentMesh — 产品说明

> GitHub：[https://github.com/frontendRicky/AgentMesh](https://github.com/frontendRicky/AgentMesh)
> Runtime 版本：0.1.0rc5 · Python 3.11+ · 零外部依赖

---

## 一句话定义

**AgentMesh** 是一套本地文件驱动的 AI 多 Agent 协作系统，由 **Python A2A Runtime**（状态机执行引擎）和 **Cursor SDK TypeScript Orchestrator**（自动化编排器）两部分组成，让 PM → Architect → Developer → QA → Controller 五个 AI Agent 按严格工作流有序协作完成前端开发任务，全程无需手动复制粘贴 Prompt，遇到 Human Review / 模糊需求时自动暂停等待人工决策。

---

## 两个核心模块

### 1. Python A2A Runtime（`a2a_runtime/`）

**定位**：本地 CLI 状态机引擎，不调 LLM，不写业务代码，只管状态流转、门禁检查、Prompt 生成。

**主要能力：**

- **Task 生命周期管理**：`task create / list / active`，创建 Task 写 `task.md` + `state.md` + `active-task.md`
- **Prompt 生成**：为 PM / Architect / Developer / QA / Controller 生成带严格 `[A2A]` 头和 Recommended Model 段的 Cursor Prompt，不执行
- **Developer Gate 门禁**：写源码前五条硬检：state 必须是 `developer_processing` + `human_review_status=approved` + 路径在 `file-change-plan` 白名单 + 不命中禁改集（`.github/`、`package.json`、CI/CD、Dockerfile 等）
- **Human Review 双步流转**：`review approve/reject`，不允许合并两步
- **两阶段 Blocker**：专业 Agent 只能发 `blocker-request`，正式 Blocker 只能由 Controller 创建
- **P0/P1 Risk Gate**：P0/P1 风险必须显式人工决策，Final Delivery 前必须清零
- **模型推荐**：`model recommend --agent <pm|architect|developer|qa|controller> --tool <cursor|codex>`，只输出建议，不执行
- **报告导出**：`report` 打印完整运行态，`--output` 导出到 task archive
- **`--dry-run` / `--yes` 双模式**：所有写操作先 dry-run 预览，确认再 `--yes` 落盘

**CLI 命令格式：**

```bash
a2a-agent --project-root <项目目录> <命令> [选项] [--json] [--dry-run|--yes]
```

**安全边界：** 不调 LLM、不写业务源码、不执行 Codex、不 git commit/push、不修改 `.ai-agents/a2a/` 协议文件、不绕过任何 Review/Gate。

---

### 2. TypeScript Cursor SDK Orchestrator（`.ai-agents/scripts/`）

**定位**：通过 `@cursor/sdk` 在终端全自动编排 A2A 五个 Agent，按状态机连续驱动，无需人工切换 Cursor。

**三种使用方式：**

```bash
# 方式 1：一键全自动跑完（PM→Arch→Dev→QA，Human Review 节点自动暂停问你）
./start-task --type feature --priority P2 --owner zhangxia "需求：新增角色权限管理模块"

# 方式 2：从中断处继续
./resume-task               # 自动读 active-task.md
./resume-task T-2026-001    # 指定 task id

# 方式 3：手动单步
./pm "分析需求..."
./architect "出技术方案"
./developer "按 file-change-plan 实现"
./qa "7 维测试验收"
./controller "推进状态"
```

**自动化流程：**

```
start-task → Controller 创建 Task → PM 写需求产物 → Architect 写方案
→ ⏸ Human Review（终端问你 verdict）→ Controller 双步推进
→ Developer 实现（5 条 Gate 自检）→ QA 验收
→ ⏸ Final Review（终端问你 verdict）→ Controller 写 final-delivery.md ✨
```

**关键保护机制：**

- 遇模糊需求：Agent 写 `clarification-questions.md` 后强制暂停，编排器引导你逐条回答
- 遇 Blocker：显示 `active_blocker`，等待人工裁决
- 双步中间态自动恢复：Controller 启动自检场景 0 自动补做被中断的第 2 步
- 遇 `state.current_status` 连续 3 轮不变：询问是否继续

---

## A2A 协议（`.ai-agents/`）

**版本**：`a2a/v1.0.0`，已于 2026-05-11 冻结。

协议层提供以下静态资产，由 Runtime 读取，不允许被 Runtime 修改：

| 目录 | 内容 |
|---|---|
| `a2a/` | 14 个 Schema（state / blocker / review / message / task / artifact / file-change-plan / handoff-contract 等）|
| `agents/` | 5 份 Agent 行为定义（PM / Architect / Developer / QA / Controller）|
| `agent-cards/` | 5 份机器可读权限卡（writable_paths 白名单）|
| `handoffs/` | 6 份 Handoff Contract（user→PM / PM→Arch / Arch→HumanReview / HumanReview→Dev / Dev→QA / QA→FinalReview）|
| `flows/` | 6 条 Flow（feature / refactor / bugfix / ui-redesign / permission / api-integration）|
| `rules/` | 7 份规则（a2a-rules / cursor-rules / code-change-rules / frontend-rules / global-rules / review-rules / test-rules）|
| `templates/` | 16 份可复制模板（PRD / task / tech-plan / file-change-plan / test-report 等）|

---

## 技术规格

| 项 | 值 |
|---|---|
| Runtime 版本 | 0.1.0rc5 |
| Python 要求 | 3.11+，仅用标准库，零依赖 |
| TypeScript 要求 | Node.js + `tsx`，依赖 `@cursor/sdk` / `chalk` / `gray-matter` / `@inquirer/prompts` |
| 协议版本 | A2A v1.0.0（冻结）|
| 状态机状态数 | 14 个 |
| 单测 / E2E 测试 | 50+ 测试文件，317 个测试通过 |
| 全局安装路径 | `~/.a2a-runtime/`，CLI 快捷入口 `~/.local/bin/a2a-agent` |
| 项目接入工具 | `a2a-bootstrap-project <project-root> [--dry-run]` |
| 每个项目的 task workspace | 留在 `<project>/.ai-agents/workspace/<task-id>/`，不跨项目共用 |

---

## 适用场景

- 前端工程团队用 Cursor 开发新功能 / 重构 / Bug Fix，需要 AI Agent 协助但不想 AI 未经审核直接改代码
- 需要 PM 写需求 → Architect 出方案 → 人工审核 → Developer 有限改代码 → QA 验收这套有保障的流程
- 希望 AI 操作有完整审计链（每个产物含 task_id / created_at / produced_by，每个状态转移有历史记录）
- 希望 P0/P1 风险必须人工决策，不被 AI 自动绕过

---

## 关键约束

1. **Runtime 不执行 LLM**：所有 Prompt 生成后由人工复制到 Cursor，Runtime 只做状态管理和门禁
2. **每次操作必须带 `--project-root`**：Runtime 通过它定位项目内的 `.ai-agents/workspace/`
3. **写源码前必须先跑 Gate**：`a2a-agent gate developer --path <文件> --operation modify --json`
4. **state.md 只有 Controller 能写**，其他 Agent 不得直接改
5. **Human Review 是真实人工操作**：Runtime 不会伪造 review record
6. **Task workspace 属于各自项目**：不允许全局共用同一个 workspace 管理多个项目的 Task

---

## 快速使用

```bash
# 第一步：接入新项目
a2a-bootstrap-project /path/to/project --dry-run   # 先预览
a2a-bootstrap-project /path/to/project             # 确认后执行

# 第二步：创建 Task
a2a-agent --project-root /path/to/project task create \
  --type feature --title "新增权限管理模块" --priority P2 --owner zhangxia --yes

# 第三步A：手动生成 Prompt，复制到 Cursor 执行
a2a-agent --project-root /path/to/project prompt pm
a2a-agent --project-root /path/to/project prompt architect
a2a-agent --project-root /path/to/project prompt developer \
  --path src/pages/permission/index.tsx --operation create

# 第三步B：或用 Orchestrator 全自动跑（进入 .ai-agents/scripts/ 后）
npm install
./start-task --type feature --priority P2 --owner zhangxia "新增权限管理模块"

# 写代码前 Gate 检查
a2a-agent --project-root /path/to/project gate developer \
  --path src/pages/permission/index.tsx --operation create --json
```
