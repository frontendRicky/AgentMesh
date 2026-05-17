# AgentMesh 产品需求说明（PRD）

**文档版本**：Draft · 对齐 Runtime **0.1.0rc5** · A2A 协议 **v1.0.0（冻结，2026-05-11）**  
**仓库**：AgentMesh  
**用途**：产品经理阅读、后续自升级迭代 Plan 的对齐基线

---

## 1. 一句话与定位

**AgentMesh** 是一套 **本地 Markdown 文件驱动** 的 AI 多 Agent 协作与工作流门禁系统：由 **Python A2A Runtime**（状态机与门禁，不调 LLM）、**TypeScript Cursor SDK Orchestrator**（可选自动化编排）、**A2A Console**（本地可视化 + 中文任务包向导）与 **冻结的 A2A 协议资产**（`.ai-agents/`）组成。目标是在 **Human Review / 风险决策** 未放行时，约束 AI 不得越权改代码。

---

## 2. 背景与机会

### 2.1 问题

- 在 Cursor / Codex 等多角色 Prompt 场景下，易出现：**跳过评审直接改代码、改动超出白名单、风险未确认、过程不可审计**。  
- 纯对话式 Agent **缺少可执行的流程契约**（谁、何时、可写何处）。

### 2.2 机会

将协作「制度化」为：**文件即协议** + **单一状态源（state.md）** + **双门禁写代码** + **两阶段 Blocker** + **P0/P1 风险人工决策** + **可导出的运行报告**。

---

## 3. 目标用户（Jobs-To-Be-Done）

| 画像 | 诉求 | 主要触点 |
|------|------|----------|
| 前端 / 全栈开发者 | 在门禁内含约束地用 AI 改代码 | Runtime CLI、`gate`、`prompt developer`、Cursor rules |
| AI 应用开发者 / 平台工程师 | 编排多 Agent、对接 Cursor | `.ai-agents/scripts/` Orchestrator |
| Tech Lead / 架构师 | 方案与白名单可控、风险可审计 | Architect artifacts、`file-change-plan`、risk / finalize |
| QA / 质量 Owner | 验收与边界可读 | QA artifacts、Console Metrics |
| PM / 业务（偏非技术） | 中文描述需求并交出任务包 | Console `/generator` 普通模式 |
| 项目负责人 | 评审点决策 | Human Review（CLI / Cursor / 编排器终端） |

**非目标（现阶段）**：完全不接触 Markdown workspace 的纯无代码用户（除非仅生成任务包后交由研发）；需要 **多人在线协同同一任务** 的 SaaS 形态（见 Console Roadmap 远期项）。

---

## 4. 产品架构（叙事）

```
Cursor / Codex（真人 + AI 执行）
       ▲                              ▲
       │ Prompt 文案                   │ 改源码（受 Gate + file-change-plan）
       │
Python A2A Runtime（无 LLM · 无自动写业务代码）
       ▲
       │ 读写 .ai-agents/workspace/<task-id>/
A2A 协议（.ai-agents/a2a、agents、flows、handoffs、rules、templates）

并行可选：
· TS Orchestrator（@cursor/sdk）自动召唤 Agent，在闸门处暂停
· A2A Console（Vite + Express）只读为主 + 普通模式写任务包
```

---

## 5. 核心模块与已实现能力（MVP）

### 5.1 A2A 协议（静态）

- **schema_version**：`a2a/v1`；**protocol_version**：`v1.0.0`（冻结）。  
- **元素**：Task、State、Message、Artifact、Blocker、Review、Handoff、State Machine、File Message Bus 等；配套 `rules/`、`flows/`、`templates/`、`agent-cards/`。  
- **角色**：PM、Architect、Senior FE Developer、QA、Flow Controller；Human Review Actor 为人类闸门。

### 5.2 Python A2A Runtime（`a2a_runtime/`）

**职责**：本地执行 Markdown A2A；管理 task/state/message/artifact/blocker/review/risk/final-delivery；生成带 **`[A2A]`** 头与 **Recommended Model** 段的 Prompt；强制执行 Gate / Review / Blocker / Risk / Final Delivery。

**命令域（摘要）**：`status`、`validate`、`task`、`prompt`、`gate developer`、`review`、`blocker`、`risk`、`finalize`、`report`、`model list|policy|recommend`；变更类支持 `--dry-run` / `--yes`；`--project-root` / `--json`。

