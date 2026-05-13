---
artifact_id: A-T-2026-001-requirement-analysis
task_id: T-2026-001
artifact_type: requirement
produced_by: pm
consumed_by:
  - architect
  - developer
  - qa
file_path: artifacts/pm/requirement-analysis.md
version: 1
status: ready
summary: 平台管理与批量简历上传前端需求拆解（来源仅限：后端技术方案 v0.0.0.5 与 20260513142206 测试报告）。
dependencies: []
validation_result: pass
validation_notes: 仅基于附带的两份文档，不臆造接口/字段/权限点/状态码。
created_at: 2026-05-13T16:00:00+08:00
schema_version: a2a/v1
---

# 需求拆解（Requirement Analysis）

## 1. 业务背景

- 平台管理模块用于沉淀外部简历，HR 在此筛选并推进候选人状态。
- 第一阶段（v0.0.0.5）收敛为：**HR 批量上传简历附件 → presign 直传 COS → confirm 确认 → 手动触发 AI 分析 → 成功入平台管理人才列表，失败留在上传页**。
- 后端 dev 环境已落地核心接口（见测试报告 `runId=20260513142206`），前端需对接已通过的接口；AI 提交接口暂未提供。

## 2. 用户角色

| 角色 | 范围 | 说明 |
|---|---|---|
| HR（BUser） | 唯一前端使用角色 | 在简历上传页、平台管理页操作；`companyId` 由登录上下文给出，前端不主动传 |
| 候选人 / 求职者 | 不在本前端范围 | 只通过收到的注册邮件链接外部进入注册流程 |
| 系统 | 后端 | 定时任务（未回应自动流转）、AI 回调（integration → hire） |

## 3. 页面范围（in-scope）

| 页面 | 说明 |
|---|---|
| 简历上传页 `app/buser/resumeUpload/page.tsx` | 批量上传 + presign/confirm + 上传统计 + 上传明细列表 + 批量绑定职位 + 批量删除 + 触发分析（多选/单条）+ 待分析 / 分析中 / 分析失败状态展示 |
| 平台管理页 `app/buser/platformManagement/page.tsx` | 5 Tab（人才池 / 感兴趣 / 邀请中 / 未回应 / 不合适）+ 列表 + 筛选 + 详情弹窗（基本信息 / AI 洞察 / 附件简历）+ 操作（感兴趣 / 邀请 / 重发 / 撤回 / 不合适 / 恢复 / 删除） |

## 4. 不做范围（out-of-scope）

- 关键词模糊搜索（后端未接 ES）
- 导出 Excel、列排序、自定义列、保存快捷筛选
- 候选人对比、拖拽排序
- 短信邀请、邮件打开追踪
- 在线简历转换、候选人注册后生成在线简历
- 多平台自动抓取、邮箱回流（仅保留 `sourceType` 字段不实现）
- AI 简历评估的批次表 / 批次级一键分析
- 修改 `package.json` / lock 文件 / 全局权限体系 / 无关页面
- 修改后端接口契约（如发现字段问题只能记录到 open-question，不允许前端绕过）

## 5. 核心流程

### 5.1 简历上传 → AI 分析

```text
HR 进入「简历上传」页
  → 选择多份附件（可暂不绑定岗位）
  → 前端逐文件调 /talent/resume/upload/presign（获取 cosKey + uploadUrl）
  → 前端 PUT 直传 COS
  → 前端调 /talent/resume/upload/confirm
  → 上传明细 uploadStatus=已上传, analysisStatus=待分析
  → HR 可批量调 /talent/resume/upload/bind-job 绑定职位
  → HR 选择已绑定职位的明细调 /talent/resume/analyze（多条/单条复用）
  → 分析状态 = 分析中
  → 等待 AI 回调（前端轮询 page 列表刷新状态）
  → 成功：进入平台管理人才池
  → 失败：保留在上传页，展示 failureReason（含"邮箱为空"）
```

### 5.2 平台管理 5 Tab 流转

