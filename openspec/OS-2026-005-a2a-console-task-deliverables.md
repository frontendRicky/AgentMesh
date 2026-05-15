---
openspec_id: OS-2026-005
title: A2A Console — 任务结果交付层（任务包下载 / 我的任务历史 / 普通模式查看）
status: draft
source_task: T-2026-004
proposed_a2a_task_id: T-2026-006
owner: zhangxia
created_at: 2026-05-15
schema_version: openspec/v1
---

# OpenSpec: A2A Console 任务结果交付层

> 来源：T-2026-004 完成「中文普通模式 + 项目生成向导」后，向导只把任务包写到 `.ai-agents/workspace/T-YYYY-NNN/`，并提示「交给技术同事在 Cursor/Codex 继续」。**用户拿不到任务包本身，普通模式也没有「我跑过的任务」入口**，导致非技术用户跑完一次就找不到结果。本 OpenSpec 收口为可验收、可回滚的一轮小改。
> 实施范围默认 **仅** `apps/a2a-console/**`；**禁止** 写 `.ai-agents/**`、禁止调 LLM、禁止 `child_process`、保持 path-guard / file-size-guard 行为不变；T-2026-003 拆分的 `packages/contract` schema 结构与 T-2026-004 已交付的 generator route/service/UI 均纳入禁改集。

---

## 1. 背景与动机

T-2026-004 上线后，普通模式用户的真实使用闭环只有一半：

1. 在 `/generator` 描述需求 → 生成任务包 → 跳到「任务包已创建」结果页 ✅
2. 想再下载任务包 / 想看上次跑过哪些任务 / 想把任务包发给技术同事 → ❌

当前唯一的入口是让用户**手动去 `.ai-agents/workspace/T-YYYY-NNN/` 找文件夹**，对非技术用户不可接受。

本期目标：在 **不引入对象存储、不引入鉴权、不做"重跑"** 的前提下，把「跑出来的东西怎么拿走 / 怎么再回头看」补齐到可交付水平。

---

## 2. 目标（必须全部达成）

### G1 — 任务包 zip 下载

- **行为**：在结果页 `/generator/tasks/:taskId` 与「我的任务」详情页提供 **「下载任务包 (.zip)」** 主操作按钮。
- **服务端**：新增 `GET /api/a2a/tasks/:taskId/download` 走 `Content-Disposition: attachment; filename="<taskId>.zip"`，**流式打包** `.ai-agents/workspace/T-YYYY-NNN/` 整个目录。
  - 必须复用 T-2026-002 的 `path-guard.ts`，禁止跳出 task root；禁止打包符号链接指向 task root 之外的内容。
  - taskId 校验沿用 `^T-\d{4}-\d{3}$`；不存在返回 envelope `ok:false` + `code: TASK_NOT_FOUND`。
  - **大小硬上限 50 MB**，超过返回 `ok:false` + `code: TASK_PACKAGE_TOO_LARGE`，message 含建议（直接打开仓库目录拷贝）。
  - 不做 zip 缓存；每次请求即时打包。
- **客户端**：按钮点击触发浏览器下载；下载中按钮 disabled + 中文 loading 文案；失败显示中文错误 toast 并保留可重试。
- **非目标**：不引入签名 URL / 不做下载次数统计 / 不做断点续传。

### G2 — 「我的任务」历史列表升级

- **行为**：普通模式 sidebar 的「我的任务」从当前列表（仅显示标题/状态）扩展为带操作的任务历史。
- **列**：任务编号、中文标题、状态（中文化：已完成 / 进行中 / 失败 / 已阻塞）、更新时间、操作（**查看 / 下载**）。
- **数据源**：复用现有 `GET /api/a2a/tasks` 列表接口；如缺更新时间字段，由 server 在原 response 上**追加**字段（不破坏现有 client）。
- **空状态**：列表为空时显示中文引导卡，主操作链到 `/generator`（"去生成第一个任务包"）。
- **专家模式**：完全不动；专家模式 Tasks 页继续使用 T-2026-002/003 既有列。
- **非目标**：不做搜索 / 不做筛选 / 不做分页（任务量超过 50 条时再开 follow-up，本期固定显示最近 50 条）。

