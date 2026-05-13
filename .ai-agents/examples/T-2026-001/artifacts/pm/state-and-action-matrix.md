---
artifact_id: A-T-2026-001-state-and-action-matrix
task_id: T-2026-001
artifact_type: state_action_matrix
produced_by: pm
consumed_by:
  - architect
  - developer
  - qa
file_path: artifacts/pm/state-and-action-matrix.md
version: 1
status: ready
summary: 上传状态 / 分析状态 / HR 5 Tab / 邀请状态 / 操作按钮显隐 / 禁用规则一览。
dependencies:
  - A-T-2026-001-requirement-analysis
  - A-T-2026-001-api-contract-checklist
validation_result: pass
validation_notes: 显隐与禁用规则可直接转 ViewModel `canXxx` 标志或 hook 层 `boolean` 暴露，避免组件内重复判断。
created_at: 2026-05-13T16:00:00+08:00
schema_version: a2a/v1
---

# 状态与操作矩阵

## 1. 上传状态矩阵（`talent_resume_upload_item.uploadStatus`）

| code | 枚举 | 中文 | 前端展示 | 进入条件 |
|---|---|---|---|---|
| 0 | `PENDING_UPLOAD` | 待上传 | 不在 UI 主流程展示（presign 已创建明细但 PUT 未完成） | presign 返回 |
| 1 | `UPLOADED` | 已上传 | 上传明细列表正常行 | confirm 成功 |
| 2 | `UPLOAD_FAILED` | 上传失败 | 上传队列内单条错误态 + 错误文案 | PUT COS 失败 / confirm 业务错误 |

> 上传队列与上传明细列表是两个域：上传队列是前端瞬时态（含 0/2），明细列表只展示后端持久态（仅 1）。

## 2. 分析状态矩阵（`talent_resume_upload_item.analysisStatus`）

| code | 枚举 | 中文 | 上传页是否展示 | 触发条件 | 备注 |
|---|---|---|---|---|---|
| 0 | `PENDING_ANALYSIS` | 待分析 | 是 | confirm 成功 | 允许"绑定职位" + "分析" + "删除" |
| 1 | `ANALYZING` | 分析中 | 是 | `/analyze` 成功返回 | 禁止"绑定职位" + "分析" + "删除" |
| 2 | `ANALYSIS_FAILED` | 分析失败 | 是 | AI 回调失败 / 邮箱为空 | 允许"重新分析"+"绑定职位"+"删除"；失败原因走 `failureReason` |
| 3 | `IMPORTED` | 已导入平台管理 | 否（已迁移到平台管理列表） | AI 回调成功，主表写入 | 不在上传页展示，不允许任何上传明细操作 |

显隐 / 禁用规则：

| 操作 | 0 待分析 | 1 分析中 | 2 分析失败 | 3 已导入 |
|---|---|---|---|---|
| 单选 row | 允许 | 允许（仅查看）| 允许 | 不展示 |
| 批量绑定职位 | 允许 | 禁用（tooltip：分析中不可改） | 允许 | 不展示 |
| 批量删除 | 允许 | 禁用（tooltip：分析中不可删） | 允许 | 不展示 |
| 批量分析 | 允许（须已绑定职位） | 禁用 | 允许（"重新分析"语义） | 不展示 |
| 单条"重新分析" | 不展示 | 不展示 | 显示（须已绑定职位） | 不展示 |

ViewModel 推导字段（建议在 mapper 内一次生成，供组件直接消费）：

```text
isPendingAnalysis: analysisStatus === 0
isAnalyzing:      analysisStatus === 1
isAnalysisFailed: analysisStatus === 2
isImported:       analysisStatus === 3
canBindJob:       analysisStatus === 0 || analysisStatus === 2
canDelete:        analysisStatus === 0 || analysisStatus === 2
canAnalyze:       (analysisStatus === 0 || analysisStatus === 2) && jobId != null
canRetry:         analysisStatus === 2 && jobId != null
```

## 3. HR 5 Tab 状态矩阵（`talent_resume.hrStatus`）

| code | 枚举 | 中文 | Tab key | 列表请求 | 默认排序 |
|---|---|---|---|---|---|
| 0 | `TALENT_POOL` | 人才池 | `talentPool` | `hrStatus=0` | createdAt desc / matchScore desc（待 Architect 收敛） |
| 1 | `INTERESTED` | 感兴趣 | `interested` | `hrStatus=1` | 最近标记感兴趣时间 desc |
| 2 | `INVITING` | 邀请中 | `inviting` | `hrStatus=2` | 最近邀请时间 desc / 有效期 |
| 3 | `NO_RESPONSE` | 未回应 | `noResponse` | `hrStatus=3` | 过期时间 desc |
| 4 | `UNSUITABLE` | 不合适 | `unsuitable` | `hrStatus=4` | 标记不合适时间 desc |

列展示差异（PRD §3.1）：

| 列 | 人才池 | 感兴趣 | 邀请中 | 未回应 | 不合适 |
|---|---|---|---|---|---|
| 姓名/联系电话 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 投递/绑定职位 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 简历评分 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 风险数量 | ✓ | ✓ |  |  |  |
| 年龄 / 工作年限 / 学历 / 学校 / 求职状态 | ✓ | ✓ |  |  |  |
| 简历附件入口 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 邀请状态 |  |  | ✓ | ✓ |  |
| 邀请次数 |  |  | ✓ | ✓ |  |
| 有效期至 |  |  | ✓ |  |  |
| 过期时间 |  |  |  | ✓ |  |
| 不合适原因 |  |  |  |  | ✓ |
| 标记时间 |  |  |  |  | ✓ |
| 操作 | ✓ | ✓ | ✓ | ✓ | ✓ |

