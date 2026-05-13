---
artifact_id: A-T-2026-001-architect-handoff
task_id: T-2026-001
artifact_type: architect_handoff
produced_by: pm
consumed_by:
  - architect
file_path: artifacts/pm/architect-handoff.md
version: 1
status: ready
summary: 给 Architect 的输入包，含推荐模块设计方向、file-change-plan 粒度建议、必答问题、Human Review 风险点、Developer 拆分建议。
dependencies:
  - A-T-2026-001-requirement-analysis
  - A-T-2026-001-api-contract-checklist
  - A-T-2026-001-frontend-scope
  - A-T-2026-001-state-and-action-matrix
  - A-T-2026-001-risk-and-open-questions
validation_result: pass
validation_notes: 不替代 Architect 的 tech-plan / file-change-plan；只给输入。
created_at: 2026-05-13T16:00:00+08:00
schema_version: a2a/v1
---

# Architect Handoff（PM → Architect）

> 本文件给 Architect 阶段使用。Architect 必须基于以下输入产出 `artifacts/architect/tech-plan.md`、`artifacts/architect/file-change-plan.md`、`artifacts/architect/risk-plan.md`。
> PM 阶段已完成的事不要重复做；PM 未拍板的事请在 file-change-plan 中明确收敛。

## 1. 推荐模块设计方向

### 1.1 分层

| 层 | 路径 | 职责 |
|---|---|---|
| 路由层 | `app/buser/resumeUpload/page.tsx`, `app/buser/platformManagement/page.tsx` | 组合聚合 hook + 子组件；不写业务 |
| 聚合 hook | `hooks/buser/resumeUpload/useResumeUploadPage.ts`, `hooks/buser/platformManagement/usePlatformManagementPage.ts` | 编排：state / SWR / handlers；返回稳定 `state + handlers + ViewModel[]` |
| 基础 hook | `hooks/buser/resumeUpload/baseHooks.ts`（建议新增）, `hooks/buser/platformManagement/baseHooks.ts`（建议新增） | 拆分子能力：`useUploadQueue` / `useAnalysisActions` / `useInviteActions` / `usePlatformResumeDetail` |
| mapper | `hooks/buser/resumeUpload/mappers.ts`, `hooks/buser/platformManagement/mappers.ts` | Raw → ViewModel + payload builder；纯函数 |
| service | `services/buser/resumeUpload/index.ts`（新增）, `services/buser/platformManagement/index.ts`（新增） | 纯 HTTP；不弹 toast |
| 子组件 | `components/buser/resumeUpload/*`, `components/buser/platformManagement/*` | 只接 props、只渲染 |
| 类型 | `types/buser/resumeUpload/index.ts`, `types/buser/platformManagement/index.ts` | DTO + ViewModel 分离 |

### 1.2 数据流（强约束）

```text
API raw response
  → service 函数（含 checkResCode + unwrap）
  → hook 内 mapper 转 ViewModel
  → 子组件直接消费 ViewModel
```

```text
表单 / Form value
  → hook 内 payload builder（mappers 内）
  → service 函数
```

### 1.3 SWR 缓存策略

- 列表（上传明细 / 平台管理列表）：`keepPreviousData: true`、`revalidateOnFocus: false`、`dedupingInterval: 10000`（参考现有实现）。
- 上传统计 `/upload/stat`：独立 SWR key；在"上传成功 / 删除 / 分析 / AI 回调可能完成时"由 mutate 联动。
- 详情 `/{id}/ai-insight`：仅在 modal 打开时拉取（懒加载）；关闭即清。
- 不引入 polling（决定权交 Architect，建议 SWR `refreshInterval` 仅在"上传页 + analysisStatus=1 行存在"时启用）。

## 2. 推荐 file-change-plan 粒度

> 建议按"领域 + 文件级"列出每条 entry；每条含 `operation / allowed / owner / risk`。

### 2.1 简历上传领域（约 12 条）

| # | 路径 | operation | 说明 |
|---|---|---|---|
| 1 | `services/buser/resumeUpload/index.ts` | create | 7 个上传 + 分析接口 service |
| 2 | `types/buser/resumeUpload/index.ts` | modify | DTO + ViewModel + 联合枚举 |
| 3 | `hooks/buser/resumeUpload/mappers.ts` | modify | uploadItemRawToViewModel + payload builders |
| 4 | `hooks/buser/resumeUpload/baseHooks.ts` | create | useUploadQueue / useAnalysisActions / useBindJobActions / useDeleteUploadItems |
| 5 | `hooks/buser/resumeUpload/useResumeUploadPage.ts` | modify | 接入真实接口 |
| 6 | `hooks/buser/resumeUpload/index.ts` | modify | barrel export |
| 7 | `components/buser/resumeUpload/ResumeUploadPage.tsx` | modify | 编排 |
| 8 | `components/buser/resumeUpload/ResumeUploadHeader.tsx` | modify | 接 stat |
| 9 | `components/buser/resumeUpload/ResumeUploadDropzone.tsx` | modify | presign → PUT → confirm |
| 10 | `components/buser/resumeUpload/ResumeUploadResultTable.tsx` | modify | 列 / 行操作 / selection |
| 11 | `components/buser/resumeUpload/ResumeUploadConfigJobModal.tsx` | modify | 调 bind-job |
| 12 | `components/buser/resumeUpload/ResumeUploadRemoveModal.tsx` | modify | 调 delete |
| 13 | `app/buser/resumeUpload/page.tsx` | modify | 仅编排 |

