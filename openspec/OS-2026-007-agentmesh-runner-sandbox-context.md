---
openspec_id: OS-2026-007
title: AgentMesh — Context Pack + Sandbox + Test Runner（自动编程闭环 MVP）
status: draft
source_task: T-2026-006
proposed_a2a_task_id: T-2026-007
owner: zhangxia
created_at: 2026-05-18
schema_version: openspec/v1
---

# OpenSpec: AgentMesh 自动编程闭环 MVP（Phase 2.5 + Phase 3 + Phase 4）

> 来源：T-2026-006 完成「任务包下载 / 我的任务历史 / 普通模式查看」后，AgentMesh 在 OS-2026-006 演进任务包（`planning/AgentMesh_A2A全自动代码编写_多任务并线_Token节省演进任务包_v2.2.md`）外接续推进。本期已自动完成 Phase 0 / 1 / 1.5 / 1.6 / 1.7 / 1.8 / 2 共 7 个阶段的骨架（RunSession、RunPool、TaskQueue、LockManager、ProjectRegistry、Token Ledger + Budget Gate、Policy Engine 建议版），本 OpenSpec 收口为可验收、可回滚的下一轮 A2A 任务：把"看见成本"升级为"节省成本"，把"骨架接口"升级为"沙箱写代码 + 自动测试可运行 demo"。
> 实施范围默认 **仅** `apps/a2a-console/**` + 新增 `.agentmesh/runs/**` 沙箱根目录（gitignore）；**禁止** 改 `a2a_runtime/**`、禁止改既有禁改集（继承 T-2026-002/003/004/006）、禁止改已交付的 Phase 0–2 模块语义；保持 path-guard / file-size-guard / Cursor SDK runner stub 行为不变。

---

## 1. 背景与动机

T-2026-006 + 演进任务包 Phase 0–2 落地后，AgentMesh 已经具备：

1. **多任务管理**：RunSession / RunPool / TaskQueue / LockManager / ProjectRegistry / Token Ledger / Policy Engine 全部端到端通
2. **可观测成本**：每次 Runner 调用可以记录 input/output tokens + cost_usd + 项目/任务/run 维度 summary
3. **风险评分建议**：file-change-plan 路径自动评分为 low/medium/high/critical，给出 AUTO_APPROVE / NEED_HUMAN_REVIEW 等建议

但仍缺 3 块关键能力，导致系统**只能"看见与建议"，不能"主动节省成本 + 实际自动写代码"**：

1. **没有上下文裁剪**：每个 Agent 拿到 Prompt 时，默认仍是全量历史/全量源码 → Token 必然失控（演进 §6.12.4）
2. **没有沙箱**：Developer Agent 真要写代码时只能直接改主项目 → 演进 §15 不要做清单第 6 条 / §6.4 红线
3. **没有测试运行器**：写完代码无法验证 → 自动修复循环（Phase 4）和自动交付（Phase 5）的前提都不成立

本期目标：在 **不接真实 LLM、不引入对象存储、不改 a2a_runtime** 的前提下，把"自动编程闭环 MVP"补齐到**可演示、可量化、可回滚**的程度。

---

## 2. 目标（必须全部达成）

### G1 — Context Pack Builder（Phase 2.5 落地）

- **行为**：按 Agent 阶段生成"最小上下文包"，让每次 Runner 调用不再默认带全量历史。
- **服务端**：新增 `POST /api/a2a/context/build`、`GET /api/a2a/context/:packId`、`GET /api/a2a/context?task_id=&agent=`。
- **裁剪规则**（遵循演进 §6.12.4）：
  - `pm`: requirement + 项目摘要（不含源码全文）
  - `architect`: requirement + file-change-plan 路径列表（仅路径不含全文）
  - `developer`: file-change-plan + 被授权文件路径（不读全文，只列引用）
  - `qa`: file-change-plan + diff（截断 30K）+ fail_log（截断 20K）
  - `fix`: fail_log + diff + 改动文件路径
  - `security`: diff + 高风险路径列表
