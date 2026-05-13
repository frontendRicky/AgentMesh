---
artifact_id: A-T-2026-001-api-contract-checklist
task_id: T-2026-001
artifact_type: api_contract_checklist
produced_by: pm
consumed_by:
  - architect
  - developer
  - qa
file_path: artifacts/pm/api-contract-checklist.md
version: 1
status: ready
summary: 前端需对接的全部后端接口清单，含字段类型风险与测试报告状态；网关前缀按现有 axios 配置 `/api/v1` 走，业务路径见各项。
dependencies:
  - A-T-2026-001-requirement-analysis
validation_result: pass
validation_notes: 字段与示例均来源 PRD §1-§3 与测试报告 §1-§32；未在两份文档出现的字段不在本清单内。
created_at: 2026-05-13T16:00:00+08:00
schema_version: a2a/v1
---

# API 契约 Checklist

## 0. 通用约定

- 业务路径按 PRD：`/talent/resume/...` 与 `/integration/callback/...`；测试报告中真实命中网关前缀为 `https://app-dev.succaiss.com/api/v1/hire/...`，对应前端 axios `baseURL` 已含 `/api/v1`，调用时只填 `/hire/talent/resume/...`（详 frontend-scope.md §2）。
- `companyId` 不由前端传，全部从登录上下文取（已在测试报告中验证）。
- 成功响应统一 `{ code: 200, data: <T>, message: "成功", timestamp: <string> }`；`code !== 200` 走 `checkResCode` 走业务异常通道。
- 时间统一 `yyyy-MM-dd HH:mm:ss`；前端只做展示，不做时区转换。
- 分页请求字段为 `current / size`（测试报告所示）；不是 PRD §1.3 的 `page / size`，**前端以测试报告为准**。
- 分页返回字段中 `current / size / pages / total` 均为 string；记录数组在 `records`。
- 所有 Long ID 字段在测试报告响应中均为 string，前端按 string 处理。

## 1. 简历上传链路

### 1.1 创建上传明细 / 申请预签名

- method: `POST`
- path: `/hire/talent/resume/upload/presign`
- request:
  ```json
  { "jobId": 2045092622891720706, "fileName": "post-success.pdf", "contentType": "application/pdf", "contentDisposition": "inline", "fileSize": 75 }
  ```
- response (data):
  ```json
  {
    "uploadItemId": "2054447072525656066",
    "jobId": "2045092622891720706", "jobName": "测试公司",
    "fileName": "post-success.pdf", "fileSize": "75",
    "cosKey": "Company_Information/.../post-success.pdf",
    "cosUrl": "https://bucket-xxx.cos.../post-success.pdf",
    "uploadUrl": "https://bucket-xxx.cos.../post-success.pdf?sign=...",
    "bucket": "bucket-1387128439", "region": "ap-guangzhou",
    "expireAt": "2026-05-13 14:32:06",
    "uploadStatus": 0, "uploadStatusName": "待上传",
    "analysisStatus": 0, "analysisStatusName": "待分析",
    "aiTaskId": null, "analysisStartedAt": null, "analysisCompletedAt": null,
    "failureReason": null, "talentResumeId": null, "uploadedAt": null
  }
  ```
- 字段类型风险：`uploadItemId / jobId / fileSize` 返回 string；`bucket / region / expireAt` 可能为 null（confirm 后）。
- 是否已通过：是（测试 §1, §4, §7）
- 前端使用场景：批量上传逐文件申请 cosKey/uploadUrl；记录 `uploadItemId + cosKey` 用于 confirm。
- 异常处理：
  - 业务错误（`code !== 200`）由 axios 拦截统一 toast；hook 层不重复 toast。
  - `expireAt` 已过（>10min）→ 重新调 presign（生成新 `uploadItemId / cosKey`）。
- 备注：本期后端已**移除 `uploadMode / multipartUploadId`**（测试报告"断点续传残留"项 `upload_columns_no_multipart=0`），前端不传不接，**不实现分片续传**。

### 1.2 确认上传完成

- method: `POST`
- path: `/hire/talent/resume/upload/confirm`
- request:
  ```json
  { "uploadItemId": "2054447072525656066", "cosKey": "Company_Information/.../post-success.pdf", "fileName": "post-success.pdf", "fileSize": 75, "contentType": "application/pdf" }
  ```