### 2.2 平台管理领域（约 13 条）

| # | 路径 | operation | 说明 |
|---|---|---|---|
| 1 | `services/buser/platformManagement/index.ts` | create | 9 个接口 service |
| 2 | `types/buser/platformManagement/index.ts` | modify | DTO + ViewModel + 联合枚举 |
| 3 | `hooks/buser/platformManagement/mappers.ts` | modify | resumeRawToViewModel + detail mapper + payload builders |
| 4 | `hooks/buser/platformManagement/baseHooks.ts` | create | useTabList / useResumeDetail / useStatusActions / useInviteActions / useUnsuitableActions |
| 5 | `hooks/buser/platformManagement/usePlatformManagementPage.ts` | modify | 接入真实接口；移除关键词搜索 |
| 6 | `hooks/buser/platformManagement/index.ts` | modify | barrel export |
| 7 | `components/buser/platformManagement/PlatformManagementPage.tsx` | modify | 编排 |
| 8 | `components/buser/platformManagement/PlatformManagementHeader.tsx` | modify | 关键词搜索 disabled 或移除 |
| 9 | `components/buser/platformManagement/PlatformFilterBar.tsx` | modify | 按 PRD §3.2 字段重排 |
| 10 | `components/buser/platformManagement/PlatformCandidateTable.tsx` | modify | 列 / 行操作（按矩阵） |
| 11 | `components/buser/platformManagement/InvitationStatusTag.tsx` | modify | tone mapping |
| 12 | `components/buser/platformManagement/PlatformResumePreviewModal.tsx` | modify | 三段式详情弹窗 |
| 13 | `components/buser/platformManagement/PlatformResumeInsightPanel.tsx` | modify | AI 洞察空态兼容 |
| 14 | `app/buser/platformManagement/page.tsx` | modify | 仅编排 |

### 2.3 不允许 / 禁改集

- `package.json` / lock 文件
- `services/axiosConfig.ts`
- `middleware.ts`
- `next.config.*` / `tsconfig.json`
- 全局主题 / antd ConfigProvider
- 任何与本次需求无关的 app / hooks / components / types / services 路径

## 3. Architect 必须回答的问题（architect_must_answer）

> 这些问题不回答清楚就不应该写 file-change-plan。

1. **OQ-01**：`services/buser/{resumeUpload,platformManagement}/index.ts` 中接口路径前缀是 `/hire/talent/resume/...` 还是 `/api/v1/hire/talent/resume/...`？（请查 `services/axiosConfig.ts` baseURL）
2. **OQ-02**：上传明细列表分析中行的刷新策略？（建议：行数 > 0 时启用 `refreshInterval = 5000`，行数为 0 时关闭）
3. **OQ-03**：附件预览失败 fallback 实现细节（iframe.onerror / object fallback / 仅下载按钮）？
4. **OQ-04**：所有请求体 ID 字段统一 string 还是按测试报告 number？影响 mapper 与 payload builder。
5. **OQ-06**：触发 `/analyze` 成功后的乐观更新策略（单条 SWR 缓存更新 / 全表 mutate / 两者结合）？
6. **OQ-07**：是否在 dev 环境引入 AI mock（用 env 开关）以解锁本地"分析中→成功"链路自测？若是，定义清楚 mock 文件位置、开关名称、prod 排除策略。
7. 上传组件的进度展示库选型（axios `onUploadProgress` 还是原生 XHR / 是否引入 `tus-js-client`）—— 倾向最小依赖 axios `onUploadProgress`。
8. confirm 重试次数与退避策略是否落 hook 层 utility 还是直接写在 service？
9. 哪些 ViewModel 推导字段（`canBindJob / canDelete / canAnalyze / canInvite / canResend / canRecall / canUnsuitable / canRestore / canDeleteCandidate`）放在 mapper、哪些放在 hook？建议 mapper 内一次性生成 `boolean` 字段，组件只读。
10. 详情弹窗与列表 SWR 的 mutate 联动：标记不合适 / 邀请 / 撤回成功后是否需要主动 mutate 详情？
11. 当 `task.md` 与真实需求标题不一致时，是否需要 Controller 先发 message 锁定 task slot？（PM 已记录到 OQ-05，等 Controller 处理；Architect 阶段不会被阻塞）

## 4. 需要 Human Review 的风险点

