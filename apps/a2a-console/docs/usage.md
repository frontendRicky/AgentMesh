# Usage Guide

## 1. 启动

```bash
cd apps/a2a-console
npm install
npm run dev
```

`npm run dev` 会并发启动 client（Vite，5173）和 server（Express + tsx watch，5174）。打开 <http://localhost:5173>。

## 2. 配置 project root

首次访问 Dashboard 会提示「无法读取 active task」。点「去设置」（或顶部 sidebar 底部的「设置」），输入任意包含 `.ai-agents/workspace/` 的项目绝对路径，例如：

```
/Users/zhangxia/work/projects/AgentMesh
```

保存后会写入 `apps/a2a-console/.a2a-console-config.json`（不写到任何 `.ai-agents/**` 路径）。

## 3. 浏览群聊（chat-first 主视图）

进入 Dashboard `/`，看到的就是「Agent 群聊」：

- **左 sidebar 6 个头像**：Controller / PM / Architect / Developer / QA / Human。点头像 = 只看该 Agent 的发言，再点一次取消。
- **顶部 mini Timeline**：PM → Architect → Human Review → Developer → QA → Final → Done，绿勾=已过 / 蓝转圈=进行中 / 锁=未到 / 红色=阻塞。
- **气泡**：左头像 + 名称 + 时间 + intent + summary。点气泡 → 弹窗显示完整 markdown。
- **右侧摘要**：状态卡 / 下一步 prompt 关键字（一键复制）/ Context 估算条 / 当前 Blocker。

## 4. 看单个 Task 的细节

`/tasks` 列表 → 点 Task ID 进 `/tasks/:taskId`，7 个 Tab：

| Tab | 内容 |
|---|---|
| 💬 群聊 | 与 Dashboard 一致的消息流，支持 sidebar 过滤 |
| 概览 | task.md（不可变）+ state.md（动态）双卡片 |
| 时间线 | 按 created_at 升序的事件链 |
| Artifacts | 左侧文件树 + 右侧 Markdown 预览（>500KB 自动截断） |
| 风险 / Blocker | 当前 Blocker + Human Review 历史 |
| 指标 | Recharts by_agent / by_stage 双柱图 + Top10 大文件 |
| Model & Prompt | 5 个 Agent 的模型选择（override 锁定时禁选） + 当前阶段关键字 |

## 5. 切 Task

把 active task 切走由 `a2a-agent task use <id>` 在终端执行，Console 不主动切。Console 会在 5s 后轮询到新 active task 并更新 Dashboard。

## 6. Server API（curl 验证）

```bash
curl http://localhost:5174/api/a2a/health | jq
curl http://localhost:5174/api/a2a/active-task | jq
curl http://localhost:5174/api/a2a/tasks | jq
curl http://localhost:5174/api/a2a/tasks/T-2026-002 | jq
curl http://localhost:5174/api/a2a/tasks/T-2026-002/state | jq
curl http://localhost:5174/api/a2a/tasks/T-2026-002/artifacts | jq
curl "http://localhost:5174/api/a2a/tasks/T-2026-002/artifacts/file?path=artifacts/pm/prd.md" | jq
curl http://localhost:5174/api/a2a/tasks/T-2026-002/messages | jq
curl http://localhost:5174/api/a2a/tasks/T-2026-002/blockers | jq
curl http://localhost:5174/api/a2a/tasks/T-2026-002/reviews | jq
curl http://localhost:5174/api/a2a/tasks/T-2026-002/metrics | jq
curl http://localhost:5174/api/a2a/tasks/T-2026-002/prompt-keywords | jq
curl http://localhost:5174/api/a2a/tasks/T-2026-002/model-presets | jq

curl -XPOST http://localhost:5174/api/a2a/config/project-root \
  -H 'content-type: application/json' \
  -d '{"project_root":"/Users/zhangxia/work/projects/AgentMesh"}' | jq
```

## 7. 改轮询间隔

设置页 → 「轮询间隔」改成你想要的毫秒数（最小 1000）。会持久化到 localStorage。

## 8. 复制关键字到 Cursor

Dashboard 右侧 / Task Detail 「Model & Prompt」Tab 显示当前阶段对应的 cli 关键字（如 `prompt developer`）。点「复制」按钮，到 Cursor 粘贴即可继续推 Agent。**Console 永远不会主动调起 Agent。**

## 9. 排查

- **看不到 active task**：去设置页确认 project root；CLI 跑 `a2a-agent task use <id>` 切一下。
- **群聊空**：当前 task 还没有 message 文件；先让某个 Agent 推进一下。
- **Artifact 文件大灯报红**：超过 500KB 已截断为前 100KB，完整内容请直接打开本地文件。
- **server 启动报 PORT 占用**：先 `lsof -ti:5174 | xargs kill -9`。