- response (data): 同 1.1，`uploadStatus=1 / uploadStatusName="已上传"`，`uploadedAt` 有值，`bucket / region / uploadUrl / expireAt = null`。
- 字段类型风险：`fileSize` 请求为 number、响应为 string；前端请求时按 number 传，展示时按 string 兜底。
- 是否已通过：是（测试 §3, §6, §9）
- 前端使用场景：PUT COS 成功后调用，触发后端写入上传明细。
- 异常处理：
  - 同一 `uploadItemId + cosKey` 重试幂等（PRD §2.7）；前端按 toast 错误 + 允许"重试 confirm"按钮处理网络中断场景。
  - PUT COS 已成功但 confirm 失败：前端展示"上传完成但确认失败，请重试"，重试同一份不重新申请 presign（PRD §2.7 第 1 条）。

### 1.3 上传统计

- method: `POST`
- path: `/hire/talent/resume/upload/stat`
- request: `null`
- response (data):
  ```json
  { "uploadSuccessCount": "8", "analyzingCount": "0", "lastFailedCount": "1" }
  ```
- 字段类型风险：三个字段均为 string；前端 ViewModel 转 number 仅用于展示，不做计算。
- 是否已通过：是（测试 §10）
- 前端使用场景：上传页头部统计卡片 + Tab 数字徽标。
- 异常处理：列表刷新 / 触发分析 / 删除 / 绑定职位之后通过 SWR mutate 重新拉取。

### 1.4 上传明细分页

- method: `POST`
- path: `/hire/talent/resume/upload/page`
- request:
  ```json
  { "current": 1, "size": 20, "analysisStatus": 0 }
  ```
- response (data):
  ```json
  {
    "current": "1", "size": "20", "pages": "1", "total": "n",
    "records": [
      { "uploadItemId": "...", "jobId": "..." | null, "jobName": "..." | null,
        "fileName": "...", "fileSize": "...",
        "uploadStatus": 1, "uploadStatusName": "已上传",
        "analysisStatus": 0|1|2|3, "analysisStatusName": "...",
        "failureReason": "..." | null, "talentResumeId": "..." | null,
        "cosKey": "...", "cosUrl": "...",
        "aiTaskId": "..." | null,
        "uploadedAt": "...", "analysisStartedAt": null | "...", "analysisCompletedAt": null | "..." }
    ]
  }
  ```
- 字段类型风险：分页字段全部 string；`failureReason` 当 `analysisStatus=2` 时含中文文案（如"邮箱为空"）。
- 是否已通过：是（测试 §11，请求字段实测为 `current / size`，**不是** PRD §1.3 的 `page / size`）。
- 前端使用场景：上传页明细 Table；按 `analysisStatus` 切换"待分析 / 分析中 / 分析失败"子 Tab。
- 异常处理：空列表展示 empty 态；筛选条件变化重置 `current=1`。

### 1.5 批量绑定 / 修改职位

- method: `POST`
- path: `/hire/talent/resume/upload/bind-job`
- request: `{ "uploadItemIds": ["..."], "jobId": 2045092622891720706 }`（请求 `jobId` 可以是 number；后端按 long 解析；前端为安全统一传 number 字面量是否安全待 Architect 确认，**建议字符串化**——见 risk-and-open-questions §字段类型）
- response (data): `{ "successCount": 1, "failedCount": 0, "items": [{ "uploadItemId": "...", "success": true, "failureReason": null }] }`
- 字段类型风险：`uploadItemIds[]` 元素为 string；`jobId` 是 number 还是 string 待 Architect 在 file-change-plan 中确认（测试报告 §12 入参传 number，**也通过**）。
- 是否已通过：是（测试 §12）
- 前端使用场景：上传页批量绑定/修改职位；选择"待分析 / 分析失败"明细后弹 modal。
- 异常处理：返回 `failedCount > 0` 时，按 `items[]` 中 `failureReason` 列表展示失败原因；成功项刷新列表。

### 1.6 批量删除上传明细

- method: `POST`
- path: `/hire/talent/resume/upload/delete`
- request: `{ "uploadItemIds": ["..."] }`
- response (data): 结构同 1.5
- 字段类型风险：同上。
- 是否已通过：是（测试 §13）
- 前端使用场景：上传页批量删除按钮；仅非"分析中 / 已导入"的明细可删。
- 异常处理：同 1.5；删除成功后 mutate 列表 + 统计。

## 2. AI 分析

### 2.1 触发 AI 分析（多选 / 单条重试同接口）

- method: `POST`
- path: `/hire/talent/resume/analyze`
- request: `{ "uploadItemIds": ["..."] }`
- response (data):
  ```json
  { "items": [ { "uploadItemId": "...", "aiTaskId": "...", "analysisStatus": 1, "analysisStatusName": "分析中" } ] }
  ```
- 字段类型风险：本期前端不需要消费 `aiTaskId` 字段（仅后端追踪），但需校验返回结构存在。
- 是否已通过：**SKIP**（测试 §14；AI 服务接收任务接口尚未提供，但前端按契约对接即可）。
- 前端使用场景：上传页"批量分析"按钮 + 失败行"重新分析"按钮，共用同一 service。
- 异常处理：业务错误 toast；触发成功后通过 SWR mutate 刷新明细 + 统计；分析中状态由轮询 1.4 列表更新。

