# PRD：A2A Runtime 可视化控制台

## 1. 目标

为现有 Markdown File-based A2A Runtime 增加一个本地可运行的前端可视化控制台，用于查看任务、Agent 对话、执行步骤、产物、状态流转、Token 消耗、上下文容量、模型选择与启动 Prompt 关键字。

目标不是替代 CLI，而是作为 A2A 的可视化驾驶舱。

---

## 2. 产品定位

推荐名称：**A2A Console**

定位：本地运行的 A2A Runtime Dashboard，用前端页面可视化管理 `.ai-agents/workspace` 中的任务、消息、产物、状态、成本和 Agent 协作过程。

---

## 3. 核心用户

- 前端技术经理
- AI Agent 开发者
- 使用 Cursor / Codex / 多 Agent 工作流的人
- 需要审查 A2A 执行过程、结果、风险与成本的人

---

## 4. 核心场景

### 4.1 查看当前任务执行状态

用户打开本地页面，可以看到：

- 当前 active task
- current_status
- current_agent
- Human Review 状态
- Final Review 状态
- 当前阶段产物
- 是否 blocked
- 下一步建议操作

### 4.2 像微信群一样查看 Agent 协作消息

每个 Agent 是一个角色：

- Controller
- PM
- Architect
- Developer
- QA
- Human

页面以聊天群 UI 展示：

- Agent 头像
- Agent 名称
- 消息时间
- 消息类型
- handoff / blocker / review / output
- 可展开对应 artifact

### 4.3 查看执行步骤

展示完整流程：

```text
Task Created
→ PM Processing
→ PM Completed
→ Architect Processing
→ Human Review Required
→ Developer Processing
→ QA Processing
→ Final Review Required
→ Completed
```

每一步展示：

- 状态
- 开始时间
- 结束时间
- 耗时
- 产物
- 是否通过
- 是否有 blocker

### 4.4 查看 Token 与上下文消耗

控制台展示：

- 每个 Agent 的 token 消耗
- 每个阶段的 token 消耗
- 当前任务总 token
- 输入 token / 输出 token
- 估算成本
- 当前上下文容量
- 已使用上下文比例
- 高风险上下文膨胀提示

### 4.5 Human Review 可视化审批

当状态为：

- human_review_required
- final_review_required

页面展示：

- 待审 artifacts
- file-change-plan
- risk-plan
- QA test-report
- changed-files
- approve / needs_changes / reject 按钮

第一版只生成 review markdown，不直接自动改 state；状态推进仍交给 Controller 校验。

### 4.6 页面选择模型并展示启动 Prompt 关键字

用户可以在页面上为不同 Agent 选择模型，并查看每个阶段启动时需要复制给 Cursor / Codex / CLI 的 Prompt 关键字。

例如：

- PM：`a2a-agent --project-root "$(pwd)" prompt pm`
- Architect：`a2a-agent --project-root "$(pwd)" prompt architect`
- Developer：`a2a-agent --project-root "$(pwd)" prompt developer`
- QA：`a2a-agent --project-root "$(pwd)" prompt qa`
- Controller：`a2a-agent --project-root "$(pwd)" prompt controller`

页面提供复制按钮，但第一版不直接自动执行命令。

---

## 5. 功能模块

## 5.1 Dashboard 首页

展示：

- Active Task 卡片
- 当前 Agent
- 当前状态
- 阻塞状态
- 下一步动作
- 最近任务列表
- 今日 token 消耗
- 当前上下文容量
- 最近 blocker
- 当前推荐模型
- 当前阶段启动 Prompt 关键字

---

## 5.2 Task List 任务列表

字段：

| 字段 | 说明 |
|---|---|
| task_id | T-2026-xxx |
| title | 任务标题 |
| status | 当前状态 |
| agent | 当前 Agent |
| priority | P0/P1/P2 |
| created_at | 创建时间 |
| updated_at | 更新时间 |
| token_total | token 总量 |
| blocker_count | blocker 数量 |

支持：

- 搜索
- 按状态筛选
- 按 Agent 筛选
- 按优先级筛选
- 打开任务详情

---

## 5.3 Task Detail 任务详情

包含 7 个 Tab：

1. Overview
2. Agent Chat
3. Timeline
4. Artifacts
5. Risk / Blockers
6. Metrics
7. Model & Prompt

---

## 5.4 Agent Chat 群聊视图

UI 类似微信群：

左侧：Agent 列表