- **预算门禁**：build 时若 total_estimated_input_tokens 超过演进 §6.12.3 配置 `max_input_tokens_per_run`，自动触发上下文压缩（截断长字段并在 inclusion_reason 注明）。
- **Escape hatch**：`POST /context/build { full_context: true, reason: "..."}` 可跳过裁剪，但 reason 必填（缺失返回 400 + `FULL_CONTEXT_REASON_REQUIRED`）。
- **Console**：专家模式 TaskDetail 在已有"Policy 建议"卡片下方增加"Context 估算"卡片，展示 total_estimated_input_tokens + items 数 + 前 3 条 inclusion_reason；普通模式不显示。
- **非目标**：不实现真实 token 计数（用 length/4 与 Console 现有口径对齐）；不接真实 LLM；不做摘要算法（Artifact Summarizer 留 Phase 2.6）。

### G2 — Sandbox Workspace（Phase 3 落地）

- **行为**：Developer Agent 写代码必须在隔离目录里，产出 patch（diff），由 Console 一键应用到主项目。
- **目录约定**：
  - 沙箱根：`.agentmesh/runs/<run-id>/workspace-copy/`（git ignore）
  - patch 输出：`.agentmesh/runs/<run-id>/patches/<seq>.patch`（unified diff 格式）
  - 日志：`.agentmesh/runs/<run-id>/logs/`
  - 测试结果：`.agentmesh/runs/<run-id>/test-results/`
- **服务端**：新增 `POST /api/a2a/sandbox/init { run_id, project_id, source_files: string[] }`、`GET /api/a2a/sandbox/:runId/diff`、`POST /api/a2a/sandbox/:runId/apply`。
  - `init`：把 source_files（必须在 ProjectRegistry.allowed_paths 内）从 project_root 复制到 sandbox workspace-copy（**复用 path-guard**）。
  - `diff`：对比 workspace-copy 与 project_root 当前内容，返回 unified diff 字符串 + 改动文件列表。
  - `apply`：把 diff 真正应用回 project_root；apply 前必须先调 LockManager.acquire；apply 后写 `.agentmesh/runs/<run-id>/applied.json`（snapshot 元数据）。
- **回滚**：每次 apply 前生成原文件 `.bak`；新增 `POST /api/a2a/sandbox/:runId/rollback` 从 `.bak` 还原。
- **Console**：专家模式 TaskDetail 新增"Sandbox"Tab，展示 diff、改动文件列表、"应用"和"回滚"按钮；普通模式不显示。
- **大小硬上限**：单 patch ≤ 5 MB，单 run sandbox 总大小 ≤ 100 MB；超过返回 `SANDBOX_TOO_LARGE`。
- **非目标**：不做 git-style 三方合并；不做 patch 冲突自动解决（直接拒绝 apply 并返回 `SANDBOX_DIRTY`）；不做远程沙箱（只本地文件系统）。

### G3 — Test Runner（Phase 4 落地骨架）

- **行为**：sandbox apply 前后可触发 `npm run typecheck` / `npm run lint` / `npm run build`，捕获日志、退出码、用时；写入 `.agentmesh/runs/<run-id>/test-results/`。
- **服务端**：新增 `POST /api/a2a/test/run { run_id, project_id, suites: ('typecheck'|'lint'|'build')[] }`、`GET /api/a2a/test/:runId`。
  - 执行通过 `child_process.spawn`（首次引入 child_process **必须** 在 file-change-plan 显式列出 + risk-plan 单独段落证明只用于受信白名单命令）。
  - 命令必须来自项目 `package.json` 的 scripts 字段（不允许任意命令注入）；只接受 suites 枚举里的固定 3 个。
  - 30 秒硬超时；超时返回 exit_code = -1 + `TEST_TIMEOUT`。
- **Console**：Sandbox Tab 新增"测试结果"区，展示 3 个 suite 的 pass/fail/timeout + 用时 + 错误日志前 50 行；普通模式不显示。
- **非目标**：本期不做 Auto Fix Loop（演进 §6.6 Fix Agent 留 OS-2026-008）；不接 jest/playwright（只跑项目 npm script）；不跑 unit test（typecheck/lint/build 三件套已是 MVP 验证）。

### G4 — RunSession 关联升级（贯穿 G1+G2+G3）

- **行为**：RunSession schema 追加 `context_pack_id?`、`sandbox_path?`、`last_test_run_at?`、`last_test_result: 'pass'|'fail'|'timeout'|null` 4 个字段。
- **客户端**：Tasks.tsx 行内徽标在已有 queued/running/paused 基础上叠加：`sandbox_path != null` → 紫色"沙箱中"；`last_test_result==='fail'` → 红色"测试失败"。
- **非目标**：不改 RunSession.status 枚举；不引入新 status 值（保持现有 6 个值的兼容性）。