### 2.2 AI 外部回调（不由前端调用，仅记录）

- method: `POST`
- path: `/integration/callback/talent-resume-ai`
- 是否已通过：通过（测试 §15），但后端有 JSONB 写入风险（详 §3 风险），前端只需感知"分析中"长期不更新需提示用户。

### 2.3 AI 内部回调（不由前端调用，仅记录）

- method: `POST`
- path: `/hire/talent/resume/ai/callback`
- 是否已通过：是（测试 §16，邮箱为空流程通过）

## 3. 平台管理

### 3.1 列表分页

- method: `POST`
- path: `/hire/talent/resume/page`
- request:
  ```json
  { "current": 1, "size": 20, "hrStatus": 0, "jobId": null, "sourceType": null, "education": null, "workExperience": null, "jobSearchStatus": null, "gender": null, "industryExperience": null, "deliveryStatus": null }
  ```
- response (data):
  ```json
  {
    "current": "1", "size": "20", "pages": "1", "total": "n",
    "records": [
      { "id": "...", "candidateName": "...", "phone": "138****0000",
        "jobId": "...", "jobName": "...", "expectedJob": "...",
        "matchScore": 91.0, "riskCount": 0,
        "age": null|28, "workExperience": null|"5年",
        "education": null|"本科", "schoolName": null|"南京大学",
        "gender": null|"男", "industryExperience": null|"互联网", "jobSearchStatus": null|"...",
        "resumeAttachmentPreviewUrl": "https://...",
        "hrStatus": 0|1|2|3|4, "hrStatusName": "人才池|...",
        "inviteStatus": 0|1|2, "inviteStatusName": "未邀请|已发送|已注册",
        "inviteCount": 0, "inviteExpireAt": null|"...", "inviteSentAt": null|"...",
        "unsuitableReasonType": null|1..4, "unsuitableReasonName": null|"...",
        "unsuitableReasonRemark": null|"...", "unsuitableMarkedAt": null|"...",
        "createdAt": "..." }
    ]
  }
  ```
- 字段类型风险：
  - `id / jobId` 为 string Long ID。
  - `matchScore` 为 number；`riskCount / inviteCount` 为 number；但分页字段 `current/size/pages/total` 为 string，**不能混合处理**。
  - `phone` 已脱敏（`138****0000`），前端直接渲染，不再处理。
- 是否已通过：是（测试 §17, §18, §21, §23, §29）
- 前端使用场景：5 Tab 列表统一来源；按 `hrStatus` 区分 Tab；其它筛选项作为 optional 入参。
- 异常处理：空列表 empty 态；分页 mutate；筛选变化重置 `current=1`。
- 备注：**不支持 keyword 模糊搜索**（PRD §3.2，后端未接 ES）；前端 UI 移除搜索框或 disabled+tooltip。

### 3.2 详情（AI 洞察）

- method: `GET`
- path: `/hire/talent/resume/{id}/ai-insight`
- response (data):
  ```json
  {
    "id": "...",
    "basicInfo": { "candidateName": "...", "phone": "...", "email": "...", "jobName": "...", "expectedJob": "...", "age": null, "gender": null, "workExperience": null, "education": null, "schoolName": null, "industryExperience": null, "jobSearchStatus": null },
    "attachment": { "fileName": "...", "fileSize": "75", "previewUrl": "...", "downloadUrl": "...", "uploadedAt": "..." },
    "aiInsight": { "matchScore": 91.0, "summary": "...", "highlights": [], "riskPoints": [], "interviewSuggestions": [], "completedAt": "..." }
  }
  ```
- 字段类型风险：
  - `fileSize` string；`matchScore` number；
  - `highlights / riskPoints / interviewSuggestions` 三个数组在测试报告中可能为 `[]`（因 §3 JSONB 写入失败导致主表写不进去时，详情走的是平台管理模拟数据，AI 字段为空），前端必须支持空数组与 null。
- 是否已通过：是（测试 §19）
- 前端使用场景：详情弹窗三 Tab：基本信息 / AI 洞察 / 附件简历。
- 异常处理：详情接口 404 / 业务错误 → 弹窗内显示 error 态 + 关闭按钮可用。
- 备注：**`attachment.previewUrl` 与 `downloadUrl` 当前响应中实测为同一个 COS 直链**（未经预览代理），前端按"先预览失败 → fallback 下载"逻辑兜底（PRD §3.3）。

### 3.3 状态流转 / 操作