- Controller
- PM
- Architect
- Developer
- QA
- Human

中间：消息流

消息类型：

- task created
- stage handoff
- blocker request
- gate failure
- review record
- QA report
- final delivery

消息卡片展示：

- Agent 头像
- Agent 名称
- 时间
- 内容摘要
- 关联 artifact
- 点击展开 markdown

---

## 5.5 Timeline 执行步骤视图

用纵向流程图展示：

```text
PM
Architect
Human Review
Developer
QA
Final Review
Completed
```

每一步展示：

- 状态：pending / running / passed / failed / blocked
- 耗时
- 输入 artifacts
- 输出 artifacts
- token 消耗
- 风险数量

---

## 5.6 Artifacts 文件视图

读取：

```text
.ai-agents/workspace/<task-id>/artifacts/**
.ai-agents/workspace/<task-id>/messages/**
.ai-agents/workspace/<task-id>/human-reviews/**
.ai-agents/workspace/<task-id>/blockers/**
```

功能：

- 文件树
- Markdown 预览
- diff 预览
- 搜索 artifact
- 一键复制内容
- 下载 markdown

---

## 5.7 Metrics 指标视图

### Token 指标

- 总 token
- PM token
- Architect token
- Developer token
- QA token
- Review token

### 上下文指标

- 当前上下文使用量
- 最大上下文容量
- 使用百分比
- 超限风险提示

### 成本指标

- 估算成本
- 每阶段成本
- 每 Agent 成本

### 效率指标

- 总耗时
- 每阶段耗时
- blocker 次数
- rerun 次数
- needs_changes 次数

---

## 5.8 Blocker 中心

展示：

- blocker-request
- gate-failure-request
- path-out-of-whitelist
- new-dependency
- upstream-conflict
- forbidden-path violation

支持：

- 按严重程度筛选
- 查看阻塞原因
- 查看建议解决路径
- 查看不影响部分

---

## 5.9 Human Review 面板

当任务进入 review 状态：

显示：

- 待审材料
- 风险项
- 白名单文件
- changed-files diff
- QA 结果

操作：

- Approve
- Needs Changes
- Reject

输出：

```text
human-reviews/architect-review.md
human-reviews/final-review.md
```

第一版只写 review record，不直接改 state。

---

## 5.10 Model & Prompt 面板

### 目标

在页面中集中管理每个 Agent 使用的模型，以及当前阶段启动所需的 Prompt 关键字。

### 功能

1. 模型选择
   - 全局默认模型
   - 每个 Agent 单独模型
   - 当前任务临时模型

2. 推荐模型展示
   - PM 推荐模型
   - Architect 推荐模型
   - Developer 推荐模型
   - QA 推荐模型
   - Controller 推荐模型

3. 启动 Prompt 关键字展示
   - 根据 current_status 自动展示下一步 Prompt
   - 支持复制
   - 支持查看完整 Prompt
   - 支持查看 CLI 命令

4. 模型能力提示
   - 上下文容量
   - 是否适合规划
   - 是否适合代码修改
   - 是否适合 QA 审查
   - 成本等级

### 推荐模型配置示例

```json
{
  "defaultModel": "gpt-5.5",
  "agents": {
    "pm": "gpt-5.5",
    "architect": "claude-opus-4-7-thinking-high",
    "developer": "gpt-5.5",
    "qa": "gpt-5.5",
    "controller": "gpt-5.5"
  }
}
```

### 启动 Prompt 关键字示例

| Agent | Prompt 关键字 | 用途 |
|---|---|---|
| Controller | `prompt controller` | 状态推进 / blocker 处理 |
| PM | `prompt pm` | 需求拆解 |
| Architect | `prompt architect` | 技术方案 + 白名单 |
| Developer | `prompt developer` | 按 file-change-plan 实施 |
| QA | `prompt qa` | 验收与 test-report |

### 当前阶段自动推荐

| current_status | 推荐操作 |
|---|---|
| pm_processing | 复制 PM Prompt |
| architect_processing | 复制 Architect Prompt |
| human_review_required | 打开 Human Review 面板 |
| developer_processing | 复制 Developer Prompt |
| qa_processing | 复制 QA Prompt |
| final_review_required | 打开 Final Review 面板 |
| blocked | 复制 Controller Prompt |
| completed | 查看 final-delivery |

### 存储策略

第一版可使用本地配置文件：

```text
.ai-agents/config/model-presets.json
```

或 Console 自己的配置：