---

## 3. 非目标（本期不做）

- 不接真实 LLM / Cursor SDK runner / Codex runner（continue 用 stub）。
- 不做 Auto Fix Loop（Phase 4 后半段，留 OS-2026-008）。
- 不做 Reviewer Agent / Security Agent（演进 §6 模块图末端，留 OS-2026-009）。
- 不做 Self-Upgrade Lane / Project Registry 多 root 并行调度（演进 Phase 1.7 已有占位）。
- 不引入对象存储 / 远程 sandbox / 远程 test runner。
- 不改 a2a_runtime/**、不改 .ai-agents/workspace/T-* 之外的 .ai-agents 内容。
- 不改 Phase 0–2 已交付模块的对外契约（schema 字段仅 append，不删改）。
- 不引入新的 npm dependency（除 Architect 评估后 child_process 不够时可论证引入 1 个 diff 库；优先用 Node 内置 `diff` 或简单的 line-based diff）。

---

## 4. 默认禁改集（继承 T-2026-002/003/004/006 并扩展）

- `.github/**`、根 `package.json`、根 `package-lock.json`
- `.ai-agents/agent-cards/**`
- `.ai-agents/workspace/**/state.md`（仅 Controller 推 T-2026-007 自己的 state）
- `a2a_runtime/**`（Python Runtime 本期完全不动）
- `apps/a2a-console/server/src/lib/path-guard.ts`、`file-size-guard.ts`（只读不可改语义；新增 sandbox/test 必须独立实现）
- T-2026-003 拆分后的 contract 6 个 schema 文件 + T-2026-004 的 `project-generator.ts`（仅可在 `index.ts` 追加 re-export）
- T-2026-006 已交付：`server/src/routes/tasks.ts` download handler、`client/src/pages/TaskDetail/OrdinaryView.tsx`
- Phase 0–2 已交付模块（仅可 append 字段，不改既有语义）：
  - contract: `runs.ts`、`projects.ts`、`usage.ts`、`policy.ts`
  - server/store: `run-pool.ts`、`task-queue.ts`、`lock-manager.ts`、`project-registry.ts`、`token-ledger.ts`、`budget-gate.ts`、`risk-scorer.ts`、`policy-engine.ts`、`file-change-plan-parser.ts`
  - server/routes: `runs.ts`、`queue.ts`、`locks.ts`、`projects.ts`、`usage.ts`、`policy.ts`
- `apps/a2a-console/server/src/runner/**`（CursorSdkRunner 仍是 stub，本期不接真实 SDK）
- `apps/generated-projects/**`（不存在，不允许创建）

---

## 5. 验收标准

| ID | 验收点 | 验收方式 |
|---|---|---|
| AC-01 | `POST /context/build agent=pm` 仅含 requirement，不含 file_path items | curl + jq |
| AC-02 | `POST /context/build agent=developer` 含 file_change_plan + 被授权文件路径，不含全文 | curl + jq |
| AC-03 | `POST /context/build` 输入字段 > 50K 自动截断到 ≤30K，inclusion_reason 注明 | curl |
| AC-04 | `POST /context/build { full_context: true }` 无 reason 返回 400 + FULL_CONTEXT_REASON_REQUIRED | curl |
| AC-05 | `POST /sandbox/init` source_files 含 ProjectRegistry.allowed_paths 外的路径 → 400 + PATH_NOT_ALLOWED | curl |
| AC-06 | `POST /sandbox/init` 后修改 workspace-copy，`GET /sandbox/:runId/diff` 返回正确 unified diff | shell + diff |
| AC-07 | `POST /sandbox/:runId/apply` 前 LockManager.acquire 必须成功，否则返回 LOCK_WAITING | curl + 并发 |
| AC-08 | `POST /sandbox/:runId/rollback` 能从 `.bak` 还原原文件 | shell |
| AC-09 | `POST /test/run suites=['typecheck']` 在 a2a-console 项目跑 typecheck，正确捕获 PASS/FAIL + 用时 | curl + 主项目实测 |
| AC-10 | suites 含非枚举值（如 `'rm -rf /'`）返回 400 + INVALID_SUITE | curl |
| AC-11 | RunSession 新字段 typecheck pass；旧 client（不带新字段）仍可正常读取 | tsc + curl |
| AC-12 | Tasks.tsx 普通模式 sandbox_path != null 显示紫色"沙箱中"徽标 | 浏览器手测 |
| AC-13 | 专家模式 TaskDetail "Sandbox" Tab 渲染 diff + 测试结果区；普通模式 OrdinaryView 不显示 | 浏览器双模式手测 |
| AC-14 | T-2026-002/003/004/006 + Phase 0–2 已交付能力零回归（含 download / generator / 中文普通模式 / Policy 建议卡片 / Token Ledger summary） | QA 回归清单全 pass |
| AC-15 | client/server/contract 三端 typecheck 全绿；child_process 引入有 risk-plan 单独章节 | 命令实跑 + 文档 |
| AC-16 | 默认禁改集 scoped git status 全绿；a2a_runtime / Phase 0–2 模块未被修改语义 | scoped diff |
| AC-17 | `.agentmesh/` 目录已加入 `.gitignore`，git status 不含运行态文件 | git check-ignore |

---

## 6. 风险与回滚

| Risk | Mitigation | Rollback |
|---|---|---|
| child_process spawn 注入风险 | suites 严格枚举校验；命令必须来自 package.json scripts；30 秒超时；不允许任意 cwd | revert /test 路由，UI 隐藏测试区 |
| sandbox 大文件复制阻塞 event loop | 单 patch 5 MB / 单 run 100 MB 上限；用 stream 复制 | revert /sandbox 路由 |
| apply 与主项目并发写冲突 | apply 前必须 LockManager.acquire；apply 失败必须 release | revert apply 路由，degrade 到 diff-only 模式 |
| 上下文压缩误删关键信息 | inclusion_reason 必须中文人类可读；high risk 任务自动走 full_context=true（项目 automation_mode='manual' 时） | revert Context Pack Builder，degrade 到 Token Ledger only |
| RunSession 字段追加破坏旧 client | 4 个新字段全部 `.optional()`，contract schema 用 `passthrough()` | revert schema 字段 |
| Test Runner 30 秒超时不够 | 本期固定 30 秒，超时返回 TEST_TIMEOUT，不影响其他流程；后续 OS 可调 | revert /test 路由 |
| Sandbox Tab 与 Policy/Context 卡片互相耦合 | Tab 独立组件 `SandboxTab.tsx`，按 expertMode 路由级别短路 | 删 SandboxTab 引用，全量回退到 6 Tab 视图 |

---

## 7. 实施顺序建议（仅供 Architect / Developer 参考，非强制）

1. **Phase 2.5** — contract `context.ts` + server `context-pack-builder.ts` / `context-pack-store.ts` + 路由 + TaskDetail 卡片
2. **Phase 3.1** — contract `sandbox.ts` + server `sandbox-store.ts`（init/diff/apply/rollback） + LockManager 集成
3. **Phase 3.2** — Console SandboxTab + RunSession schema append `context_pack_id / sandbox_path`
4. **Phase 4.0** — contract `test.ts` + server `test-runner.ts`（child_process 白名单 spawn） + 路由
5. **Phase 4.1** — SandboxTab 接入测试结果区 + RunSession schema append `last_test_result / last_test_run_at`
6. **Phase 4.2** — Tasks.tsx 普通模式徽标叠加（沙箱中 / 测试失败）
7. **文档** — `apps/a2a-console/docs/api.md` / `README.md` 更新

---

## 8. 与既有任务的关系

- 依赖：T-2026-002 / T-2026-003 / T-2026-004 / T-2026-006（任务包下载） + 演进 Phase 0–2 全部已交付。
- 解锁：
  - OS-2026-008：Auto Fix Loop（基于 G3 Test Runner 的失败日志 → Fix Agent 自动修复）
  - OS-2026-009：Reviewer/Security Agent（基于 G2 Sandbox diff 做静态扫描）
  - OS-2026-010：Self-Upgrade Lane（基于 G2 Sandbox 安全升级 AgentMesh 自身）
- 不阻塞：T-2026-005 活力猩猩官网生成等业务任务（本期不动 generator）。