| 操作 | method | path | request | 已通过 | 前端使用场景 |
|---|---|---|---|---|---|
| 标记感兴趣 | POST | `/hire/talent/resume/{id}/interest` | 空 | 是（§20） | 行操作（仅人才池 0） |
| 标记不合适 | POST | `/hire/talent/resume/{id}/unsuitable` | `{reasonType: 1\|2\|3\|4, reasonRemark?: string}`（`reasonType=4` 时 `reasonRemark` 必填，最多 500） | 是（§28, §31） | 行操作（除"不合适"Tab 外均可见） |
| 恢复人才池 | POST | `/hire/talent/resume/{id}/restore` | 空 | 是（§30） | 行操作（仅不合适 4） |
| 删除 | DELETE | `/hire/talent/resume/{id}` | 空 | 是（§32） | 行操作（仅不合适 4） |
| 发送邀请 | POST | `/hire/talent/resume/{id}/invite` | 空 | 是（§22, §26） | 行操作（人才池 0 或 感兴趣 1） |
| 重发邀请 | POST | `/hire/talent/resume/{id}/invite/resend` | 空 | 是（§24） | 行操作（邀请中 2 且 inviteStatus=已发送 且 inviteCount<3） |
| 撤回邀请 | POST | `/hire/talent/resume/{id}/invite/recall` | 空 | 是（§25） | 行操作（邀请中 2 且 inviteStatus=已发送） |
| 注册回调 | POST | `/hire/talent/resume/invite/register-callback` | `{inviteToken, registeredUserId, registeredAt}` | 是（§27） | **不由本前端调用**（系统内部接口） |

字段类型风险：

- 状态流转返回的 `fromStatus / toStatus` 为 number；`hrStatus / inviteStatus` 全部 number；`previousInviteCount / inviteCount / maxInviteCount` number。
- `reasonType` 入参为 number；前端 Select option value 用 number，与 form 字段类型保持一致。

异常处理：

- 业务错误码（PRD §3.13）：
  - `INVALID_HR_STATUS` / `EMAIL_EMPTY` / `INVITE_COUNT_EXCEEDED` / `INVITE_NOT_SENT` / `INVITE_ALREADY_REGISTERED` / `DELETE_NOT_ALLOWED` / `UNSUITABLE_REASON_REQUIRED` / `TALENT_RESUME_NOT_FOUND` —— 由 axios 拦截统一弹 toast；不在前端硬编码兜底文案，沿用后端 `message`。
  - 前端按"操作矩阵"在 UI 上隐藏 / disabled 不合法操作以减少业务错误率；但仍以后端校验为权威。

## 4. 不调接口（仅记录）

- 定时任务（未回应自动流转）：PRD §3.12，无 HTTP 接口，不由前端触发；前端只通过 3.1 列表展示流转结果。

## 5. Checklist 汇总

| # | path | method | 测试报告 | 备注 |
|---|---|---|---|---|
| 1.1 | `/hire/talent/resume/upload/presign` | POST | 通过 | 移除 uploadMode |
| 1.2 | `/hire/talent/resume/upload/confirm` | POST | 通过 | 幂等 |
| 1.3 | `/hire/talent/resume/upload/stat` | POST | 通过 | 三字段均 string |
| 1.4 | `/hire/talent/resume/upload/page` | POST | 通过 | `current/size` |
| 1.5 | `/hire/talent/resume/upload/bind-job` | POST | 通过 | jobId 类型待 Architect 收敛 |
| 1.6 | `/hire/talent/resume/upload/delete` | POST | 通过 | 仅非分析中/已导入 |
| 2.1 | `/hire/talent/resume/analyze` | POST | SKIP | AI 接收任务接口未提供 |
| 3.1 | `/hire/talent/resume/page` | POST | 通过 | 不支持 keyword |
| 3.2 | `/hire/talent/resume/{id}/ai-insight` | GET | 通过 | AI 字段可能为空数组 |
| 3.3a | `/hire/talent/resume/{id}/interest` | POST | 通过 |  |
| 3.3b | `/hire/talent/resume/{id}/unsuitable` | POST | 通过 | reasonType=4 → reasonRemark 必填 |
| 3.3c | `/hire/talent/resume/{id}/restore` | POST | 通过 |  |
| 3.3d | `/hire/talent/resume/{id}` | DELETE | 通过 | 仅不合适 4 |
| 3.3e | `/hire/talent/resume/{id}/invite` | POST | 通过 | 仅 0/1 |
| 3.3f | `/hire/talent/resume/{id}/invite/resend` | POST | 通过 | inviteCount<3 且 inviteStatus=1 |
| 3.3g | `/hire/talent/resume/{id}/invite/recall` | POST | 通过 | inviteStatus=1 |
