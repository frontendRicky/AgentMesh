---
artifact_id: A-T-2026-001-file-change-plan
task_id: T-2026-001
artifact_type: file_change_plan
produced_by: architect
consumed_by:
  - developer
  - qa
file_path: artifacts/architect/file-change-plan.md
version: 1
status: ready
summary: 28 个文件改动白名单（create 4 / modify 24 / readonly 1 / forbidden 14）；不引入新依赖；package.json / lock / CI / Dockerfile / axiosConfig / middleware / next.config / tsconfig 默认 forbidden。
dependencies:
  - A-T-2026-001-tech-plan
validation_result: pending
created_at: 2026-05-13T16:30:00+08:00
schema_version: a2a/v1
---

# File Change Plan: 平台管理 + 批量简历上传前端联调

> **Developer 写代码门禁的唯一依据**。每个文件条目必含 7 字段（path / operation / allowed / reason / risk / owner / notes）。
>
> Developer 严禁修改本计划之外的任何文件。发现需新增白名单外的文件 → 发 `from-developer-<seq>-blocker-request.md`，由 Architect 补，再回到 Developer。

## 1. 白名单（28 条）

### 1.1 简历上传 — 类型与 service（基础层）

```yaml
- path: types/buser/resumeUpload/index.ts
  operation: modify
  allowed: yes
  reason: 新增/重写 DTO（PresignReq/Resp、ConfirmReq/Resp、UploadStatResp、UploadItemRaw、UploadPageReq/Resp、BindJobReq/Resp、DeleteReq/Resp、AnalyzeReq/Resp）+ 联合枚举（UploadStatus / AnalysisStatus）+ ViewModel（保留 ResumeUploadFileViewModel 名字，字段大改）+ canXxx 派生字段类型
  risk: 中,跨越多个组件 import 需同步更新
  owner: developer
  notes: 保留现有 export 名字以减小 import diff；联合枚举禁用 enum，用 type union；ID 字段一律 string

- path: services/buser/resumeUpload/index.ts
  operation: create
  allowed: yes
  reason: 7 个上传 + 分析接口（presign / confirm / stat / page / bind-job / delete / analyze）；纯 HTTP，无业务逻辑，无 UI 反馈
  risk: 低,新文件独立
  owner: developer
  notes: 接口路径不加 /api/v1 前缀（baseURL 已含）；返回类型用泛型 <T>；请求体 ID 字段全 string；不使用 Number/parseInt
```

### 1.2 简历上传 — hooks / mappers

```yaml
- path: hooks/buser/resumeUpload/mappers.ts
  operation: modify
  allowed: yes
  reason: 接入新 DTO；新增 mapUploadItemRawToViewModel（含 canBindJob/canDelete/canAnalyze/canRetry/isAnalyzing/isAnalysisFailed/fileSizeLabel）+ buildPresignPayload + buildConfirmPayload + buildBindJobPayload + buildDeletePayload + buildAnalyzePayload；保留旧 export 名以兼容 import
  risk: 中,是数据流唯一收敛点
  owner: developer
  notes: 纯函数；不调 service / 不弹 toast / 不操作 DOM；分页 current/size/pages/total 转 number

- path: hooks/buser/resumeUpload/baseHooks.ts
  operation: create
  allowed: yes
  reason: 拆分子能力 hook（useUploadQueue 含 presign+PUT+confirm+retry+abort、useUploadStat、useUploadItemPage、useBindJobAction、useDeleteUploadItemsAction、useAnalyzeAction）；聚合 hook 调用
  risk: 中,新增分层
  owner: developer
  notes: useUploadQueue 内私有 retryConfirm（1s/2s/4s 退避，最多 3 次）+ AbortController；不引入 COS SDK；不实现 multipart

- path: hooks/buser/resumeUpload/useResumeUploadPage.ts
  operation: modify
  allowed: yes
  reason: 编排：组合 baseHooks + SWR + 上传队列瞬时态 + 子 Tab（success/parsing/failed）切换 + 多选 + bind-job modal + remove modal + analyze 触发；移除任何 multipart 残留
  risk: 中,聚合层
  owner: developer
  notes: 文件不得超 300 行；超出拆 baseHooks；返回稳定 UsexxxReturn；SWR refreshInterval 仅在 parsing Tab + 行数>0 时为 5000

- path: hooks/buser/resumeUpload/index.ts
  operation: modify
  allowed: yes
  reason: barrel export 更新（导出 useResumeUploadPage / baseHooks 公开 hook / mapper 公开函数）
  risk: 低
  owner: developer
  notes: 不导出 baseHooks 内部 utility 函数
```