```text
人才池(0)
  ├─ 标记感兴趣 → 感兴趣(1)
  ├─ 发送邀请 → 邀请中(2, inviteCount=1, inviteStatus=已发送)
  └─ 标记不合适 → 不合适(4)

感兴趣(1)
  ├─ 发送邀请 → 邀请中(2)
  └─ 标记不合适 → 不合适(4)

邀请中(2)
  ├─ 重发邀请（inviteStatus=已发送 且 inviteCount<3）→ 邀请中(2, inviteCount+1)
  ├─ 撤回邀请（仅 inviteStatus=已发送）→ 人才池(0)，inviteCount 保留
  ├─ 候选人注册成功（后端回调）→ inviteStatus=已注册，hrStatus 仍 2
  ├─ 标记不合适 → 不合适(4)
  └─ 定时任务（inviteCount=3 且 inviteExpireAt<now）→ 未回应(3)

未回应(3)
  └─ 标记不合适 → 不合适(4)

不合适(4)
  ├─ 恢复 → 人才池(0)
  └─ 删除（逻辑删除）
```

## 6. 验收口径

| 类别 | 口径 |
|---|---|
| 上传链路 | presign 成功返回 `uploadItemId/cosKey/uploadUrl`；前端 PUT 200；confirm 后 `uploadStatus=1, analysisStatus=0` |
| 上传统计 | `/talent/resume/upload/stat` 返回 `uploadSuccessCount / analyzingCount / lastFailedCount`，三个数字以 string 形式展示 |
| 上传明细列表 | `/talent/resume/upload/page` 按 `analysisStatus` 过滤，支持分页（请求字段：`current` / `size`） |
| 批量绑定职位 | `/talent/resume/upload/bind-job` 返回 `successCount / failedCount / items[]`；仅 `analysisStatus ∈ {0,2}` 的明细可绑定 |
| 批量删除 | `/talent/resume/upload/delete` 返回逐条结果；仅非分析中、非已导入的明细可删 |
| 触发分析 | `/talent/resume/analyze` 接受 `uploadItemIds[]`；多选与单条重试同接口（注意：当前测试报告标记为"跳过"，因为 AI 服务接收任务接口未提供，前端按契约对接即可） |
| 5 Tab 列表 | `/talent/resume/page` 以 `hrStatus ∈ {0,1,2,3,4}` 区分；分页字段 `current` / `size`，总数 `total`（string） |
| 详情弹窗 | `GET /talent/resume/{id}/ai-insight` 返回 `basicInfo / attachment / aiInsight` 三段 |
| 状态流转操作 | `interest / unsuitable / restore / invite / invite/resend / invite/recall / DELETE` 各自只对允许的 `hrStatus + inviteStatus` 组合可用，否则按"操作矩阵"隐藏或后端拒绝 |
| Long ID 处理 | 所有 ID（`uploadItemId / talentResumeId / jobId / companyId`）前端一律 `String` 全链路，不做 `Number` / `parseInt` 转换 |
| 数字字符串混用 | 后端返回的 `fileSize / inviteCount / total / current / pages / size / matchScore` 在测试报告中存在 string 形式，前端必须按 `string \| number` 兼容并兜底渲染 |

## 7. 待确认问题（open-questions，详见 risk-and-open-questions.md）

1. AI 成功回调后端 JSONB 写入失败（`highlights` 列类型 jsonb，但 MyBatis 传 varchar），前端是否需要为"`analysisStatus=分析中` 但长时间无回调"提供轮询超时提示？
2. AI 提交接口（`/talent/resume/analyze`）当前测试报告标记 SKIP，前端按契约实现即可，但需 Architect 在 file-change-plan 中明确 mock 开关（dev 是否注入 stub 数据）以解除阻塞。
3. 邮件到达需人工确认；前端是否需要在邀请成功 toast 中显式提示 HR"邮件已发送，请提醒候选人查收"？
4. `task.md` 标题 "Pilot task" 与本次实际需求不一致，建议 Controller 在 Architect 接手前以 message 形式确认 task 复用关系（仅 Controller 可改 state.md）。
