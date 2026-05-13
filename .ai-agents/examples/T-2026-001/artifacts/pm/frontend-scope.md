---
artifact_id: A-T-2026-001-frontend-scope
task_id: T-2026-001
artifact_type: frontend_scope
produced_by: pm
consumed_by:
  - architect
  - developer
file_path: artifacts/pm/frontend-scope.md
version: 1
status: ready
summary: 前端需新增 / 修改 / 复用 / 不允许修改的范围清单；不引入新框架、不动 lock 文件、不动权限体系。
dependencies:
  - A-T-2026-001-requirement-analysis
  - A-T-2026-001-api-contract-checklist
validation_result: pass
validation_notes: 现有代码已扫描，识别出 `app/buser/resumeUpload`、`app/buser/platformManagement` 等可对齐目录。
created_at: 2026-05-13T16:00:00+08:00
schema_version: a2a/v1
---

# 前端范围（Frontend Scope）

## 1. 需要新增 / 修改的页面

| 路径 | 操作 | 说明 |
|---|---|---|
| `app/buser/resumeUpload/page.tsx` | 修改 | 接入真实接口；保留现有编排骨架，page 仅做组件组装与 hook 透传，不写业务逻辑 |
| `app/buser/platformManagement/page.tsx` | 修改 | 接入真实接口；保留现有骨架，按 5 Tab 切换调 `/talent/resume/page` |
| `components/buser/resumeUpload/ResumeUploadPage.tsx` | 修改 | 上传队列 + 上传明细 Table + 子 Tab（待分析 / 分析中 / 分析失败） |
| `components/buser/resumeUpload/ResumeUploadHeader.tsx` | 修改 | 接入 `/upload/stat` 三个统计字段 |
| `components/buser/resumeUpload/ResumeUploadDropzone.tsx` | 修改 | 走 presign → PUT COS → confirm 链路；移除任何 multipart 残留代码 |
| `components/buser/resumeUpload/ResumeUploadResultTable.tsx` | 修改 | 列：文件名 / 职位 / 状态 / 失败原因 / 操作（重新分析 / 删除）；行 selection 支持批量绑定 / 批量删除 / 批量分析 |
| `components/buser/resumeUpload/ResumeUploadConfigJobModal.tsx` | 修改 | 调 `/upload/bind-job`；按"操作矩阵"屏蔽分析中 / 已导入 |
| `components/buser/resumeUpload/ResumeUploadRemoveModal.tsx` | 修改 | 调 `/upload/delete` |
| `components/buser/resumeUpload/ResumeUploadInfoPanel.tsx` | 复用 / 微调 | 文案对齐（PDF、大小、份数） |
| `components/buser/platformManagement/PlatformManagementPage.tsx` | 修改 | 按 5 Tab 渲染；不同 Tab 显示不同列与操作按钮 |
| `components/buser/platformManagement/PlatformManagementHeader.tsx` | 复用 | 头部维持现样式，去掉关键词搜索（或 disabled + tooltip） |
| `components/buser/platformManagement/PlatformFilterBar.tsx` | 修改 | 按 PRD §3.2 筛选项重排：jobId / sourceType / education / workExperience / jobSearchStatus / gender / industryExperience；本期不接入 keyword |
| `components/buser/platformManagement/PlatformCandidateTable.tsx` | 修改 | 列按 Tab 切换（state-and-action-matrix §1）；操作按钮按"操作矩阵"显隐 |
| `components/buser/platformManagement/InvitationStatusTag.tsx` | 修改 | tone mapping 对齐 `inviteStatus ∈ {0,1,2}` |
| `components/buser/platformManagement/ResumeScoreBadge.tsx` | 复用 | `matchScore` 直接展示 |
| `components/buser/platformManagement/PlatformResumePreviewModal.tsx` | 复用 / 微调 | 详情弹窗：基本信息 / AI 洞察 / 附件简历三段；attachment 用 `previewUrl`，失败 fallback `downloadUrl` |
| `components/buser/platformManagement/PlatformResumeInsightPanel.tsx` | 修改 | AI 洞察三段：highlights / riskPoints / interviewSuggestions（兼容空数组） |