### 1.3 简历上传 — 组件层

```yaml
- path: components/buser/resumeUpload/ResumeUploadPage.tsx
  operation: modify
  allowed: yes
  reason: 编排组件；挂载 Header / Dropzone / InfoPanel / ResultTable / Modal；只透传 useResumeUploadPage 返回值
  risk: 低
  owner: developer
  notes: 不写业务逻辑；不发请求；不持有非展示态 state

- path: components/buser/resumeUpload/ResumeUploadHeader.tsx
  operation: modify
  allowed: yes
  reason: 头部接 /upload/stat 三字段（uploadSuccessCount / analyzingCount / lastFailedCount），按 Tab 数字徽标展示
  risk: 低
  owner: developer
  notes: 文案与现有保持一致；string 字段 mapper 转 number 后展示

- path: components/buser/resumeUpload/ResumeUploadDropzone.tsx
  operation: modify
  allowed: yes
  reason: 走 presign → PUT 直传 COS → confirm 链路；用 axios onUploadProgress 展示行级进度；用户取消 abort；不实现分片
  risk: 中,前端链路核心
  owner: developer
  notes: PDF 校验沿用 isValidPdf；fileSize 上限 10MB；文件数上限 50；不调 services/common/upload.ts 老链路

- path: components/buser/resumeUpload/ResumeUploadInfoPanel.tsx
  operation: modify
  allowed: yes
  reason: 文案对齐（PDF / 单文件 10MB / 单次 50 份）；保留现有视觉
  risk: 低
  owner: developer
  notes: 仅文案与展示字段微调；不动布局

- path: components/buser/resumeUpload/ResumeUploadResultTable.tsx
  operation: modify
  allowed: yes
  reason: 列（文件名 / 职位 / 状态 / 失败原因 / 操作）+ 行 selection + 重新分析（行级，仅 canRetry=true 显示）+ 删除（行级，仅 canDelete=true 显示）+ 子 Tab 切换（待分析 / 分析中 / 分析失败）
  risk: 中,UI 重头戏
  owner: developer
  notes: 列定义按 Tab key 切换；按钮显隐读 ViewModel canXxx，不重复 if 判断；列表 selection 仅在 canBindJob/canDelete=true 行可选

- path: components/buser/resumeUpload/ResumeUploadConfigJobModal.tsx
  operation: modify
  allowed: yes
  reason: 调 /upload/bind-job；Job Select 来自 useResumeUploadPage 的 jobOptions（复用 searchJobPositionByEs）；表单 value 与 option value 一致 string
  risk: 中
  owner: developer
  notes: 选择失败行（canBindJob=false）不允许进入；提交 loading 单一来源；form rule 校验 jobId 必填

- path: components/buser/resumeUpload/ResumeUploadRemoveModal.tsx
  operation: modify
  allowed: yes
  reason: 调 /upload/delete；二次确认；批量结果按 items[] 失败原因列出
  risk: 低
  owner: developer
  notes: 仅 canDelete=true 行允许传入

- path: components/buser/resumeUpload/styles.ts
  operation: readonly
  allowed: no
  reason: 不动；复用现有样式常量
  risk: 低
  owner: developer
  notes: 如需新增样式，必须先发 blocker-request 由 Architect 在本 plan 增条

- path: components/buser/resumeUpload/index.ts
  operation: modify
  allowed: yes
  reason: barrel export 不变；如新增 Component 才需补
  risk: 低
  owner: developer
  notes: 本期不新增 Component，仅 modify 现有

- path: app/buser/resumeUpload/page.tsx
  operation: modify
  allowed: yes
  reason: 仅编排（挂 ResumeUploadPage）；不写业务
  risk: 低
  owner: developer
  notes: 不写 useEffect 取数；不写 try/catch
```

