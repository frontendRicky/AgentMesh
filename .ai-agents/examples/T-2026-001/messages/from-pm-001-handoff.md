---
message_id: M-T-2026-001-002
task_id: T-2026-001
from_agent: pm
to_agent: architect
message_type: handoff
intent: pm-to-architect-handoff
summary: PM 阶段完成。已产出 6 份 artifacts/pm/* 文档（需求拆解 / API 契约 / 前端范围 / 状态-操作矩阵 / 风险与待确认 / Architect 输入包）。请 Architect 基于此输入产出 tech-plan / file-change-plan / risk-plan。
payload:
  requirement_artifact_id: A-T-2026-001-requirement-analysis
  api_contract_artifact_id: A-T-2026-001-api-contract-checklist
  frontend_scope_artifact_id: A-T-2026-001-frontend-scope
  state_action_matrix_artifact_id: A-T-2026-001-state-and-action-matrix
  risk_and_open_questions_artifact_id: A-T-2026-001-risk-and-open-questions
  architect_handoff_artifact_id: A-T-2026-001-architect-handoff
  open_questions:
    - OQ-01 接口路径与 axios baseURL 拼接
    - OQ-02 上传明细分析中行轮询策略
    - OQ-03 附件预览失败 fallback 实现细节
    - OQ-04 请求体 ID 字段类型统一 string 或保持 number
    - OQ-05 task.md 标题与实际需求不一致（Controller 处置）
    - OQ-06 触发 /analyze 后乐观更新策略
    - OQ-07 是否在 dev 环境引入 AI mock
  architect_must_answer:
    - 1. service 路径前缀是 /hire/... 还是 /api/v1/hire/...
    - 2. SWR 轮询策略
    - 3. 附件预览 fallback 实现
    - 4. ID 字段在请求体的类型统一策略
    - 5. /analyze 成功后的乐观更新模式
    - 6. 是否启用 AI dev mock 及 prod 排除策略
    - 7. 上传进度库选型（axios onUploadProgress vs XHR）
    - 8. confirm 失败重试策略落点（hook 或 service）
    - 9. ViewModel canXxx 推导字段放置层
    - 10. 详情弹窗与列表 SWR 联动策略
  high_priority_risks:
    - R-01 AI 成功回调 JSONB 写入失败（后端 bug，前端不补偿）
    - R-02 AI 提交接口当前 SKIP（需决策 dev mock）
    - R-09 数字字段 string/number 混用（DTO 联合类型 + mapper 收敛）
  human_review_focus:
    - "分析中 > 5min" 文案与阈值
    - 是否引入 AI dev mock
    - confirm 失败自动重试策略
    - 邀请 toast 文案避免误导"已送达"
    - 不允许修改清单与 file-change-plan 一致性
  default_forbidden_paths:
    - package.json / package-lock.json / pnpm-lock.yaml / yarn.lock
    - .github/** / .gitlab-ci.yml / Dockerfile / CI 配置
    - services/axiosConfig.ts
    - middleware.ts
    - next.config.* / tsconfig.json
    - 全局主题 / antd ConfigProvider
  next_action: architect_processing
referenced_artifacts:
  - A-T-2026-001-requirement-analysis
  - A-T-2026-001-api-contract-checklist
  - A-T-2026-001-frontend-scope
  - A-T-2026-001-state-and-action-matrix
  - A-T-2026-001-risk-and-open-questions
  - A-T-2026-001-architect-handoff
required_response: true
blockers: []
created_at: 2026-05-13T16:00:00+08:00
schema_version: a2a/v1
---

# PM → Architect Handoff

> PM 阶段完成。Architect 请按以下顺序读：
>
> 1. `artifacts/pm/requirement-analysis.md` —— 业务背景 / 角色 / 页面 / 流程 / 不做范围 / 验收口径
> 2. `artifacts/pm/api-contract-checklist.md` —— 16 个接口 × 字段类型 / 测试报告状态 / 异常处理
> 3. `artifacts/pm/frontend-scope.md` —— 需新增 / 修改 / 复用 / 不允许修改
> 4. `artifacts/pm/state-and-action-matrix.md` —— 上传状态 / 分析状态 / 5 Tab / 邀请状态 / 操作按钮规则
> 5. `artifacts/pm/risk-and-open-questions.md` —— 11 条风险 + 7 条 Open Question
> 6. `artifacts/pm/architect-handoff.md` —— 模块设计方向 + file-change-plan 粒度建议 + 必答问题 + Developer 拆分建议

## 关键摘要

- 后端 dev 环境 31/31 通过 + 1 SKIP（AI 提交接口未提供）；前端按契约对接，不补偿后端 bug。
- 列表 / 详情 / 状态流转 / 邀请 / 撤回 / 不合适 / 恢复 / 删除链路均已后端通过，前端可全量对接。
- 上传链路：移除 multipart 字段，**不实现分片续传**，只走 presign → PUT → confirm。
- 数字 / ID 字符串混用：DTO 联合类型 + mapper 内收敛；ID 全链路 `string`。
- 当前 task.md 标题"Pilot task"与本次需求不匹配，已记录为 OQ-05；不阻塞 Architect 阶段。

## Architect 输出预期

- `artifacts/architect/tech-plan.md`
- `artifacts/architect/file-change-plan.md`（覆盖本 handoff §2 列出的所有路径，且回答必答问题）
- `artifacts/architect/risk-plan.md`（补齐 PM 风险 + 引入 Architect 自己识别的实现风险）
- `messages/from-architect-001-handoff.md`（指向 Human Review）

PM 阶段不再产出额外内容。等待 Controller 推进 `state.current_status` 到 `architect_processing`。