> 复用边界：上述"复用"项**不修改 props 与样式**；只补类型不动 UI。

## 2. 需要新增 / 修改的 API service

业务路径前端写法（`services/axiosConfig.ts` 的 `baseURL` 已含 `/api/v1`，调用时无需重复前缀）：

| 路径（前端 axios 调用） | 实际命中 | 操作 |
|---|---|---|
| `/hire/talent/resume/upload/presign` | `app-dev.../api/v1/hire/talent/resume/upload/presign` | 新增 |
| `/hire/talent/resume/upload/confirm` | 同上 | 新增 |
| `/hire/talent/resume/upload/stat` | 同上 | 新增 |
| `/hire/talent/resume/upload/page` | 同上 | 新增 |
| `/hire/talent/resume/upload/bind-job` | 同上 | 新增 |
| `/hire/talent/resume/upload/delete` | 同上 | 新增 |
| `/hire/talent/resume/analyze` | 同上 | 新增 |
| `/hire/talent/resume/page` | 同上 | 新增 |
| `/hire/talent/resume/{id}/ai-insight` | 同上 | 新增 |
| `/hire/talent/resume/{id}/interest` | 同上 | 新增 |
| `/hire/talent/resume/{id}/unsuitable` | 同上 | 新增 |
| `/hire/talent/resume/{id}/restore` | 同上 | 新增 |
| `/hire/talent/resume/{id}` | 同上 | 新增（DELETE） |
| `/hire/talent/resume/{id}/invite` | 同上 | 新增 |
| `/hire/talent/resume/{id}/invite/resend` | 同上 | 新增 |
| `/hire/talent/resume/{id}/invite/recall` | 同上 | 新增 |

存放约束（参考 `04-service-request-auth.rule.mdc`）：

- `services/buser/resumeUpload/index.ts` —— 新增；7 个上传 + 分析接口
- `services/buser/platformManagement/index.ts` —— 新增；9 个平台管理接口
- **不允许** 直接在组件 / hook 中 `axiosInstance.post(...)` 绕过 service
- **不允许** 在 service 内部 `message.error(...)` 做 UI 反馈

## 3. 需要新增 / 修改的 type

| 路径 | 操作 | 说明 |
|---|---|---|
| `types/buser/resumeUpload/index.ts` | 修改 | 新增 DTO：`PresignReq/Resp`、`ConfirmReq/Resp`、`UploadStatResp`、`UploadItemRaw`（与 `talent_resume_upload_item` 对齐）、`UploadPageReq/Resp`、`BindJobReq/Resp`、`DeleteReq/Resp`、`AnalyzeReq/Resp`；保留现有 `ResumeUploadFileViewModel` 但收敛字段以兼容后端 |
| `types/buser/platformManagement/index.ts` | 修改 | 新增 DTO：`PlatformResumeListReq/Resp` 与 `PlatformResumeListItemRaw`（与 `talent_resume` 列字段对齐：`id/candidateName/phone/jobId/jobName/expectedJob/matchScore/riskCount/age/workExperience/education/schoolName/gender/industryExperience/jobSearchStatus/resumeAttachmentPreviewUrl/hrStatus/hrStatusName/inviteStatus/inviteStatusName/inviteCount/inviteExpireAt/inviteSentAt/unsuitableReasonType/unsuitableReasonName/unsuitableReasonRemark/unsuitableMarkedAt/createdAt`）；新增 `PlatformResumeDetail`、`StatusTransitionResp`、`InviteOpResp`；保留 `PlatformCandidateViewModel` 但 ViewModel 字段补齐至覆盖详情弹窗所需 |
| `types/buser/resumeUpload/index.ts` | 修改 | 新增联合枚举：`UploadStatus = 0 \| 1 \| 2`、`AnalysisStatus = 0 \| 1 \| 2 \| 3`、`HrStatus = 0 \| 1 \| 2 \| 3 \| 4`、`InviteStatus = 0 \| 1 \| 2`、`UnsuitableReasonType = 1 \| 2 \| 3 \| 4` |