### 1.4 平台管理 — 类型与 service

```yaml
- path: types/buser/platformManagement/index.ts
  operation: modify
  allowed: yes
  reason: 新增/重写 DTO（PlatformResumeListReq/Resp、PlatformResumeListItemRaw、PlatformResumeDetailRaw、StatusTransitionResp、InviteOpResp、UnsuitableReq）+ 联合枚举（HrStatus / InviteStatus / UnsuitableReasonType）+ ViewModel（保留 PlatformCandidateViewModel 名字、扩字段至覆盖列表与详情）+ canXxx 派生类型
  risk: 中
  owner: developer
  notes: 保留 PlatformManagementTabKey 等现有枚举，但 tab→hrStatus 映射在 mapper 内统一

- path: services/buser/platformManagement/index.ts
  operation: create
  allowed: yes
  reason: 9 个接口 service（list page / ai-insight / interest / unsuitable / restore / delete / invite / invite/resend / invite/recall）；纯 HTTP
  risk: 低
  owner: developer
  notes: 不加 /api/v1 前缀；路径参数 id 接 string；不消费业务错误
```

### 1.5 平台管理 — hooks / mappers

```yaml
- path: hooks/buser/platformManagement/mappers.ts
  operation: modify
  allowed: yes
  reason: 接入新 DTO；mapPlatformResumeRawToViewModel（含 canInterest/canInvite/canResend/canRecall/canUnsuitable/canRestore/canDeleteResume/inviteCountLabel）+ mapPlatformResumeDetailRaw + buildPlatformPageParams + buildUnsuitablePayload；保留旧 export 名
  risk: 中
  owner: developer
  notes: 纯函数；分页 current/size/pages/total 转 number；matchScore null → '-' 字符串展示

- path: hooks/buser/platformManagement/baseHooks.ts
  operation: create
  allowed: yes
  reason: 拆分子能力 hook（useTabResumeList、useResumeDetail（modal 内 lazy）、useStatusActions（interest/restore/delete/unsuitable）、useInviteActions（invite/resend/recall））
  risk: 中
  owner: developer
  notes: 各 action hook 内调 service + 处理 isBusinessError + mutate 列表/详情；不重复 toast；不依赖全局 store

- path: hooks/buser/platformManagement/usePlatformManagementPage.ts
  operation: modify
  allowed: yes
  reason: 编排：5 Tab + 列表 SWR + 详情 modal controller + 状态/邀请 actions + 筛选 + 分页；移除关键词搜索（不支持 ES）；移除 sortField/sortOrder（本期不做列排序）
  risk: 中
  owner: developer
  notes: 文件不得超 300 行；超出拆 baseHooks；切 Tab/筛选变化时 current=1；不调 keyword 接口

- path: hooks/buser/platformManagement/index.ts
  operation: modify
  allowed: yes
  reason: barrel export 更新
  risk: 低
  owner: developer
  notes: 仅暴露聚合 hook 与公开 mapper
```

### 1.6 平台管理 — 组件层