**明确不包含**：真实 LLM Provider、Runtime 侧 `run pm` 等全自动执行命令、HTTP Server、git commit/push、修改 `.ai-agents` 协议树与 `.cursor`。

**工程**：Python **≥3.11**，**零第三方依赖**（标准库）；配套大量单元/E2E 测试（README 记载约 317 测试通过量级）。

### 5.3 Cursor SDK Orchestrator（`.ai-agents/scripts/`）

**职责**：通过 `@cursor/sdk` 驱动 PM → Architect → Developer → QA → Controller 轮转；在 Human Review、Final Review、澄清、Blocker 处暂停。

**依赖**：`CURSOR_API_KEY`；调用 Cursor Cloud Agents API。

### 5.4 A2A Console（`apps/a2a-console/`）

**职责**：本地「驾驶舱」；**不调 LLM**、**不 shell-out `a2a-agent`**；读 `.ai-agents/workspace`，写限于配置与 **普通模式新建任务包**。

**双模式**：普通模式默认 `/generator`（中文向导）；专家模式 Dashboard、Task 详情七 Tab 等。

**技术边界**：大文件截断预览、5s 轮询、无 WebSocket、**无鉴权**（单机工具）；不写 `apps/generated-projects/`。

---

## 6. 状态机与用户旅程（摘要）

- **`current_status`**：14 态（`created` … `completed` / `blocked` / `cancelled`）；Human/Final 审核子状态见 `human_review_status` / `final_review_status`。  
- **主路径 A（保守）**：`task create` → 各阶段 `prompt` → 双步 `review` → `gate` + Developer → QA → Final → `finalize`。  
- **主路径 B（编排器）**：`start-task` / `resume-task`，闸门处交互暂停。  
- **主路径 C（Console 普通模式）**：向导生成 `T-YYYY-NNN` 任务包（预制 `pm_completed`）→ **研发**从 Architect 继续；**浏览器内不一键执行代码生成**（当期产品边界）。

---

## 7. 功能需求明细（FR）

| ID | 描述 |
|----|------|
| FR-01 | 任务静态信息在 `task.md`，动态状态仅在 `state.md`，且仅 Controller 逻辑写入 state |
| FR-02 | 写代码须：`developer_processing` + `human_review_status=approved` + 路径命中 file-change-plan 白名单 |
| FR-03 | Blocker：专业 Agent 仅 request；正式 Blocker 仅 Controller |
| FR-04 | P0/P1 风险须人工决策；Finalize 前 unresolved P0/P1 阻塞 |
| FR-05 | Developer Gate：禁改 CI/CD、根配置等路径集合（含 monorepo 深度策略） |
| FR-06 | Console：API + 普通模式任务包创建；专家模式可视化；契约 Zod（`packages/contract`） |

---

## 8. 非功能需求（NFR）

| 类别 | 要求 |
|------|------|
| 安全 | Console path-guard、artifact 大小上限；单机无鉴权假设需对外说明 |
| 可审计 | frontmatter：`task_id`、`created_at`、`produced_by`、`schema_version` |
| 可操作性 | CLI JSON、`[A2A CLI Error]`、明确 exit codes |
| 可测试 | Runtime unittest/E2E；Console 契约校验 |

---

## 9. 文档债与开放问题

1. **`a2a-bootstrap-project`**：`PRODUCT.md` 提及接入工具，**本仓库未检出对应实现**——需「实现」或「修订文档」。  
2. **双轨推进**：纯 Runtime 手动 vs SDK 编排，需在 onboarding 中写清选用场景。  
3. **Console 普通模式** 预置 `pm_completed`：对外需说明「PM 产物为向导生成模板」，避免误解为真实 PM Agent 已跑完 LLM。

---

## 10. 建议迭代主线（供 Plan 拆解）

1. **Runtime & onboarding**：bootstrap 一致性、试点文档与 CLI 叙事收敛。  
2. **Orchestrator**：可观测性、失败恢复、与 Runtime 状态对齐说明。  
3. **Console**：从「任务包」到「可选受控执行」（若做：二次确认、白名单 runner，见专项 PRD）。  
4. **协议演进**：v1.1+ 的冻结/迁移流程（若触碰冻结协议需单独治理）。

---

## 附录 A · 配套说明（迭代 Plan 常用）

### A.1 项目目标用户（结论）