类型硬约束（参考 `07-type-id-field-convention.rule.mdc`）：

- 所有 ID 字段（`uploadItemId / talentResumeId / jobId / aiTaskId`）类型 `string`；ViewModel 一致。
- 测试报告中 `matchScore / fileSize / inviteCount / current / size / pages / total / riskCount` 存在 `number | string` 混用：DTO 使用 `number | string | null` 联合类型，**mapper 内 normalize 为前端 ViewModel 字段**（`number` 或 `string`，二选一稳定形式）。
- 禁止 `as any` 与 `Number(id)`。

## 4. 需要复用的现有组件 / Hook / 工具

| 类别 | 路径 | 用途 |
|---|---|---|
| service 单例 | `services/axiosConfig.ts` + `services/buser/jobs` (`searchJobPositionByEs`) | 邀请 / 绑定职位的下拉数据来源 |
| 业务错误处理 | `constants/mappers` (`checkResCode`, `unwrap`) | hook 层统一调用 |
| toast | `lib/appMessage` (`appMessage as message`) | 非业务错误（网络异常）才弹；业务错误已由 axios 拦截 |
| SWR | `useSWR`（已在 `usePlatformManagementPage` / `useResumeUploadPage` 使用） | 列表、统计、详情、Tab 切换 |
| Job 选项 | `searchJobPositionByEs<ApiResponse<PageData<JobPositionItem>>>` | 上传页"绑定职位"+ 平台管理页"职位筛选" |
| 路由 / Layout | `app/buser/layout.tsx` + 现有侧边栏 | 不修改 |
| Antd 组件 | `Table / Modal / Form / Select / Upload / Tabs / Tag / Tooltip / Progress` | 上传进度、Tab、操作按钮、Tooltip |
| Tailwind / designTokens | `components/buser/platformManagement/styles.ts`、`components/buser/resumeUpload/styles.ts` | 已存在样式常量复用，不新增全局样式 |
| Long ID 工具 | mappers 内统一 `String(id)`；不引入新 utils | |

## 5. 不允许修改的范围

- `package.json` / `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock`
- `.github/**` / `.gitlab-ci.yml` / `Dockerfile` / CI 配置
- `next.config.js` / `next.config.ts` / `tsconfig.json`（除非 Architect 在 file-change-plan 中显式 `allowed: yes` 且 `owner: user-approved`）
- `services/axiosConfig.ts`（鉴权拦截器 / `PUBLIC_AUTH_PATHS` / `checkResCode` 行为）—— 本次接口为已登录态，无需动鉴权
- `middleware.ts` —— 本次无新增公开路由
- 任何与平台管理 / 简历上传**无关的页面与组件**（如 `app/buser/jobs`、`app/buser/dashboard`、`app/cuser/**` 等）
- 全局权限体系 / 菜单配置
- 主题 / Antd ConfigProvider 全局变量
- mock 数据：本期不引入新的 mock 框架，开发期由 Architect 在 file-change-plan 中明确"如何在 AI 接口未就绪时验证 UI"

## 6. PM 阶段不做范围（留 Architect 决策）

- `services/buser/resumeUpload/` 与 `services/buser/platformManagement/` 的具体函数名、参数命名风格、是否拆分多个 service 文件
- `hooks/buser/resumeUpload/useResumeUploadPage.ts` 与 `hooks/buser/platformManagement/usePlatformManagementPage.ts` 是否拆分子 hook（如 `useUploadQueue` / `useAnalysisActions` / `useInviteActions`）
- mapper 文件是否拆分（如 `uploadItemMapper.ts` / `platformResumeMapper.ts`）
- 上传明细分页时机（SWR keepPreviousData / 触发分析后立即 mutate / interval polling 周期）—— 列入 architect-handoff 必答
- 详情弹窗附件预览失败的具体兜底（iframe 失败检测、`object` 退化、纯下载按钮）—— 列入 architect-handoff 必答
