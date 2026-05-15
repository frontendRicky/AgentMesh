---
openspec_id: OS-2026-003
title: A2A Console — P2 follow-ups（metrics / contract / reviews 路由）
status: draft
source_task: T-2026-002
proposed_a2a_task_id: T-2026-003
owner: zhangxia
created_at: 2026-05-16
schema_version: openspec/v1
---

# OpenSpec: A2A Console P2 follow-ups

> 来源：T-2026-002 `artifacts/qa/test-report.md` 结论段三条 **P2 follow-up**，不阻塞 MVP 收口，建议独立 A2A Task（如 **T-2026-003**）由 Architect 出 `file-change-plan` 后 Developer 实施。  
> 实施范围默认 **仅** `apps/a2a-console/**`；**禁止**写 `.ai-agents/**`、禁止调 LLM、禁止 `child_process`、保持 path-guard / file-size-guard 行为不变。

---

## 1. 背景与动机

Console MVP 已交付；QA 在回归中发现 client 与 server 的 JSON 形态曾手工对齐，长期维护成本高；Metrics Tab 曾按「含 largest_artifacts」设计而后端未输出；Human Review 列表接口路径为 `human-reviews`，与其它资源命名不一致。本 OpenSpec 将三条收口为可验收、可回滚的一轮小改。

---

## 2. 目标（必须全部达成）

### G1 — `GET .../metrics` 增加 `largest_artifacts`（Top N）

- **行为**：在现有 `MetricsResponse` 上扩展字段（**向后兼容**：旧 client 忽略新字段不崩）。
- **定义**：`largest_artifacts: Array<{ path: string; size_bytes: number; tokens_estimate: number }>`，默认 **N=10**，按 `size_bytes` 降序；路径为 **相对 task 根** 的 POSIX 风格（与现有 `messages/*.md`、`artifacts/...` 一致）。
- **范围**：统计对象与 `computeMetrics` 现有逻辑一致——任务目录下参与 token 估算的文件集合（与 `dirCharCount(root)` 或现有 by_stage 聚合所用文件集合对齐，**须在 PRD/tech-plan 写清**，避免与「仅 artifacts」歧义）。
- **性能**：单次请求全量扫描可接受（MVP 任务规模）；若 Architect 要求上限，文档中写明最大扫描文件数或超时策略。

### G2 — Client / Server **契约**单一来源（schema 共享）

- **问题**：client `hooks/use*.ts` 手写类型与 `WorkspaceReader` / route 返回易漂移。
- **目标**：引入 **单一真相**（推荐优先级由高到低，Architect 在 tech-plan 里 **三选一锁定**）：
  1. **推荐**：`apps/a2a-console/packages/contract/`（或 `shared/contract/`）内 **zod schema + `z.infer<>` 类型**，server 在组装 JSON 前 `safeParse`，client `apiGet` 后 `safeParse`；失败返回统一 `VALIDATION_ERROR`（或沿用现有 envelope 的 `ok:false`）。
  2. **可选**：从 Express 路由生成 OpenAPI + 生成 TS client（更重，需额外依赖与 CI）。
  3. **最低**：仅共享 **TypeScript 类型** 包（无 runtime 校验）——**仅当** Architect 明确拒绝 zod 时采用，并在 risk-plan 写明技术债。
- **覆盖范围（MVP）**：至少覆盖 **Envelope** `{ ok, data?, error? }` + 下列端点之一组完整链路：`/tasks/:id`、`/tasks/:id/messages`、`/tasks/:id/metrics`、`/tasks/:id/human-reviews`（或 G3 更名后路径）、`/api/a2a/model-presets`。其余端点可列「Phase 2」表格。

### G3 — Human Review 路由命名统一

- **现状**：`GET /api/a2a/tasks/:taskId/human-reviews`
- **目标**：对外主路径为 **`GET /api/a2a/tasks/:taskId/reviews`**（与 `messages` / `blockers` 等资源名风格一致）。
- **兼容**：**必须**在至少 **一个版本周期** 内保留旧路径（实现方式二选一，Architect 锁定）：
  - **A**：`human-reviews` 与 `reviews` 双注册，同 handler；`docs/api.md` 标明 `human-reviews` **deprecated**，计划移除版本号；或
  - **B**：仅 `reviews`，`human-reviews` 301/308 到 `reviews`（若 Express 层不便，则用同 handler 双 route）。
- **Client**：只调用新路径 `reviews`；若有 e2e/手工清单，更新 curl 示例。

---

## 3. 非目标（本期不做）

- 不写 `state.md` / 不写 review record / 不执行 `a2a-agent`。
- 不引入 WebSocket / chokidar；轮询策略不变。
- 不改为真实 tokenizer；`tokens_estimate` 仍为 chars/3.5（除非另开 task）。
- 不调整 Dashboard chat-first 产品形态（除非 G1 展示需要极小 UI 改动）。

