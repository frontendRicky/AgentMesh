# A2A Console

> 本地可运行的 A2A Runtime 可视化驾驶舱。默认进入中文普通模式，帮助非技术同事填写需求、生成前端项目任务包，并在 Phase 1 MVP 中提供 RunSession 执行控制入口；专家模式保留任务、Agent 协作、Timeline、产物、Token / Context 估算、模型选择和启动 Prompt 关键字视图。Human Review 是冷启动安全网，后续会逐步由 Policy Gate 判断哪些任务可自动推进。

## 自动化叙事

Console 正在从 L1「任务包 + 门禁」升级到 L2/L3「半自动编排 / 选择性自动」：

| 等级 | 名称 | Console 定位 |
|---|---|---|
| L0 | 纯手动 Prompt | 人手动复制 Prompt，多模型协作 |
| L1 | 任务包 + 门禁 | 生成任务包、查看状态、下载交付物 |
| L2 | 半自动编排 | RunSession 管理执行请求，关键节点仍暂停 |
| L3 | 选择性自动 | 低风险任务按 Policy Gate 自动推进 |
| L4 | 自动编程闭环 | 自动写代码、测试、修复、交付 |
| L5 | 多 Agent 自治工程团队 | 多任务并线、自升级、多模型评审 |

`automation_mode` 将用于描述项目或任务的自动化策略：`manual` / `assisted` / `selective_auto` / `full_auto`。

## 快速启动

```bash
cd apps/a2a-console
npm install
npm run dev
```

启动后：

- Client（UI）：<http://localhost:5173>
- Server（API）：<http://localhost:5174>

首次启动会要求在「设置」页配置 project root（指向任意包含 `.ai-agents/workspace/` 的项目根目录）。

## 主要页面

普通模式默认打开 `/generator`，右上角可切换专家模式。localStorage 没有显式记录时始终进入普通模式，不会根据 URL 自动切专家。

| 路由 | 用途 |
|---|---|
| `/` | 跳转到 `/generator` |
| `/generator` | 普通模式：中文前端项目生成向导 |
| `/tasks` | 普通模式显示“我的任务”并提供查看 / 执行 / 下载；专家模式显示全部 Task 列表 |
| `/dashboard` | 专家模式群聊主视图 |
| `/tasks/:taskId` | 专家模式单 Task 详情，7 Tab：群聊 / 概览 / 时间线 / Artifacts / 风险 / 指标 / Model & Prompt |
| `/blockers` | 当前 active task 的 blocker 速览 |
| `/model-prompt` | 单独的模型选择 + Prompt 关键字页面 |
| `/settings` | 项目根 + 轮询间隔 |

视觉约定：

- 6 个 Agent 各一种气泡颜色（Controller 紫 / PM 橙 / Architect 蓝 / Developer 绿 / QA 青 / Human 灰）
- 消息类型徽标：handoff / blocker / review / status / final 等
- 顶部 mini Timeline：PM → Architect → Human Review → Developer → QA → Final → Done
- 点 sidebar 头像可过滤群聊只看该 Agent；点气泡弹出完整 markdown

## 目录结构

```
apps/a2a-console/
├── package.json            # workspaces: ["packages/contract", "client", "server"]
├── tsconfig.base.json      # client + server 共享 strict ts
├── docs/                   # 架构 / API / 使用 / 安全 / 路线图
├── packages/contract/      # client + server 共享 zod schema / 推断类型
├── client/                 # Vite + React + TS + Tailwind + 14 个 minimal shadcn-style UI
└── server/                 # Express 4 + tsx，仅读 .ai-agents/workspace
```

## 已落地（ST-01 ~ ST-08）

**Server**
- `/api/a2a/health`、`/api/a2a/config/project-root`（GET/POST）、`/api/a2a/active-task`
- `/api/a2a/tasks`、`/tasks/:taskId`、`/tasks/:taskId/state`
- `GET /api/a2a/tasks/:taskId/download` — 下载任务包（ZIP STORE，50MB 上限）
- `GET /api/a2a/config/project-root` — 读取当前 project_root 配置
- `GET /api/a2a/runs?task_id=T-YYYY-NNN` — 查询内存 RunSession 列表
- `POST /api/a2a/runs` — 创建 RunSession（Phase 1 MVP：queued，仅内存）
- `PATCH /api/a2a/runs/:runId?action=pause|resume|cancel` — 更新 RunSession 状态
- `/tasks/:taskId/artifacts`（树）、`/tasks/:taskId/artifacts/file?path=...`（单文件，含 truncated 标记）
- `/tasks/:taskId/messages`、`/tasks/:taskId/blockers`、`/tasks/:taskId/reviews`
- `/tasks/:taskId/human-reviews`（deprecated，兼容旧 client）
- `/tasks/:taskId/metrics`（含 largest_artifacts Top 10）、`/tasks/:taskId/prompt-keywords`、`/api/a2a/model-presets`
- `/api/a2a/project-generator/templates`、`/drafts`、`/drafts/:draftId/tasks`
- 契约：`packages/contract` 提供 zod schema + `z.infer<>` 类型，覆盖 envelope / task detail / messages / metrics / model-presets / reviews
- 安全：`path-guard`（realpath + startsWith） / `file-size-guard`（>500KB 截断到 100KB） / 默认禁改集巡检 / 普通模式只允许创建新的 `.ai-agents/workspace/T-YYYY-NNN/` 任务包