```text
apps/a2a-console/config/model-presets.json
```

MVP 建议只读展示 + localStorage 保存 UI 选择，不写入 A2A 核心配置。

---

## 6. 技术方案

## 6.1 前端技术栈

推荐：

- Vite
- React 18
- TypeScript
- Tailwind CSS
- shadcn/ui
- Zustand
- React Router
- Markdown renderer
- Recharts

---

## 6.2 本地服务

需要一个轻量 Node 服务读取本地文件：

```text
apps/a2a-console/
  client/
  server/
```

Server 能力：

- 读取 `.ai-agents/workspace`
- 读取 active-task.md
- 读取 state.md
- 读取 artifacts
- 读取 messages
- 读取 review
- 读取 blocker
- 读取模型 preset
- 提供 REST API

---

## 6.3 API 设计

### 获取 active task

```http
GET /api/a2a/active-task
```

### 获取任务列表

```http
GET /api/a2a/tasks
```

### 获取任务详情

```http
GET /api/a2a/tasks/:taskId
```

### 获取 artifacts

```http
GET /api/a2a/tasks/:taskId/artifacts
```

### 获取消息

```http
GET /api/a2a/tasks/:taskId/messages
```

### 获取指标

```http
GET /api/a2a/tasks/:taskId/metrics
```

### 获取模型配置

```http
GET /api/a2a/model-presets
```

### 获取当前阶段 Prompt 关键字

```http
GET /api/a2a/tasks/:taskId/prompt-keywords
```

### 写 review record

```http
POST /api/a2a/tasks/:taskId/reviews
```

---

## 7. 数据读取规则

第一版只读为主。

允许写：