---

## 4. 接口与类型（摘要）

### 4.1 `GET /api/a2a/tasks/:taskId/metrics`（扩展）

响应 `data` 在现有字段基础上增加：

```json
{
  "tokens": { "total_estimate": 0, "by_agent": {}, "by_stage": {} },
  "context": { "active_chars": 0, "active_tokens_estimate": 0, "model": null, "model_max_context": 0, "usage_pct": 0, "level": "safe" },
  "largest_artifacts": [
    { "path": "artifacts/pm/prd.md", "size_bytes": 19908, "tokens_estimate": 5689 }
  ]
}
```

（字段名以 Architect `tech-plan` / `api.md` 为准；此处为 OpenSpec 建议名。）

### 4.2 `GET /api/a2a/tasks/:taskId/reviews`

- 语义与现 `human-reviews` 完全一致：`{ items: ReviewItem[] }`。
- `ReviewItem` 形状不变；`file_path` 仍为相对 task 目录路径。

---

## 5. 验收标准（QA 可执行）

| ID | 描述 |
|----|------|
| AC-01 | `GET .../metrics` 返回含 `largest_artifacts`，长度 ≤10，降序，路径均在 task 目录内且经 path-guard 同类校验 |
| AC-02 | 旧路径 `.../human-reviews` 仍可用或在文档声明的兼容期内可用；新路径 `.../reviews` 200 且 body 一致 |
| AC-03 | client `npm run typecheck` 通过；contract 包被 client/server 引用无循环依赖 |
| AC-04 | server `npm run typecheck` 通过；关键响应经 zod（若采用 G2-1）safeParse，非法结构不崩溃并返回明确 error code |
| AC-05 | `docs/api.md` + `apps/a2a-console/README.md` 中 curl 示例更新 |
| AC-06 | 路径遍历用例（至少 3 个 payload）对 **新/改** 路由无回归 |
| AC-07 | grep：`child_process` / 写 `.ai-agents` 仍为 0 |

---

## 6. 风险与缓解

| 风险 | 缓解 |
|------|------|
| largest 扫描大仓库慢 | 限制 N、或仅扫描 `artifacts/**` + `messages/**`（与 tech-plan 一致） |
| zod 与 gray-matter 日期类型 | 延续 T-2026-002 的 `toIsoString` 策略；schema 用 `z.union([z.string(), z.date()]).transform(...)` 等 |
| 双路由遗漏测试 | QA checklist 显式两条 curl |

---

## 7. 依赖 A2A 流程的交付物（由对应 Agent 产出）

| 阶段 | 产物 |
|------|------|
| PM | `requirement.md`（可薄：本 OpenSpec 引用 + 用户故事） / `prd.md` |
| Architect | `tech-plan.md`（锁定 G2 三选一）/ `file-change-plan.md` / `risk-plan.md` |
| Developer | 代码 + `implementation-log.md` / `changed-files.md` |
| QA | `test-report.md` / `acceptance-checklist.md` |

---

## 8. Codex / 外部执行者输入

将「附录 A：Codex Prompt」整段复制给 Codex；其 **不** 代替 A2A 状态机写 `state.md`，仅作实现参考；**实际合码与门禁**仍以 Cursor + A2A Developer 为准。

---

## 附录 A：Codex Prompt（复制区开始）

```text
你是 Developer，在仓库 AgentMesh 中实现 OpenSpec OS-2026-003（文件：openspec/OS-2026-003-a2a-console-p2-followups.md）。只改 apps/a2a-console/** 与必要文档（同目录下 docs/api.md、README.md），禁止写 .ai-agents/**、禁止 child_process、禁止调用 LLM。

必做三件事（验收见该 OpenSpec §5）：
1) metrics：扩展 GET /api/a2a/tasks/:taskId/metrics 的 data，增加 largest_artifacts（Top 10，按 size 降序，path 相对 task 根），向后兼容。
2) contract：按 OpenSpec G2 在 tech-plan 中选定的方案实现 client/server 共享校验（优先 zod 共享包）；至少覆盖 envelope + messages + metrics + reviews + model-presets。
3) reviews：新增 GET /api/a2a/tasks/:taskId/reviews，与现 human-reviews 同语义；保留 human-reviews 兼容（双 route 或 redirect），更新 client 只调 reviews；更新文档 curl。

交付：两包 npm run typecheck 通过；简述你改了哪些文件；列出 3 条 curl 自测命令。
```

**复制区结束**

---

## 9. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| draft | 2026-05-16 | 初稿，对应 T-2026-002 QA P2 三条 |
