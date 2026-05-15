# API Reference

> 全部前缀 `/api/a2a/`。完整契约详见 `.ai-agents/workspace/T-2026-002/artifacts/pm/api-contract-checklist.md`。

## 通用

- 全部 JSON
- 成功：`{ ok: true, data: ... }`
- 失败：`{ ok: false, error: { code, message, details? } }`
- 错误码：`PROJECT_ROOT_MISSING` / `PROJECT_ROOT_INVALID` / `TASK_NOT_FOUND` / `ARTIFACT_NOT_FOUND` / `PARSE_ERROR` / `PATH_TRAVERSAL` / `FILE_TOO_LARGE` / `READONLY_MODE` / `NOT_FOUND`

## 路由清单

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/a2a/active-task` | active-task.md 解析 |
| GET | `/api/a2a/tasks` | 全 task 列表，支持 `?status&agent&priority&q` |
| GET | `/api/a2a/tasks/:taskId` | 单 task 完整 |
| GET | `/api/a2a/tasks/:taskId/state` | 仅 state.md（轮询用） |
| GET | `/api/a2a/tasks/:taskId/artifacts` | 文件树（不带 path）或单文件（带 `?path=`） |
| GET | `/api/a2a/tasks/:taskId/messages` | messages 列表 |
| GET | `/api/a2a/tasks/:taskId/blockers` | blockers + active_blocker / blocked_context |
| GET | `/api/a2a/tasks/:taskId/human-reviews` | review record 列表 |
| GET | `/api/a2a/tasks/:taskId/metrics` | token / context |
| GET | `/api/a2a/tasks/:taskId/prompt-keywords` | 当前阶段 Prompt |
| GET | `/api/a2a/model-presets` | overrides + defaults |
| POST | `/api/a2a/config/project-root` | 写 server config，body: `{project_root}` |

## 不存在的接口（MVP 显式不实现）

- `POST/PUT/DELETE /api/a2a/tasks/:taskId/reviews`
- `POST/PUT/DELETE /api/a2a/state`
- 任何写 `.ai-agents/**` 的接口

→ 路由层不注册，统一 404 NOT_FOUND。
