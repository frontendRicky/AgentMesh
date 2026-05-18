# API Reference

> 全部前缀 `/api/a2a/`。关键响应契约以 `packages/contract` 的 zod schema 为单一真相；server 返回前校验，client `apiGet` 后校验。
> OS-2026-003 MVP 覆盖：Envelope、`GET /tasks/:taskId`、messages、metrics、reviews、model-presets。

## 通用

- 全部 JSON
- 成功：`{ ok: true, data: ... }`
- 失败：`{ ok: false, error: { code, message, details? } }`
- 错误码：`PROJECT_ROOT_MISSING` / `PROJECT_ROOT_INVALID` / `TASK_NOT_FOUND` / `ARTIFACT_NOT_FOUND` / `PARSE_ERROR` / `PATH_TRAVERSAL` / `FILE_TOO_LARGE` / `READONLY_MODE` / `VALIDATION_ERROR` / `NOT_FOUND`
- Project Generator 额外错误码：`REQUEST_VALIDATION_FAILED` / `DRAFT_ID_INVALID` / `DRAFT_NOT_FOUND` / `TASK_SLUG_INVALID` / `TASK_ID_CONFLICT` / `PROJECT_GENERATOR_WRITE_FAILED`

## 路由清单

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/a2a/active-task` | active-task.md 解析 |
| GET | `/api/a2a/tasks` | 全 task 列表，支持 `?status&agent&priority&q` |
| GET | `/api/a2a/tasks/:taskId` | 单 task 完整 |
| GET | `/api/a2a/tasks/:taskId/state` | 仅 state.md（轮询用） |
| GET | `/api/a2a/tasks/:taskId/download` | 下载任务包 .zip（STORE 方式，50 MB 上限） |
| GET | `/api/a2a/tasks/:taskId/artifacts` | 文件树（不带 path）或单文件（带 `?path=`） |
| GET | `/api/a2a/tasks/:taskId/messages` | messages 列表 |
| GET | `/api/a2a/tasks/:taskId/blockers` | blockers + active_blocker / blocked_context |
| GET | `/api/a2a/tasks/:taskId/reviews` | review record 列表 |
| GET | `/api/a2a/tasks/:taskId/human-reviews` | deprecated，兼容期内等价于 `/reviews` |
| GET | `/api/a2a/tasks/:taskId/metrics` | token / context / largest_artifacts |
| GET | `/api/a2a/tasks/:taskId/prompt-keywords` | 当前阶段 Prompt |
| GET | `/api/a2a/model-presets` | overrides + defaults |
| GET | `/api/a2a/project-generator/templates` | 普通模式项目类型模板 |
| POST | `/api/a2a/project-generator/drafts` | 根据中文需求整理预览，不写文件 |
| POST | `/api/a2a/project-generator/drafts/:draftId/tasks` | 创建新的 `.ai-agents/workspace/T-YYYY-NNN/` 任务包 |
| GET | `/api/a2a/config/project-root` | 读取 project_root（无鉴权，只读） |
| POST | `/api/a2a/config/project-root` | 写 server config，body: `{project_root}` |
| POST | `/api/a2a/context/build` | 生成 Context Pack（支持 `full_context` reason gate） |
| GET | `/api/a2a/context/:packId` | 读取单个 Context Pack |
| GET | `/api/a2a/context?task_id=&agent=` | 查询 Context Pack 列表 |
| POST | `/api/a2a/sandbox/init` | 初始化本地 sandbox workspace-copy |
| GET | `/api/a2a/sandbox/:runId/diff` | 读取 sandbox unified diff |
| POST | `/api/a2a/sandbox/:runId/apply` | 应用 sandbox diff 到主项目（写回前加锁和 .bak） |
| POST | `/api/a2a/sandbox/:runId/rollback` | 从 .bak 回滚已应用文件 |
| POST | `/api/a2a/test/run` | 执行受限 test suite：typecheck / lint / build |
| GET | `/api/a2a/test/:runId?project_id=` | 读取最近 test result |

## Project Generator

`GET /api/a2a/project-generator/templates`:

```json
{
  "ok": true,
  "data": {
    "items": [
      {
        "id": "business-dashboard",
        "name": "经营看板",
        "description": "适合展示销售、订单、客户、库存、财务等关键指标。",
        "examples": ["销售日报"],
        "recommended_strategy": "quality"
      }
    ]
  }
}
```

`POST /api/a2a/project-generator/drafts` body 不接受 `task_id`：

```json
{
  "project_name": "门店销售看板",
  "project_type": "business-dashboard",
  "business_description": "查看各门店每日销售额、热卖商品和库存提醒。",
  "target_users": "店长和运营同事",
  "pages": ["首页", "门店列表", "商品详情"],
  "style_preference": "清爽、数字醒目",
  "data_source": "先用示例数据",
  "generation_strategy": "quality",
  "model_profile": "recommended",
  "api_mode": "mock",
  "needs_auth": false,
  "needs_charts": true
}
```

`POST /api/a2a/project-generator/drafts/:draftId/tasks` body:

```json
{ "slug": "store-sales-dashboard" }
```

返回：

```json
{
  "ok": true,
  "data": {
    "task_id": "T-2026-005",
    "task_path": ".ai-agents/workspace/T-2026-005",
    "created_files": ["task.md", "state.md"],
    "model_snapshot_path": "artifacts/pm/model-selection-snapshot.md",
    "next_step": "handoff_to_technical_owner"
  }
}
```

约束：

- `task_id` 由 server 扫 `.ai-agents/workspace/T-YYYY-*` 后自增分配，年份取系统当前年。
- `slug` 必须匹配 `^[a-z0-9-]{1,40}$`。
- 同名 `task_id` 已存在返回 `TASK_ID_CONFLICT`，不覆盖、不自动追加后缀。
- 本期不注册 runner/start/job 路由；contract 只保留 schema 占位。

## Metrics

`GET /api/a2a/tasks/:taskId/metrics` 的 `data`:

```json
{
  "tokens": { "total_estimate": 0, "by_agent": {}, "by_stage": {} },
  "context": {
    "active_chars": 0,
    "active_tokens_estimate": 0,
    "model": "gpt-5.5",
    "model_max_context": 200000,
    "usage_pct": 0,
    "level": "safe"
  },
  "largest_artifacts": [
    {
      "path": "artifacts/pm/prd.md",
      "size_bytes": 19908,
      "tokens_estimate": 5689
    }
  ]
}
```

`largest_artifacts` 最多 10 条，按 `size_bytes` 降序；扫描集合与当前 `computeMetrics` 的 `dirCharCount(taskRoot)` 保持一致，路径为 task 根目录相对路径。

## Reviews

主路径：

```bash
curl -s "http://localhost:5174/api/a2a/tasks/T-2026-003/reviews"
```

旧路径仍可用但 deprecated：

```bash
curl -s "http://localhost:5174/api/a2a/tasks/T-2026-003/human-reviews"
```

两者返回相同形态：

```json
{ "ok": true, "data": { "items": [] } }
```

## Curl 自测

```bash
curl -s "http://localhost:5174/api/a2a/tasks/T-2026-003/metrics" | jq '.data.largest_artifacts'
curl -s "http://localhost:5174/api/a2a/tasks/T-2026-003/reviews"
curl -s "http://localhost:5174/api/a2a/tasks/T-2026-003/human-reviews"
curl -OJ "http://localhost:5174/api/a2a/tasks/T-2026-003/download"
curl -s -X POST "http://localhost:5174/api/a2a/context/build" \
  -H "content-type: application/json" \
  -d '{"task_id":"T-2026-007","agent":"developer"}'
curl -s -X POST "http://localhost:5174/api/a2a/test/run" \
  -H "content-type: application/json" \
  -d '{"run_id":"R-demo","project_id":"self-upgrade","suites":["typecheck"]}'
```

## 不存在的接口（MVP 显式不实现）

- `POST/PUT/DELETE /api/a2a/tasks/:taskId/reviews`
- `POST/PUT/DELETE /api/a2a/state`
- 任何修改既有 task state 或写 `apps/generated-projects/` 的接口
- 任何 project-generator runner/start/job 执行接口

→ 路由层不注册，统一 404 NOT_FOUND。
