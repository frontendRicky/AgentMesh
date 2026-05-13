---
artifact_id: A-T-2026-001-risk-plan
task_id: T-2026-001
artifact_type: risk_plan
produced_by: architect
consumed_by:
  - developer
  - qa
  - human
file_path: artifacts/architect/risk-plan.md
version: 1
status: ready
summary: 12 条风险（P0 2 / P1 8 / P2 2），按归属（frontend / backend / cross-domain）分组；每条含触发条件、缓解、回滚；6 条需 Human Review 拍板。
dependencies:
  - A-T-2026-001-tech-plan
  - A-T-2026-001-file-change-plan
validation_result: pending
created_at: 2026-05-13T16:30:00+08:00
schema_version: a2a/v1
---

# Risk Plan: 平台管理 + 批量简历上传前端联调

> 风险等级：**P0** = 阻塞联调 / 用户体验严重受损；**P1** = 影响某条链路；**P2** = 长期治理。
> 归属：**frontend** = 前端可独立处理；**backend** = 仅后端处理；**cross-domain** = 前后端协同。

## 1. P0 风险

### R-01【P0 / backend】AI 成功回调后端 JSONB 写入失败

- 触发条件：测试报告"失败项日志证据"。`column "highlights" is of type jsonb but expression is of type character varying`。AI 外部回调 200，但 hire 写主表失败。
- 影响：成功回调路径无法落 `talent_resume`；`analysis_status` 卡在 1；平台管理列表不增。
- 前端能做：
  - 不补偿后端 bug；
  - 列表行 `analysisStatus === 1` 持续 > 5 分钟时，UI Tooltip 提示"AI 处理较慢，请稍后刷新"；
  - 不主动重发 analyze；
- 回滚：无需前端回滚；后端配 MyBatis JSONB TypeHandler 或 SQL cast 即可恢复。
- Human Review 拍板：5 分钟阈值与 Tooltip 文案。

### R-02【P0 / cross-domain】AI 提交接口当前 SKIP

- 触发条件：测试报告 §14。AI 服务接收任务接口未提供，`/talent/resume/analyze` 触发链路无法端到端验证。
- 影响：用户在 dev 触发分析后立即进入"分析中"，无后续 AI 回调来源；功能链路无法端到端 demo。
- 前端能做：
  - **不引入 dev mock**（Architect 推荐路径，避免污染 service / hook / 类型层与 prod 排除复杂度）；
  - QA 用"邮箱为空回调"（AI 内部回调，已通过）验证状态切换；
  - 用户体验：dev 环境表现"分析中"为长期态，PM/UX 接受此现象作为已知现象。
- 备选方案：若 Human Review 决定要 mock，提交方式 = 单独 `services/buser/resumeUpload/devMock.ts` + env `NEXT_PUBLIC_ENABLE_AI_MOCK=1`，prod 构建时 tree-shake；**会扩大 file-change-plan 与 owner: user-approved**。
- 回滚：本期不引入 mock；后端 analyze 上线后零代码联通。
- Human Review 拍板：是否允许 dev mock。

## 2. P1 风险

### R-03【P1 / frontend】数字字段 string/number 混用

- 触发条件：测试报告大量返回。分页 string、`fileSize / matchScore` 混用、`inviteCount` 等。
- 影响：前端 `Number(...)` 直接调用易产生 NaN；列表渲染或分页计算错误。
- 前端缓解：
  - DTO 用 `number | string | null` 联合类型；
  - mapper 内统一 normalize：分页 → number、ID → string、fileSize → string label + 保留 number、matchScore → number 兜底 null；
  - 组件**直接消费** ViewModel，不再 normalize。
- 回滚：mapper 单点收敛，回滚改 normalize 函数即可。
- Human Review 拍板：不需要（属技术规范）。

### R-04【P1 / frontend】confirm 失败重试

- 触发条件：PUT 成功 / confirm 网络中断或瞬时业务错误。
- 影响：用户已直传 COS 成功但前端不知道；若误重申 presign 会产生孤儿 COS 对象 + 多余明细。
- 前端缓解：
  - hook 层 utility `retryConfirm(uploadItemId, ctx)`，最多 3 次，1s / 2s / 4s 退避；
  - confirm 接口幂等（PRD §2.7），同 `uploadItemId + cosKey` 重试安全；
  - 仍失败 → toast"上传完成但确认失败"+ 行内"重试 confirm"手动入口；
  - 不重发 PUT，不重申 presign；