### G3 — 普通模式任务详情页（精简视图）

（继续看下一节后再读 G4）



- **行为**：从「我的任务」点「查看」进入 `/tasks/:taskId`：
  - 普通模式：渲染**精简视图**（中文摘要、当前阶段、关键产物链接、下载按钮、"如何继续"指引）。
  - 专家模式：保持 T-2026-002/003 已交付的完整详情页（Chat / Timeline / Artifacts / Metrics / Risk / ModelPrompt 各 Tab）零回归。
- **路由**：复用既有 `/tasks/:taskId`，按 `expertMode` 做条件渲染，不新建路由。
- **精简视图来源**：复用既有 task-detail / messages / metrics 接口，**不新增**接口（除 G1 download 外）。
- **非目标**：不做产物 inline 编辑 / 不做评论 / 不做 share link。

---

### G4 — 顺手修复 `/api/a2a/config/project-root` 404（搭车清理）

- **来源**：T-2026-003 QA 报告 §4 Observation。客户端 `useProjectRoot()` 调用了 `GET /api/a2a/config/project-root`，server 没有这个路由，浏览器 console 报 404 资源错误（不阻塞功能）。
- **行为**：二选一，由 Architect 在 tech-plan 锁定：
  - **A**：server 端补一个只读的 `GET /api/a2a/config/project-root`，返回 envelope `{ ok:true, data:{ project_root } }`，复用现有 server 内部 `getProjectRoot()`。
  - **B**：client 端改 `useProjectRoot()` 调用至已存在的 server 路径（如 `/api/a2a/config`），并对应缩窄 schema。
- **范围**：必须有 contract zod schema；server 实现复用 envelope helper；不引入鉴权 / 不引入写操作。
- **验收**：浏览器 console 不再有该 404 资源消息；普通/专家模式各跑一次首屏验证。
- **非目标**：不做 project_root 切换 UI；不做多 project 支持。

---

## 3. 非目标（本期不做）

- 不做对象存储 / 签名 URL / 鉴权 / 公开分享链接。
- 不做 zip 缓存 / 不做下载历史 / 不做次数限制。
- 不做"再次跑生成器" / 不做基于历史任务 fork 新任务。
- 不做产物在线编辑、评论、协作。
- 不做邮件 / IM 通知。
- 不改 T-2026-002/003/004 任何已交付 route/service/UI 的语义；仅可对「我的任务」列表 response 做**字段追加**，不删改。
- 不引入 child_process；zip 必须用 Node 内库（`zlib` / `archiver` 等纯 JS 方案；如需新 dep，由 Architect 在 tech-plan 锁定并在 file-change-plan 显式列出）。

---

## 4. 默认禁改集（继承 T-2026-002/003/004）

- `.github/**`、根 `package.json`、根 `package-lock.json`
- `.ai-agents/agent-cards/**`
- `.ai-agents/workspace/**/state.md`（仅 Controller 推 T-2026-006 自己的 state）
- `apps/a2a-console/server/src/lib/path-guard.ts`、`file-size-guard.ts`（只读不可改语义；本期需要新增 zip 大小判断时**不得**改这两个文件，应在新 download handler 里独立实现）
- T-2026-003 拆分后的 `apps/a2a-console/packages/contract/src/{envelope,tasks,messages,metrics,reviews,model-presets}.ts` 与 T-2026-004 的 `project-generator.ts`：仅可在 `index.ts` re-export 处追加新 schema 导出，**不得**改既有 schema 字段。
- T-2026-004 已交付：`server/src/routes/project-generator.ts`、`server/src/services/project-generator*.ts`、`client/src/pages/Generator.tsx`、`client/src/hooks/useProjectGenerator.ts`、`client/src/store/settingsStore.ts`（expertMode 行为）。
- `apps/generated-projects/**`（不存在，不允许创建）。

---

## 5. 验收标准

