# A2A Console

> 本地可运行的 A2A Runtime 可视化驾驶舱。读取 `.ai-agents/workspace/`，把任务、Agent 协作、Timeline、产物、Token / Context 估算、模型选择、启动 Prompt 关键字以「微信群聊」式视图展示。**只读为主，不调用 LLM，不修改 state.md，不自动执行 Agent。**

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

## 主要页面（小白向 / chat-first）

| 路由 | 用途 |
|---|---|
| `/` | **群聊主视图** — 左 sidebar 6 Agent 头像 / 中央 Agent 协作消息流 / 右侧状态摘要 + Prompt 关键字 + Context 估算条 |
| `/tasks` | 全部 Task 列表（active task 高亮） |
| `/tasks/:taskId` | 单 Task 详情，7 Tab：群聊 / 概览 / 时间线 / Artifacts / 风险 / 指标 / Model & Prompt |
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
├── package.json            # workspaces: ["client", "server"]
├── tsconfig.base.json      # client + server 共享 strict ts
├── docs/                   # 架构 / API / 使用 / 安全 / 路线图
├── client/                 # Vite + React + TS + Tailwind + 14 个 minimal shadcn-style UI
└── server/                 # Express 4 + tsx，仅读 .ai-agents/workspace
```

## 已落地（ST-01 ~ ST-08）

**Server（11 GET + 1 POST）**
- `/api/a2a/health`、`/api/a2a/config/project-root`（GET/POST）、`/api/a2a/active-task`
- `/api/a2a/tasks`、`/tasks/:taskId`、`/tasks/:taskId/state`
- `/tasks/:taskId/artifacts`（树）、`/tasks/:taskId/artifacts/file?path=...`（单文件，含 truncated 标记）
- `/tasks/:taskId/messages`、`/tasks/:taskId/blockers`、`/tasks/:taskId/reviews`
- `/tasks/:taskId/metrics`、`/tasks/:taskId/prompt-keywords`、`/tasks/:taskId/model-presets`
- 安全：`path-guard`（realpath + startsWith） / `file-size-guard`（>500KB 截断到 100KB） / 默认禁改集巡检 / 不接收任何写 `.ai-agents/**` 的请求

**Client**
- 100px 左 sidebar（6 Agent 头像 + 4 nav）+ 56px header（Task 标识 + 项目根）
- Dashboard chat-first 群聊主视图 + 右侧 320px 状态摘要面板
- 7 Tab Task Detail（Chat 默认）：Overview / Timeline / Artifacts（文件树 + Markdown 预览） / Risk / Metrics（Recharts 双柱图 + Top10）/ Model & Prompt
- Tasks 列表 + Settings + Blockers + 独立 Model & Prompt 页
- 14 个 minimal shadcn-style UI 组件（基于 @radix-ui）+ 9 个业务组件
- 11 个数据 hook，统一 5s 轮询（可在设置页改）

## 已知限制（MVP 边界）

- 不调用 LLM、不执行任何 `a2a-agent` CLI（关键字按钮只复制到剪贴板）
- 不写任何 `.ai-agents/**` 文件（包括 review record / state 推进，仍由 Cursor 主导）
- 单 markdown >500KB 仅预览前 100KB（带 truncated 警告）
- 5s 轮询刷新，无 WebSocket / chokidar
- 无鉴权（单机本地工具）
- Token 估算用 chars/3.5，仅供数量级参考

## 技术栈

| 层 | 选型 |
|---|---|
| Client | Vite 5 + React 18 + TypeScript 5 strict + Tailwind 3 + 14 个 minimal shadcn-style 组件（基于 @radix-ui） + Zustand 4 + react-router-dom 6 + react-markdown 9 + recharts 2 + lucide-react |
| Server | Node 20 + Express 4 + tsx + gray-matter + zod |

完整依赖见 `client/package.json` / `server/package.json`，与 `.ai-agents/workspace/T-2026-002/artifacts/architect/tech-plan.md` §7 一致。

## 参考文档

- PRD：`.ai-agents/workspace/T-2026-002/artifacts/pm/prd.md`（v2 含小白向 chat-first 原则）
- Tech Plan：`.ai-agents/workspace/T-2026-002/artifacts/architect/tech-plan.md`（v2）
- File Change Plan：`.ai-agents/workspace/T-2026-002/artifacts/architect/file-change-plan.md`（v2，93 个白名单文件）
- Risk Plan：`.ai-agents/workspace/T-2026-002/artifacts/architect/risk-plan.md`
- 架构 / API / 安全 / 使用：见 `docs/`