```yaml
- path: components/buser/platformManagement/PlatformManagementPage.tsx
  operation: modify
  allowed: yes
  reason: 编排组件；按 5 Tab 渲染；接 PlatformResumePreviewModal；不写业务
  risk: 低
  owner: developer
  notes: 不持有重复 state

- path: components/buser/platformManagement/PlatformManagementHeader.tsx
  operation: modify
  allowed: yes
  reason: 移除或 disabled+Tooltip 关键词搜索（后端未接 ES）；保留 Job 筛选下拉
  risk: 低
  owner: developer
  notes: 选择 disabled+Tooltip 路线；不删除现有组件以免破坏视觉

- path: components/buser/platformManagement/PlatformFilterBar.tsx
  operation: modify
  allowed: yes
  reason: 按 PRD §3.2 字段重排：jobId / sourceType / education / workExperience / jobSearchStatus / gender / industryExperience；删除 PRD 未覆盖的筛选项；切 Tab 时清空筛选条件
  risk: 中,筛选业务集中
  owner: developer
  notes: 筛选项 Select option value 与 form value 类型一致；为空字段不传给后端

- path: components/buser/platformManagement/PlatformCandidateTable.tsx
  operation: modify
  allowed: yes
  reason: 列按 Tab 切换（state-and-action-matrix §3）；行操作按 canXxx 显隐；不合适弹原因 modal；删除二次确认
  risk: 中
  owner: developer
  notes: 列定义抽常量按 tabKey 索引；按钮组件读 canXxx 直渲染；不在组件内重复 if

- path: components/buser/platformManagement/InvitationStatusTag.tsx
  operation: modify
  allowed: yes
  reason: tone mapping 对齐 inviteStatus ∈ {0,1,2}（未邀请 / 已发送 / 已注册）
  risk: 低
  owner: developer
  notes: 仅修 tone + label 字典；不动样式系统

- path: components/buser/platformManagement/ResumeScoreBadge.tsx
  operation: readonly
  allowed: no
  reason: 复用现有；matchScore 直接展示
  risk: 低
  owner: developer
  notes: 如 score 颜色阈值变化，发 blocker-request

- path: components/buser/platformManagement/PlatformResumePreviewModal.tsx
  operation: modify
  allowed: yes
  reason: 详情弹窗三 Tab：基本信息 / AI 洞察 / 附件简历；通过 useResumeDetail 拉详情；附件 iframe + onError fallback 下载
  risk: 中
  owner: developer
  notes: detail loading 与 submit loading 分两层；关闭时 reset；submit 时 cancel 禁用，detail loading 时仍可关闭

- path: components/buser/platformManagement/PlatformResumeInsightPanel.tsx
  operation: modify
  allowed: yes
  reason: AI 洞察三段（highlights / riskPoints / interviewSuggestions）兼容空数组与 null；matchScore 与 summary 兜底渲染
  risk: 低
  owner: developer
  notes: mapper 已兜底 ?? []；组件不再判断 null

- path: components/buser/platformManagement/styles.ts
  operation: readonly
  allowed: no
  reason: 不动；复用现有 PLATFORM_MANAGEMENT_TABLE_CLASS 等样式常量
  risk: 低
  owner: developer
  notes: 如需新增 class，发 blocker-request

- path: components/buser/platformManagement/index.ts
  operation: modify
  allowed: yes
  reason: barrel export 不变；若类型 export 名变，同步更新
  risk: 低
  owner: developer
  notes: 不新增 component

- path: app/buser/platformManagement/page.tsx
  operation: modify
  allowed: yes
  reason: 仅编排（挂 PlatformManagementPage）
  risk: 低
  owner: developer
  notes: 不写业务
```

### 1.7 服务历史路径（保留只读）

```yaml
- path: services/common/upload.ts
  operation: readonly
  allowed: no
  reason: 老 multipart 中转上传链路保留作历史调用方（其他模块仍用）；本期新链路在 services/buser/resumeUpload 独立实现
  risk: 中,改它会破坏其他模块
  owner: developer
  notes: 不在本期触碰
```

## 2. 默认禁改集（必须显式列出）