**Client**
- 100px 左 sidebar：普通模式只显示“生成项目 / 我的任务 / 设置”；专家模式显示 6 Agent 头像 + 专家 nav
- Dashboard chat-first 群聊主视图 + 右侧 320px 状态摘要面板
- Generator 中文向导：项目类型、业务说明、页面范围、生成偏好、模型档位、任务包预览
- 7 Tab Task Detail（Chat 默认）：Overview / Timeline / Artifacts（文件树 + Markdown 预览） / Risk / Metrics（Recharts 双柱图 + Top10）/ Model & Prompt
- Tasks 列表（普通模式含“执行”按钮，写入 RunSession queue）+ Settings + Blockers + 独立 Model & Prompt 页
- 14 个 minimal shadcn-style UI 组件（基于 @radix-ui）+ 9 个业务组件
- 11 个数据 hook，统一 5s 轮询（可在设置页改）

## 已知限制（MVP 边界）

- Phase 1 MVP 的 `/runs` 只维护内存 RunSession；RunnerAdapter 与 Cursor SDK Runner 仍是接口骨架，不真正调用 LLM / Cursor SDK
- 普通模式只创建新的 `.ai-agents/workspace/T-YYYY-NNN/` 任务包，不修改 existing task 的 `state.md`
- `GET /api/a2a/runs` 重启后清空，不持久化
- task_id 由 server 按当前年份自增分配；client 只传 slug
- 不写 `apps/generated-projects/`，不提供隐藏开关或 feature flag 启用一键执行
- 单 markdown >500KB 仅预览前 100KB（带 truncated 警告）
- 5s 轮询刷新，无 WebSocket / chokidar
- 无鉴权（单机本地工具）
- Token 估算用 chars/3.5，仅供数量级参考

## 如何继续

普通模式点击“创建任务包”后，会在 `.ai-agents/workspace/T-YYYY-NNN/` 下生成 requirement、PRD、任务拆解、模型选择快照和 PM handoff。浏览器里的“下一步”按钮本期永久不可用；请把生成的任务编号交给技术同事，让技术同事在 Cursor / Codex 中从 Architect 阶段继续 A2A 流程。

## 技术栈

| 层 | 选型 |
|---|---|
| Client | Vite 5 + React 18 + TypeScript 5 strict + Tailwind 3 + 14 个 minimal shadcn-style 组件（基于 @radix-ui） + Zustand 4 + react-router-dom 6 + react-markdown 9 + recharts 2 + lucide-react |
| Server | Node 20 + Express 4 + tsx + gray-matter + zod |

完整依赖见 `client/package.json` / `server/package.json`，与 `.ai-agents/workspace/T-2026-002/artifacts/architect/tech-plan.md` §7 一致。

## API 自测

```bash
curl -s "http://localhost:5174/api/a2a/tasks/T-2026-003/metrics" | jq '.data.largest_artifacts'
curl -s "http://localhost:5174/api/a2a/tasks/T-2026-003/reviews"
curl -s "http://localhost:5174/api/a2a/tasks/T-2026-003/human-reviews"
curl -OJ "http://localhost:5174/api/a2a/tasks/T-2026-003/download"
curl -s "http://localhost:5174/api/a2a/runs?task_id=T-2026-003"
curl -s -X POST "http://localhost:5174/api/a2a/runs" \
  -H "content-type: application/json" \
  -d '{"task_id":"T-2026-003","agent":"developer"}'
```

## 参考文档

- PRD：`.ai-agents/workspace/T-2026-002/artifacts/pm/prd.md`（v2 含小白向 chat-first 原则）
- Tech Plan：`.ai-agents/workspace/T-2026-002/artifacts/architect/tech-plan.md`（v2）
- File Change Plan：`.ai-agents/workspace/T-2026-002/artifacts/architect/file-change-plan.md`（v2，93 个白名单文件）
- Risk Plan：`.ai-agents/workspace/T-2026-002/artifacts/architect/risk-plan.md`
- 架构 / API / 安全 / 使用：见 `docs/`