> 等 Architect 完成 tech-plan + file-change-plan 后进入 Human Review；以下为必看清单：

1. **R-01 后端 JSONB 写入 bug**：前端不修复后端 bug，但需在 UI 上做"分析中 > 5min"的可见兜底文案。Human 需确认文案与时长阈值。
2. **R-02 AI 提交 SKIP**：决定是否引入 dev mock（OQ-07）；如不引入，需明确告知 QA 当前无法端到端验证分析成功路径。
3. **R-03 confirm 失败重试**：Human 需确认前端做"最多 3 次重试" vs "用户手动重试"的折中。
4. **R-04 presign 过期**：自动重试 1 次的策略是否可接受；过期文案是否需要更明显的 UI 提示。
5. **R-09 数字字符串混用**：DTO 联合类型 + mapper normalize 的方案是否在团队规范范围内（与 `07-type-id-field-convention.rule.mdc` 一致）。
6. **R-10 邮件到达不可证**：邀请 toast 文案需 Human 拍板（避免 HR 错把"邮件已发送"理解为"已送达"）。
7. **不允许修改清单**（frontend-scope §5）与 file-change-plan 是否一致；任何额外加入的禁改集必须显式 `allowed: yes + owner: user-approved`。

## 5. Developer 阶段建议拆分（供 Architect 参考；不替代 task-breakdown）

> 仅作为开发顺序建议；Architect 在 file-change-plan 后可重新组织。

### Phase 1（基础层，可独立 PR）

1. 类型定义：`types/buser/resumeUpload/index.ts` + `types/buser/platformManagement/index.ts`
2. service 函数：`services/buser/resumeUpload/index.ts` + `services/buser/platformManagement/index.ts`
3. mapper：两个 mappers 文件（含 payload builder + ViewModel 推导字段）

### Phase 2（hook 层）

4. 上传 base hooks：`useUploadQueue` / `useAnalysisActions` / `useBindJobActions` / `useDeleteUploadItems`
5. 平台管理 base hooks：`useTabList` / `useResumeDetail` / `useStatusActions` / `useInviteActions` / `useUnsuitableActions`
6. 聚合 hook：`useResumeUploadPage` / `usePlatformManagementPage`

### Phase 3（组件层 / 上传页）

7. `ResumeUploadDropzone.tsx`（presign → PUT → confirm）
8. `ResumeUploadHeader.tsx`（stat）
9. `ResumeUploadResultTable.tsx`（列 / 行操作 / selection / 重新分析）
10. `ResumeUploadConfigJobModal.tsx` + `ResumeUploadRemoveModal.tsx`
11. `ResumeUploadPage.tsx` 编排 + `app/buser/resumeUpload/page.tsx`

### Phase 4（组件层 / 平台管理）

12. `PlatformFilterBar.tsx`（按 PRD §3.2 字段）
13. `PlatformCandidateTable.tsx`（列按 Tab 切 / 行操作按矩阵）
14. `InvitationStatusTag.tsx` + `ResumeScoreBadge.tsx`（tone mapping）
15. `PlatformResumePreviewModal.tsx`（三段式）+ `PlatformResumeInsightPanel.tsx`（AI 洞察空态）
16. `PlatformManagementPage.tsx` 编排 + `app/buser/platformManagement/page.tsx`

### Phase 5（联调 + 回归）

17. 端到端：上传 → confirm → bind → analyze → 列表轮询 → 平台管理 → 详情 → 邀请 / 重发 / 撤回 / 不合适 / 恢复 / 删除
18. 边界场景：presign 过期、confirm 失败、邮箱为空失败、AI 分析中 > 5min、邀请次数到 3、`unsuitableReasonType=4` Form 校验
19. 自检：所有改动文件跑 Prettier + ReadLints + 无格式化报错

> Developer 阶段不允许跨 Phase 把 PR 揉成一个；每个 Phase 推荐独立 PR 以保证可 review、可回滚。

## 6. 强约束传递（PM → Architect → Developer）

- 所有 Long ID `string` 全链路；不允许 `Number(id)`。
- 所有数字字段（`fileSize / matchScore / inviteCount / 分页字段`）DTO 用联合类型 + mapper 收敛。
- 业务错误统一走 axios 拦截 + `checkResCode`，hook 内 catch 跳过 `isBusinessError`，page 内不重复 toast。
- mapper / normalize 无副作用。
- payload 统一出口（`buildXxxParams`）。
- modal / loading / toast 单一来源。
- 严禁 `as any` 与 `useState + useEffect 替代派生状态`。

## 7. 不属于 Architect 范围的提示

- Architect 不写代码；只产 `tech-plan / file-change-plan / risk-plan`。
- file-change-plan 必须覆盖所有要新增 / 修改的路径；未在白名单的路径 Developer 不允许写。
- 默认禁改集（package.json / lock / CI / Dockerfile）即便 Architect 允许，也需要 `owner: user-approved` 标识，并由 Human Review 显式确认。