| ID | 验收点 | 验收方式 |
|---|---|---|
| AC-01 | 结果页「下载任务包 (.zip)」按钮可见且可点击 | 浏览器手测 |
| AC-02 | 下载得到的 zip 解压后内容与 `.ai-agents/workspace/T-YYYY-NNN/` 一致（文件数 / 大小逐文件比对） | QA 手测 + diff |
| AC-03 | 50 MB 上限触发时返回 `TASK_PACKAGE_TOO_LARGE`，UI 显示中文错误而不是 500 | 构造大文件 / mock |
| AC-04 | 路径穿越攻击不可绕过：`taskId=../../etc` 等 payload 走 `path-guard` 返回 `PATH_TRAVERSAL` | curl |
| AC-05 | 不存在的 taskId 返回 `TASK_NOT_FOUND` 且不泄漏文件系统信息 | curl |
| AC-06 | 「我的任务」列表显示中文状态 / 时间 / 下载按钮，空状态有中文引导卡 | 浏览器手测 |
| AC-07 | 普通模式 `/tasks/:taskId` 渲染精简视图；专家模式仍是完整 6 Tab 视图 | 浏览器双模式手测 |
| AC-08 | T-2026-002/003/004 已交付能力零回归（含 generator 主流程、专家 Dashboard、metrics largest_artifacts、reviews 双路径、generator 创建任务包） | QA 回归清单全 pass |
| AC-09 | client/server/contract 三端 typecheck 全绿；新增 download 接口在 contract 包有 zod schema | 命令实跑 |
| AC-10 | 6 条默认禁改集 scoped git status 全绿 | scoped diff |
| AC-11 | 浏览器 console 不再出现 `GET /api/a2a/config/project-root` 404 资源消息（G4） | 浏览器普通/专家双模式首屏 |

---

## 6. 风险与回滚

| Risk | Mitigation | Rollback |
|---|---|---|
| zip 流式打包大文件阻塞 event loop | 用 `archiver` stream pipe，不在内存中拼整个 buffer；50 MB 硬上限 | 直接 disable download 路由，UI 隐藏按钮，degrade 到 T-2026-004 旧体验 |
| `archiver` 引入新依赖 | Architect 在 tech-plan 显式锁定版本；优先评估 Node 内置 `zlib` 是否够用 | 降级为生成 tar.gz 用内置 zlib 或干脆只生成 task root 路径让用户自己拷贝 |
| 「我的任务」列表 response 字段追加破坏旧 client | 字段必须可选 / 默认 nullable；contract schema 用 `z.object({...}).passthrough()` 或在新字段标 `.optional()` | revert response 字段 |
| 普通模式 `/tasks/:taskId` 精简视图与专家模式条件分支耦合 | 拆独立 `OrdinaryTaskDetail.tsx` 组件，按 `expertMode` 路由级别短路 | 删 OrdinaryTaskDetail 引用，全量回退到既有详情页 |

---

## 7. 实施顺序建议（仅供 Architect / Developer 参考，非强制）

1. server 端 `GET /tasks/:taskId/download`（含 contract schema、path-guard、大小上限、错误码）
2. contract 包 `tasks.ts` 追加 `taskListItemSchema` 时间字段（可选 nullable）
3. client `useTaskList` 兼容追加字段
4. `Tasks.tsx` 普通模式列表升级
5. `OrdinaryTaskDetail.tsx` 新建 + 路由按 expertMode 分发
6. 结果页 `/generator/tasks/:taskId` 接入下载按钮
7. 文档 `apps/a2a-console/docs/api.md` / `README.md` 更新

---

## 8. 与既有任务的关系

- 依赖：T-2026-002（path-guard）、T-2026-003（contract 拆分 + reviews 路由统一）、T-2026-004（generator + 普通模式 + expertMode store）。**必须** 在 T-2026-003 done 之后再启动本任务，避免 contract schema 双方向冲突。
- 解锁：T-2026-005（活力猩猩官网生成）跑出来后用户能用 G1 把任务包真正下载下来，构成完整闭环。