```yaml
- path: package.json
  operation: forbidden
  allowed: no
  reason: 本期不引入新依赖；axios/swr/antd/clsx/tailwind-merge 全部复用
  risk: 高,改后影响整个工程
  owner: user-approved
  notes: 默认禁改集

- path: package-lock.json
  operation: forbidden
  allowed: no
  reason: 同上
  risk: 高
  owner: user-approved
  notes: 默认禁改集

- path: pnpm-lock.yaml
  operation: forbidden
  allowed: no
  reason: 同上
  risk: 高
  owner: user-approved
  notes: 默认禁改集

- path: yarn.lock
  operation: forbidden
  allowed: no
  reason: 同上
  risk: 高
  owner: user-approved
  notes: 默认禁改集

- path: bun.lock
  operation: forbidden
  allowed: no
  reason: 同上
  risk: 高
  owner: user-approved
  notes: 默认禁改集

- path: bun.lockb
  operation: forbidden
  allowed: no
  reason: 同上
  risk: 高
  owner: user-approved
  notes: 默认禁改集

- path: .github/**
  operation: forbidden
  allowed: no
  reason: 不动 CI 配置
  risk: 高
  owner: user-approved
  notes: 默认禁改集

- path: .gitlab-ci.yml
  operation: forbidden
  allowed: no
  reason: 不动 CI 配置
  risk: 高
  owner: user-approved
  notes: 默认禁改集

- path: .circleci/**
  operation: forbidden
  allowed: no
  reason: 不动 CI 配置
  risk: 高
  owner: user-approved
  notes: 默认禁改集

- path: .buildkite/**
  operation: forbidden
  allowed: no
  reason: 不动 CI 配置
  risk: 高
  owner: user-approved
  notes: 默认禁改集

- path: Dockerfile
  operation: forbidden
  allowed: no
  reason: 不动镜像构建
  risk: 高
  owner: user-approved
  notes: 默认禁改集

- path: .husky/**
  operation: forbidden
  allowed: no
  reason: 不动 git hooks
  risk: 高
  owner: user-approved
  notes: 默认禁改集

- path: .eslintrc*
  operation: forbidden
  allowed: no
  reason: 不动 lint 规则
  risk: 高
  owner: user-approved
  notes: 默认禁改集

- path: tsconfig.json
  operation: forbidden
  allowed: no
  reason: 不动编译配置
  risk: 高
  owner: user-approved
  notes: 默认禁改集
```

## 3. 关键 readonly / forbidden 显式声明（防止 Developer 误碰）

```yaml
- path: services/axiosConfig.ts
  operation: forbidden
  allowed: no
  reason: baseURL 已含 /api/v1；鉴权拦截器 / PUBLIC_AUTH_PATHS / checkResCode 行为本期不动
  risk: 高,影响所有 service 调用
  owner: user-approved
  notes: 即使发现 base URL 拼接问题也先发 blocker-request

- path: middleware.ts
  operation: forbidden
  allowed: no
  reason: 本期无新增公开路由；不动放行列表
  risk: 高
  owner: user-approved
  notes: 即使发现路由问题也先发 blocker-request

- path: next.config.ts
  operation: forbidden
  allowed: no
  reason: 本期不动构建配置
  risk: 高
  owner: user-approved
  notes: 默认禁改集

- path: next.config.js
  operation: forbidden
  allowed: no
  reason: 同上
  risk: 高
  owner: user-approved
  notes: 默认禁改集

- path: app/buser/layout.tsx
  operation: forbidden
  allowed: no
  reason: 全局布局不动
  risk: 高
  owner: user-approved
  notes: 不影响本期业务

- path: constants/menuConfig.ts
  operation: forbidden
  allowed: no
  reason: 菜单已含两个入口（zhangxia 2026-05-11 已加），不动
  risk: 中
  owner: user-approved
  notes: 若菜单文案需变更，发 blocker-request

- path: constants/pageTitles.ts
  operation: forbidden
  allowed: no
  reason: 页面标题已含两个，不动
  risk: 中
  owner: user-approved
  notes: 同上

- path: store/**
  operation: forbidden
  allowed: no
  reason: 不引入 zustand store；用 hook 内部 state
  risk: 中
  owner: user-approved
  notes: 不动全局 store

- path: services/buser/jobs/**
  operation: readonly
  allowed: no
  reason: 复用 searchJobPositionByEs；不修改其签名
  risk: 中
  owner: developer
  notes: 仅 import 使用

- path: lib/appMessage.ts
  operation: readonly
  allowed: no
  reason: 复用全局 message 单例
  risk: 低
  owner: developer
  notes: 仅 import 使用

- path: constants/mappers.ts
  operation: readonly
  allowed: no
  reason: 复用 checkResCode / unwrap
  risk: 低
  owner: developer
  notes: 仅 import 使用
```