**混合**：深度用户为 **前端 / 全栈 / AI 应用开发者与技术负责人**；**企业团队**中 **PM / 业务**通过 Console **起草任务包**；全流程闭环仍依赖 **研发与 Cursor/Codex**。

### A.2 当前 MVP 已实现功能（ checklist）

- Runtime：Task、校验、Prompt、Gate、Review、Blocker、Risk、Finalize、Report、模型推荐与 override、`--dry-run/--yes`。  
- Orchestrator：start/resume、评审终端交互、澄清检测、按 Agent 配模型。  
- Console：双模式、只读 API、七 Tab 详情、Metrics、Artifacts、普通模式写任务包、轮询。  
- 协议：v1.0.0 冻结资产全集。

### A.3 代码目录结构（高层）

```
AgentMesh/
├── a2a_runtime/           # Python Runtime
├── tests/
├── docs/
├── apps/a2a-console/      # client / server / packages/contract
├── .ai-agents/            # 协议、workspace、scripts、examples
├── .cursor/
├── prd/                   # 其他专项 PRD 草稿
├── openspec/
├── planning/              # 本目录：PRD + 你将放入的 Plan
├── PRODUCT.md
├── README.md
├── pyproject.toml
└── CHANGELOG.md
```

### A.4 核心页面说明（Console，无截图）

| 路由 | 说明 |
|------|------|
| `/` → `/generator` | 默认中文向导 |
| `/generator` | 类型、业务描述、页面/策略/模型、预览、创建任务包 |
| `/tasks` | 普通「我的任务」/ 专家全列表 |
| `/dashboard` | 专家群聊 + 状态摘要 + mini Timeline |
| `/tasks/:taskId` | Chat / Overview / Timeline / Artifacts / Risk / Metrics / Model & Prompt |
| `/blockers` | Active task blocker 速览 |
| `/model-prompt` | 模型与 Prompt 关键字 |
| `/settings` | project root、轮询间隔 |

### A.5 Console 普通模式「一键生成」任务包结构（落盘）

在配置的 **project root** 下：

```
.ai-agents/workspace/<T-YYYY-NNN>/
├── task.md
├── state.md
├── artifacts/pm/
│   ├── requirement.md
│   ├── prd.md
│   ├── task-breakdown.md
│   ├── model-selection-snapshot.md
│   └── user-input-snapshot.md
└── messages/from-pm-001-handoff.md
```

**不写**：业务源码、`apps/generated-projects/`。

### A.6 技术栈

| 部分 | 技术 |
|------|------|
| Runtime | Python 3.11+，标准库，`a2a-agent` 入口 |
| Orchestrator | Node、tsx、`@cursor/sdk`、chalk、gray-matter、inquirer |
| Console | Vite 5、React 18、TS strict、Tailwind、Radix、Zustand、react-router、react-markdown、recharts |
| Console API | Express 4、tsx、zod、gray-matter |

### A.7 当前主要卡点（产品视角）

1. 手动 Runtime 与 SDK 编排 **两条心智**，需统一 onboarding。  
2. **bootstrap 文档与实现** 可能不一致。  
3. Console **止于任务包**，非技术用户价值依赖交接话术与研发接手。  
4. 单机无鉴权 / 轮询 — **企业采购叙事**需补强（私有化、审计、备份）。  
5. 强门禁带来 **效率摩擦**，需在向导层解释「为何需要」。

### A.8 商业形态取向（基于现状的推断）

当前代码形态最贴合 **开源核心 + 私有化交付**；**SaaS** 需账号、隔离、计费与大改数据层；**模板市场**可作为 flows/templates 分发生态。

### A.9 「A2A」定义（重要）

本项目 **A2A** = **项目自定义的本地 File-based Agent-to-Agent 协作协议**（见 `.ai-agents/a2a/protocol.md`），**不是** Google 等推广的 **Agent2Agent（A2A）开放网络协议**的同名实现。

---

## 参考索引（仓库内）

- `PRODUCT.md` — 产品一页纸  
- `README.md` — Runtime 权威说明  
- `.ai-agents/a2a/protocol.md`、`state-machine.md`  
- `apps/a2a-console/README.md`、`docs/architecture.md`、`docs/roadmap.md`  
- `prd/a2a-console-non-tech-project-generator-prd.md` — Console 小白向导专项草稿  

---

*本文档由代码与上述索引对齐整理；协议版本与 Runtime 版本以仓库当前冻结内容为准，迭代时请同步更新本节元数据。*