- 回滚：关闭重试 utility，回退至单次 confirm + 手动重试按钮。
- Human Review 拍板：3 次 + 1s/2s/4s 阈值是否可接受。

### R-05【P1 / frontend】presign 过期

- 触发条件：用户停顿 > 10 分钟，PUT COS 失败（签名过期 403/SignatureDoesNotMatch）。
- 影响：上传失败；用户困惑。
- 前端缓解：
  - 首次 PUT 失败 → 自动**对同一文件重新 presign + PUT**（最多 1 次）；
  - 仍失败 → toast "请重试上传"，保留前端瞬时态可手动重试；
  - 重新 presign 会产生新 `uploadItemId` + `cosKey`，旧明细由后端清理任务处理；
- 回滚：关闭自动重试，回退为"PUT 失败 → 提示用户重试"纯手动。
- Human Review 拍板：是否允许自动重试 presign 1 次。

### R-06【P1 / frontend】大文件上传进度

- 触发条件：单文件 ≤ 10MB（前端硬上限），用 axios `onUploadProgress` 展示进度。
- 影响：网络抖动时进度可能不平滑；用户取消时 abort 需正确清理。
- 前端缓解：
  - 单文件 ≤ 10MB，axios `onUploadProgress` 足够；
  - 用户主动取消 → `AbortController.abort()`，组件瞬时态进入"已取消"，允许重试；
  - 不引入 COS SDK / tus；
- 回滚：关闭 onUploadProgress 监听，仅展示"上传中 / 已完成"两态。
- Human Review 拍板：不需要。

### R-07【P1 / business】邀请次数 3 次限制

- 触发条件：PRD §6.6，`inviteCount` 跨撤回累计。
- 影响：HR 误以为撤回后还能再发。
- 前端缓解：
  - 邀请按钮始终展示 `inviteCount/maxInviteCount`（如 `1/3`）；
  - `inviteCount >= 3` 时按钮 disabled + tooltip "邀请次数已达上限"；
  - 撤回 toast 文案明示"已撤回，剩余 X 次"；
  - 后端兜底 `INVITE_COUNT_EXCEEDED`。
- 回滚：移除 disabled 与 tooltip 文案；后端仍兜底。
- Human Review 拍板：不需要。

### R-08【P1 / business】已注册不可撤回 / 重发

- 触发条件：`inviteStatus = 2 已注册`。
- 影响：HR 误点撤回 / 重发，看到统一业务错误 toast。
- 前端缓解：
  - 操作矩阵层面 canRecall / canResend 直接返回 false；
  - 按钮不渲染（隐藏）；
  - 后端兜底 `INVITE_ALREADY_REGISTERED`。
- 回滚：撤回 / 重发按钮逻辑改回不判断 inviteStatus。
- Human Review 拍板：不需要。

### R-09【P1 / frontend】职位绑定与分析的强依赖

- 触发条件：PRD §3.3，未绑定职位的明细点击"分析"被后端拒绝。
- 影响：用户体验差。
- 前端缓解：
  - canAnalyze = `(0||2) && jobId != null`；
  - 多选批量分析时，过滤未绑定行，modal 内明示"X 条因未绑定职位将跳过"；
  - "重新分析"同规则；
- 回滚：移除前端拦截，直接调 service，由后端拒绝。
- Human Review 拍板：不需要。

### R-10【P1 / cross-domain】邮箱为空失败

- 触发条件：AI 回调 `email=""`（已通过测试 §16）。
- 影响：候选人无法进入平台管理。
- 前端缓解：
  - 上传明细"分析失败"子 Tab 展示 `failureReason="邮箱为空"`；
  - 不提供"补填邮箱后重试"功能；
  - 引导文案：上传明细列删除该行后重新上传含邮箱版本。
- 回滚：无前端回滚需求。
- Human Review 拍板：不需要。

## 3. P2 风险

### R-11【P2 / cross-domain】邮件到达需人工确认

- 触发条件：测试报告"邀请邮件链路"项 = "需人工确认收件箱"。
- 影响：HR 误以为"邮件已发送 = 已送达"。
- 前端缓解：
  - 邀请 / 重发成功 toast 文案明示"邀请邮件已提交发送，候选人可能需要几分钟才能收到"；
  - 不实现邮件投递追踪（本期不做）。
- 回滚：toast 文案改回"邀请已发送"。
- Human Review 拍板：toast 文案最终版本。

### R-12【P2 / process】task.md 标题与实际需求不一致