## 4. 与本计划无关的其他文件

> Developer 在 Phase 1-4 实施过程中**严禁触碰**以下范围（包含但不限于）：
>
> - 其他 buser 域：`app/buser/{dashboard,jobs,jobsCreate,messages,records,settingsAccount,talents,workflow}/**`
> - 其他 buser 域：`components/buser/{dashboard,jobs,jobsCreate,messages,records,settingsAccount,talents,workflow}/**`
> - 其他 buser 域：`hooks/buser/{dashboard,jobs,jobsCreate,messages,records,settingsAccount,talents,workflow}/**`
> - 其他 buser 域：`types/buser/{dashboard,jobs,jobsCreate,messages,records,settingsAccount,talents,workflow}/**`
> - 其他 buser 域：`services/buser/{dashboard,jobs,jobsCreate,messages,records,settingsAccount,talents,workflow}/**`
> - cuser 域所有目录、share 域、login 域、common 工具（除上文 readonly 复用）
> - 任何 `__tests__ / __mocks__ / *.test.* / *.spec.*`（QA 阶段）
>
> 若 Developer 在实施中确实需要触碰，**发 from-developer-<seq>-blocker-request.md**，proposed_resume_to_agent: architect，等 Architect 补条目后再继续。

## 5. 汇总

- 新增文件数：**4**
  - `services/buser/resumeUpload/index.ts`
  - `services/buser/platformManagement/index.ts`
  - `hooks/buser/resumeUpload/baseHooks.ts`
  - `hooks/buser/platformManagement/baseHooks.ts`
- 修改文件数：**24**
  - 上传 12（含 styles 不动）
  - 平台管理 12（含 styles 不动）
- 删除文件数：**0**
- 显式 readonly 文件数：**8**
- 默认禁改集：**14**（package / lock × 6 + CI × 4 + Dockerfile + husky + eslintrc + tsconfig）
- 显式 forbidden（关键工程文件）：**9**（axiosConfig / middleware / next.config × 2 / layout / menuConfig / pageTitles / store / services/common/upload）
- 触碰默认禁改集（user-approved）：**0**

## 6. 边界声明

- 本计划之外的任何文件 = forbidden（即使是同目录新文件）。
- Developer 严禁触碰本计划之外的文件。
- 实施过程中发现需新增白名单外的文件 → 发 `from-developer-<seq>-blocker-request.md`（`message_type: blocker`、`intent: blocker_request`）让 Architect 补。
- 5 条门禁未达（Developer 在错误状态下被误启动）→ 发 `from-developer-<seq>-gate-failure-request.md`（`message_type: gate_failure`），不触发正式 Blocker、不改 state。
- 任何越界改动 = 系统级违规，必须回滚。
- AI dev mock：本期**不允许**（详 tech-plan §7 与 risk-plan R-02）。
- 新依赖：本期**不允许**。若 Developer 发现确实需要 → 发 blocker-request，由 Architect + 用户决策；新依赖必须写入本 plan 且 `owner: user-approved`。