## 4. 邀请状态矩阵（`talent_resume.inviteStatus`）

| code | 枚举 | 中文 | 仅在 `hrStatus=2` 有意义 |
|---|---|---|---|
| 0 | `NOT_INVITED` | 未邀请 | 默认或撤回后 |
| 1 | `SENT` | 已发送 | 邀请已发送，候选人尚未注册 |
| 2 | `REGISTERED` | 已注册 | 候选人完成注册（`hrStatus` 保持 2） |

邀请次数规则（PRD §6.6）：

- `inviteCount` 取值 0..3；首次邀请后为 1；重发递增；撤回不重置；
- 达到 3 后不能再发邀请（前端按钮 disabled + tooltip："邀请次数已达 3 次"）；
- `inviteExpireAt = now + 7 天`（重发刷新）；
- 撤回后 `hrStatus=0`、`inviteStatus=0`、`inviteToken / inviteExpireAt` 清空，`inviteCount` 保留。

定时任务（前端不调）：

- `hrStatus=2 AND inviteStatus=1 AND inviteCount=3 AND inviteExpireAt<now` → `hrStatus=3 (未回应)`

## 5. 操作按钮显示 / 隐藏 / 禁用规则（行操作）

> 命名规则：✓=显示 / ⊘=隐藏 / ⚠=显示但 disabled（tooltip 说明原因）。
> 通用：所有按钮在 submitting 状态 disabled；当前行已被乐观更新或 mutate 中也 disabled。

| 操作 | 人才池(0) | 感兴趣(1) | 邀请中(2) | 未回应(3) | 不合适(4) | 触发接口 |
|---|---|---|---|---|---|---|
| 标记感兴趣 | ✓ | ⊘ | ⊘ | ⊘ | ⊘ | `POST /interest` |
| 邀请注册 | ✓ | ✓ | ⊘ | ⊘ | ⊘ | `POST /invite` |
| 重发邀请 | ⊘ | ⊘ | ✓ 仅 `inviteStatus=1 且 inviteCount<3`；`inviteCount=3` 时 ⚠ tooltip："次数已达上限"；`inviteStatus=2 已注册` 时 ⊘ | ⊘ | ⊘ | `POST /invite/resend` |
| 撤回邀请 | ⊘ | ⊘ | ✓ 仅 `inviteStatus=1`；`inviteStatus=2 已注册` 时 ⊘ | ⊘ | ⊘ | `POST /invite/recall` |
| 标记不合适 | ✓ | ✓ | ✓ | ✓ | ⊘ | `POST /unsuitable`（弹原因 modal） |
| 恢复 | ⊘ | ⊘ | ⊘ | ⊘ | ✓ | `POST /restore` |
| 删除 | ⊘ | ⊘ | ⊘ | ⊘ | ✓（需二次确认） | `DELETE /{id}` |
| 查看附件简历 | ✓ | ✓ | ✓ | ✓ | ✓ | 打开 PreviewModal，调用 `GET /{id}/ai-insight` 获取详情 |

按钮文案待 Architect 与设计稿对齐（fallback 文案：感兴趣 / 邀请注册 / 重发邀请 / 撤回邀请 / 不合适 / 恢复 / 删除 / 查看附件）。

## 6. 邮箱前置校验（前端兜底，仍以后端为权威）

- 详情接口返回 `basicInfo.email` 为空时：
  - 列表层一般不显示空邮箱记录（PRD §6.6："邮箱为空的简历不会进入平台管理列表"），无需前端隐藏；
  - 但 PRD §6.6 仍要求邀请接口兜底校验邮箱为空并返回业务错误 `EMAIL_EMPTY`：前端 `invite / invite/resend` 失败时按 axios 拦截统一 toast。

## 7. 不合适原因（`unsuitableReasonType`）

| code | 中文 | reasonRemark |
|---|---|---|
| 1 | 经验不符 | 非必填 |
| 2 | 技能不匹配 | 非必填 |
| 3 | 薪资期望过高 | 非必填 |
| 4 | 其他 | **必填**，最多 500 字 |

Modal 内 Form 校验：

- `reasonType` 必填（Select option value 为 number，form value 一致 number）。
- `reasonRemark` 仅在 `reasonType === 4` 必填；`maxLength=500`；超过截断或前端 Form rule 报错。

## 8. 全局态约束

| 态 | 单一来源 | 备注 |
|---|---|---|
| 上传队列（前端瞬时） | `useResumeUploadPage` 内 `fileQueue` | 不与上传明细列表混存 |
| 上传明细列表 loading | `useResumeUploadPage` 内 SWR `isLoading` | 单一来源 |
| 上传明细列表 mutate | SWR `mutate` | 触发"绑定 / 删除 / 分析"后单点调用 |
| 上传统计 mutate | 独立 SWR | 在"上传 / 删除 / 分析"成功后联动 mutate |
| 平台管理列表 | `usePlatformManagementPage` 内 SWR | 切 Tab / 筛选变化时重置 `current=1` |
| 详情弹窗 | controller hook 内 `modalOpen / currentId` | 关闭时 reset；提交 / detail loading 分别独立 loading |
| Toast | hook 层调，单次 | service 不调；page catch 不重复 |