- 触发条件：T-2026-001 task.md 标题仍为占位 "Pilot task"。
- 影响：审计 / 后续 task 复盘时标题与产出不匹配。
- 前端缓解：
  - 已记录到 PM OQ-05 与 from-pm-001-handoff payload；
  - Architect 不阻塞；不要求 Controller 立即处理；
  - Controller 可在 Human Review 推进前发 message 锁定 task slot 关系。
- 回滚：不涉及代码。
- Human Review 拍板：不需要（属流程治理，不阻塞实施）。

## 4. 风险归属汇总

| # | 风险 | 等级 | 归属 |
|---|---|---|---|
| R-01 | AI 成功回调 JSONB | P0 | backend |
| R-02 | AI analyze SKIP | P0 | cross-domain |
| R-03 | 数字 string/number | P1 | frontend |
| R-04 | confirm 失败重试 | P1 | frontend |
| R-05 | presign 过期 | P1 | frontend |
| R-06 | 上传进度 | P1 | frontend |
| R-07 | inviteCount=3 | P1 | business |
| R-08 | inviteStatus=2 已注册 | P1 | business |
| R-09 | 职位绑定强依赖 | P1 | frontend |
| R-10 | 邮箱为空 | P1 | cross-domain |
| R-11 | 邮件到达不可证 | P2 | cross-domain |
| R-12 | task title mismatch | P2 | process |

## 5. Human Review Required（需用户在 Architect Review 时拍板）

按必要程度排序：

1. **R-02 是否引入 AI dev mock？**（Architect 推荐：**不引入**）
2. **R-01 "分析中 > 5min" Tooltip 文案与阈值是否接受？**（Architect 默认 5 分钟 + "AI 处理较慢，请稍后刷新"）
3. **R-04 confirm 失败 3 次 1s/2s/4s 退避是否接受？**
4. **R-05 presign 过期自动重申 1 次是否接受？**
5. **R-11 邀请 toast 文案"邀请邮件已提交发送，候选人可能需要几分钟才能收到"是否接受？**
6. **OQ-04 请求体 ID 字段类型 全 string** 是否接受？（Architect 默认接受；测试 number 也通过，但前端按 string 一致；不影响后端）

## 6. 不属于 Human Review（Architect 直接决策）

- R-03 数字字段 mapper normalize 单点收敛：标准技术规范，无需 Human Review
- R-06 axios `onUploadProgress` 进度展示：复用现有技术栈，无需 Human Review
- R-07 / R-08 / R-09 操作矩阵显隐：与 state-and-action-matrix 一致，无需 Human Review
- R-10 邮箱为空 UI：现有失败原因列已覆盖，无需 Human Review
- R-12 task.md 标题不一致：流程问题，由 Controller 自决

## 7. 全局回滚边界

- 本 Task 改动全部位于 5 个目录子集（services/buser/{两域}、hooks/buser/{两域}、components/buser/{两域}、types/buser/{两域}、app/buser/{两域}/page.tsx）；
- 回滚方式：**按 Phase 级 PR 单独 `git revert`**（详 PM handoff §5：Phase 1 类型 / service → Phase 2 hooks → Phase 3 上传组件 → Phase 4 平台管理组件 → Phase 5 联调）；
- 无后端数据迁移；
- 无 cookie / localStorage 持久化前端态（上传组件瞬时态丢弃即可）；
- 不需要清理服务端数据；
- 不影响其他业务页面。

## 8. 回滚触发条件

| 触发 | 回滚动作 |
|---|---|
| Phase 1-2 联调发现 mapper 字段映射错 | 改 mapper 单点；不需回滚 |
| Phase 3-4 组件 UI 严重偏差 | 单文件 revert 对应组件 |
| 全量上线后 P0 故障 | 按 Phase 顺序 revert；最坏情况完全回退至 PM 阶段前 |
| AI analyze 上线后前端无法对接 | 改 service + mapper 各 1 处；不动组件 |

## 9. 验证策略（QA 阶段用）

| 链路 | 可验证度 | 备注 |
|---|---|---|
| 上传链路（presign / PUT / confirm / stat / page / bind / delete） | 100% | 已通过 |
| 分析触发（/analyze） | 接口可通，端到端需后端 | SKIP 风险 |
| 邮箱为空 → 分析失败 | 100% | 已通过 |
| 平台管理 5 Tab + 详情 + 状态流转 + 邀请 / 撤回 / 不合适 / 恢复 / 删除 | 100% | 已通过 |
| 邀请邮件到达 | 需人工查收件箱 | 不可自动验证 |
| AI 成功 → 进入平台管理 | dev 环境暂无法（受 R-01/R-02 影响） | 等后端修复 |
