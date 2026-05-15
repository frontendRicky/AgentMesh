# Architecture

## 概览

A2A Console = 本地 Vite + React 单页前端 + Express 只读后端。两个进程在同机协作，通过 Vite dev proxy 把 `/api/*` 转发到 Express。

```
Browser (localhost:5173)
   │  Vite dev proxy /api → :5174
   ▼
Express server (localhost:5174)
   │  path-guard (realpath + startsWith)
   ▼
.ai-agents/workspace/ (read-only fs)
```

## 进程边界

- **client**：Vite dev server，仅 dev 用；prod 用 `vite build` + 任意静态服务。MVP 只考虑 dev。
- **server**：Express 4 + tsx；dev `tsx watch src/index.ts`，prod `tsc && node dist/index.js`。MVP dev 即可。
- 两者**完全独立**进程，无 IPC，仅通过 HTTP。

## 安全边界

- **唯一写路径**：`apps/a2a-console/.a2a-console-config.json`（仅存 project_root）。
- **不写**：`.ai-agents/**`、源码、`a2a_runtime/**`、根目录任何文件。
- **不读外网**：server 不发任何外部 HTTP。
- **不调用 LLM**：无任何 OpenAI / Anthropic / `a2a-agent` SDK / CLI。
- **path traversal 防护**：`server/src/lib/path-guard.ts` 单点 `fs.realpathSync` + `startsWith` 校验。

## 数据流

所有动态业务数据**每次请求重新读 fs**，无缓存层。理由：

- 单机本地，fs 读延迟 < 1ms / 文件
- 5s 轮询无瓶颈
- 避免缓存与文件不一致

用户偏好双轨：

- 模型选择 → **localStorage**（key 前缀 `a2a-console.model.*`）
- project root → **server `.a2a-console-config.json`**（多浏览器共享）

## 模块边界

- `server/src/routes/`：HTTP 入口，只做 req → service → res；不直接 `fs.read`
- `server/src/services/workspace-reader.ts`：所有 `.ai-agents/workspace` 读取的统一入口
- `server/src/lib/path-guard.ts`：所有路径校验
- `client/src/hooks/`：所有 fetch；`store/`：仅用户偏好；`pages/` 不直接 fetch

## 与 .ai-agents 的耦合

Console 仅依赖：

- `.ai-agents/workspace/active-task.md` frontmatter
- `.ai-agents/workspace/<task-id>/{task,state}.md` frontmatter
- `.ai-agents/workspace/<task-id>/{artifacts,messages,human-reviews,blockers}/**` 文件结构与 frontmatter
- `.ai-agents/agent-cards/model-overrides.md` checklist

所有 schema 与 `.ai-agents/a2a/*.schema.md` 对齐。schema 升级时 Console 优雅降级（未识别字段在 Overview 以 unknown_field 块展示）。