- human-reviews/*.md
- 可选：messages/from-human-*.md
- Console localStorage UI 配置

禁止写：

- state.md
- task.md
- source code
- artifacts/pm/**
- artifacts/architect/**
- artifacts/developer/**
- artifacts/qa/**

状态推进仍由 Controller 负责。

---

## 8. Token 统计方案

第一版如果没有真实 token 数据，可采用三层方案：

### V1：估算

按文本长度估算：

```text
token ≈ chars / 3.5
```

### V2：从 Agent 日志读取

如果 message / implementation-log 中有 usage 信息，优先读取。

### V3：模型级真实 usage

后续接入 API usage：

```json
{
  "model": "gpt-5.5",
  "input_tokens": 12345,
  "output_tokens": 2345,
  "cost": 0.12
}
```

---

## 9. 上下文容量方案

展示：

- 当前任务 artifacts 总字符数
- 当前消息总字符数
- 当前阶段输入总字符数
- 估算 token
- 模型最大上下文
- 使用百分比

风险提示：

| 使用率 | 状态 |
|---|---|
| < 50% | safe |
| 50-75% | warning |
| 75-90% | high |
| > 90% | danger |

---

## 10. UI 结构

```text
A2A Console
├── Sidebar
│   ├── Dashboard
│   ├── Tasks
│   ├── Active Task
│   ├── Blockers
│   ├── Model & Prompt
│   └── Settings
│
├── Header
│   ├── Project Root
│   ├── Active Task
│   ├── Status Badge
│   ├── Model Selector
│   └── Token Summary
│
└── Main
    ├── Overview Cards
    ├── Agent Chat
    ├── Timeline
    ├── Artifacts
    ├── Review Panel
    ├── Metrics
    └── Model & Prompt
```

---

## 11. 推荐新增功能点

### 11.1 一键生成 Cursor Prompt

在每个阶段页面增加：

- Generate PM Prompt
- Generate Architect Prompt
- Generate Developer Prompt
- Generate QA Prompt

读取当前 state 自动生成下一步 prompt。

### 11.2 风险雷达

自动扫描：

- 是否触碰 forbidden paths
- changed-files 是否超出 file-change-plan
- 是否新增依赖
- 是否跳过 Human Review
- 是否 state 与 active task 冲突

### 11.3 A2A 状态冲突检测

例如：

- active task 是 T-2026-004
- 用户正在审 T-2026-003
- completed task 又被发现 bug

页面提示：

```text
检测到 A2A 状态冲突，建议新建 reroute task 或 reopen 原 task。
```

### 11.4 Reroute / Patch Round 管理

支持：

- R1
- R2
- R3
- needs_changes
- final_review_required
- patch history

展示每轮：

- changed-files-r2
- implementation-log-r2
- test-report-r2

### 11.5 文件白名单对比

自动对比：

```text
architect/file-change-plan.md
developer/changed-files.md
```

输出：

- 合规文件
- 越界文件
- 禁改文件
- 未声明文件

### 11.6 Artifact Diff

支持对比：

- implementation-log-r1 vs r2
- changed-files-r1 vs r2
- risk-plan 版本变化
- review 版本变化

### 11.7 本地任务搜索

支持搜索：

- task_id
- 文件路径
- blocker
- Agent 消息
- artifact 内容

### 11.8 Agent 头像与角色卡

每个 Agent 有角色卡：

- 角色职责
- 可写路径
- 禁止行为
- 当前状态
- 当前模型
- 最近输出

### 11.9 成本预算提醒

可设置：

```text
单任务 token 上限
单任务成本上限
单阶段 token 上限
```

超出提醒：

```text
该任务已消耗 80% token 预算，建议压缩上下文或拆分任务。
```

### 11.10 Runbook / SOP 面板

内置 SOP：

- Bugfix SOP
- API Integration SOP
- A2A SOP
- QA SOP
- Human Review SOP

点击可复制 Prompt。

---

## 12. MVP 范围

### 必须有

- 本地启动
- 选择 project root
- 读取 active task
- 任务列表
- 任务详情
- Agent Chat
- Timeline
- Artifacts Markdown 预览
- Token 估算
- Context 使用率
- Model Selector
- 当前阶段 Prompt 关键字展示
- Human Review 只读展示
- Blocker 展示

### 暂不做

- 真正调用 LLM
- 自动推进 state
- 在线多人协作
- 远程部署
- 权限系统
- 数据库

---

## 13. 验收标准

- [ ] 本地 `npm run dev` 可启动
- [ ] 能选择或配置 project root
- [ ] 能读取 `.ai-agents/workspace/active-task.md`
- [ ] 能展示任务列表
- [ ] 能展示 current_status / current_agent
- [ ] 能展示 Agent 消息流
- [ ] 能预览 markdown artifacts
- [ ] 能展示 Timeline
- [ ] 能估算 token
- [ ] 能展示上下文使用率
- [ ] 能选择 Agent 模型
- [ ] 能展示当前阶段启动 Prompt 关键字
- [ ] 能复制 Prompt 关键字
- [ ] 能展示 blocker
- [ ] 不修改 state.md
- [ ] 不修改源码
- [ ] Console 无 error
- [ ] TypeScript 无 error

---

## 14. 非目标

第一版不做：

- 替代 Cursor / Codex
- 自动运行 Agent
- 自动修改源码
- 自动合并状态
- 云端多人协作
- 生产部署
- 复杂权限系统

---

## 15. 交付物

```text
apps/a2a-console/
├── client/
├── server/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── usage.md
│   └── roadmap.md
```

---

## 16. 给 A2A 自升级的执行建议

请让 A2A 自己按以下阶段执行：

### Phase 1：PM

输出：

- requirement-analysis.md
- frontend-scope.md
- api-contract-checklist.md
- state-and-action-matrix.md
- risk-and-open-questions.md

### Phase 2：Architect

输出：

- tech-plan.md
- file-change-plan.md
- risk-plan.md

重点确认：

- 是否新建 apps/a2a-console
- 是否允许新增 package.json
- 是否允许新增 Node server
- 是否读取本地文件系统
- 是否允许引入 UI 依赖
- 模型选择配置存在哪里
- Prompt 关键字是否只展示不执行

### Phase 3：Human Review

需要确认：

- 技术栈
- 目录位置
- 是否允许新增依赖
- 是否允许写 review record
- 是否只读 state.md
- 模型 preset 是否只写 Console 本地配置

### Phase 4：Developer

实现 MVP。

### Phase 5：QA

验证：

- 本地启动
- 读取真实 A2A workspace
- 任务状态正确
- artifacts 预览正确
- token 估算正确
- 模型选择生效
- Prompt 关键字展示正确
- 不误写 state.md

---

## 17. 第一版推荐优先级

P0：

- 本地启动
- 任务列表
- active task
- Agent Chat
- Artifacts 预览
- Timeline
- 当前阶段 Prompt 关键字

P1：

- Token 估算
- Context 使用率
- Blocker 中心
- Human Review 面板
- Model Selector

P2：

- 成本估算
- Artifact diff
- 状态冲突检测
- 一键生成完整 Prompt

P3：

- 自动运行 Agent
- WebSocket 实时刷新
- 多项目管理
