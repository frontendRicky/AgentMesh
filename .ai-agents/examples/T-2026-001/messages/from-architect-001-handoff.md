---
message_id: M-T-2026-001-004
task_id: T-2026-001
from_agent: architect
to_agent: human-review-actor
message_type: handoff
intent: architect_to_human_review_handoff
summary: Architect 阶段完成。已产出 tech-plan / file-change-plan / risk-plan，并附 gate-failure-request 留痕（state 仍 pm_processing）。等 Controller 推进状态 + Human Review Actor 写 architect-review.md。
payload:
  tech_plan_artifact_id: A-T-2026-001-tech-plan
  file_change_plan_artifact_id: A-T-2026-001-file-change-plan
  risk_plan_artifact_id: A-T-2026-001-risk-plan
  key_decisions:
    - service 路径不加 /api/v1（baseURL 已含）
    - 不引入新依赖（axios + swr + antd + clsx + tailwind-merge 全复用）
    - 不引入 AI dev mock；接受 dev 环境"分析中"为长期态
    - 不实现分片续传（后端已移除 multipart 字段）
    - 上传进度用 axios onUploadProgress + AbortController
    - confirm 失败：hook utility 退避重试 3 次 1s/2s/4s；不重发 PUT
    - presign 过期：首次 PUT 失败自动重申 1 次
    - 请求体 ID 字段全 string（与 07-type-id-field-convention 一致）
    - 触发 /analyze 后单条乐观更新 + mutate /upload/stat；不全表 mutate
    - canXxx 派生字段统一在 mapper 内生成
    - SWR refreshInterval：仅 parsing Tab + 行数>0 时 5000ms；其他场景关闭
    - 详情弹窗：iframe + onError fallback 下载；不引入预览代理
    - 列表 + 详情 SWR 联动：操作成功后 mutate 对应 Tab；邀请类操作同时 mutate 详情
    - 不修改 axiosConfig / middleware / next.config / tsconfig / lock / CI / Dockerfile / 全局主题 / 菜单 / 路由 / store
    - Phase 1-5 PR 拆分（类型/service → hooks → 上传组件 → 平台管理组件 → 联调）
  human_review_focus:
    - 1. R-02 是否允许引入 AI dev mock？（Architect 推荐：不引入）
    - 2. R-01 "分析中 > 5min" Tooltip 文案与阈值（Architect 默认 5min + 文案）
    - 3. R-04 confirm 失败 3 次 1s/2s/4s 退避是否接受
    - 4. R-05 presign 过期自动重申 1 次是否接受
    - 5. R-11 邀请 toast 文案是否接受
    - 6. OQ-04 请求体 ID 全 string 是否接受
    - 7. file-change-plan 28 条白名单 + 14 条默认禁改 + 9 条 forbidden 是否覆盖完整
    - 8. file-change-plan 中 "owner: user-approved" 项是否需要任何调整（本期默认 0 项 user-approved）
    - 9. 是否要 Controller 在 Human Review 推进前先处理 task.md "Pilot task" mismatch（R-12，Architect 倾向：不阻塞）
    - 10. Phase 1-5 PR 拆分粒度是否接受（每个 Phase 独立 PR）
  process_anomaly:
    - state.current_status 仍为 pm_processing；本阶段产出在用户显式授权下完成（详 from-architect-001-gate-failure-request.md）
    - Controller 在推进至 human_review_required 前应先把 pm_processing → architect_processing → architect_completed
  expected_next_agent: controller_then_human_review_actor
  expected_state_transitions:
    - pm_processing → architect_processing（Controller 拾起 from-pm-001-handoff，确认 PM artifacts ready）
    - architect_processing → architect_completed（Controller 校验本 handoff 与 3 个 architect artifacts）
    - architect_completed → human_review_required（Controller 推进至 Human Review；first step of two-step）
    - human_review_required + verdict approved → 第二步双步推进（详 ai-agents.mdc §8）
referenced_artifacts:
  - A-T-2026-001-tech-plan
  - A-T-2026-001-file-change-plan
  - A-T-2026-001-risk-plan
required_response: true
blockers: []
created_at: 2026-05-13T16:30:00+08:00
schema_version: a2a/v1
---

# Architect → Human Review Handoff

## 1. 阅读顺序

1. `artifacts/architect/tech-plan.md` —— 11 节方案 + PM must-answer 全部回答
2. `artifacts/architect/file-change-plan.md` —— 28 条白名单 + 14 条默认禁改 + 9 条 forbidden
3. `artifacts/architect/risk-plan.md` —— 12 条风险 + 6 条需 Human Review 拍板
4. `messages/from-architect-001-gate-failure-request.md` —— 流程留痕（state 未推进时 Architect 在用户授权下产出）

## 2. 关键决策摘要

- **最小可行方案**：复用 axios + swr + antd + 现有 styles；不引入任何新依赖；不动 axiosConfig / middleware / lock / CI。
- **上传链路**：presign → PUT (axios onUploadProgress + AbortController) → confirm (hook utility 退避重试)；presign 过期自动重申 1 次；**不实现分片续传**（后端已移除 multipart）。
- **分析链路**：`/analyze` SKIP 不阻塞前端实现；UI 接受 dev 环境"分析中"为长期态；Tooltip 提示 > 5min "AI 处理较慢"。
- **类型与 ID**：DTO 联合类型（`number | string | null`）+ mapper 唯一 normalize 点 + ID 全链路 `string`；请求体 ID 全 string。
- **canXxx 派生字段**：mapper 内一次生成，组件直读 boolean；不在组件 / hook 重复 if 判断。
- **SWR 策略**：仅"parsing Tab + 行数>0"时 refreshInterval=5000；其他场景 mutate 驱动；不引入 WebSocket / SSE。
- **乐观更新**：`/analyze` 单条更新 SWR cache + 并行 mutate `/upload/stat`，不全表 mutate。
- **详情预览**：iframe + onError fallback 下载；不引入 PDF.js / 预览代理。
- **列表-详情联动**：状态流转操作成功 → 关闭弹窗 + mutate Tab；邀请类操作 → 弹窗不关 + mutate Tab + mutate 详情。

## 3. Human Review 必看

按必要程度（详 risk-plan §5）：

1. R-02 AI dev mock：**Architect 推荐不引入**
2. R-01 "分析中 > 5min" 文案与阈值
3. R-04 confirm 退避策略
4. R-05 presign 自动重申
5. R-11 邀请 toast 文案
6. OQ-04 请求体 ID 全 string

可以快速 approve 的：

- file-change-plan 默认禁改集 + forbidden 列表（标准约束）
- canXxx 派生字段放 mapper（与项目规范一致）
- Phase 1-5 PR 拆分粒度

## 4. 流程异常说明

**state.md 未推进**。本阶段产出在用户显式授权下完成（详 `from-architect-001-gate-failure-request.md`）。

Controller 推进至 `human_review_required` 前必须先：

1. 校验 `from-pm-001-handoff.md` ready；
2. `state.current_status: pm_processing → architect_processing`；
3. 校验本 handoff + 3 个 architect artifacts；
4. `state.current_status: architect_processing → architect_completed`；
5. 准备进入 human_review_required（两步 Human Review 流程的第一步）。

**Human Review 双步**（ai-agents.mdc §8）：

1. 用户在对话中给 verdict（approved / rejected / needs_changes）；
2. Cursor 按用户指令代写 `human-reviews/architect-review.md`（reviewer 字段填用户 handle）；
3. Controller 推 `state.human_review_status = approved`（第一步）；
4. Controller 推 `state.current_status = developer_processing` + `state.current_agent = developer` + `state.next_agent = qa`（第二步，独立）。

**禁止**双步合并。

## 5. 输出物清单

| Artifact | 路径 | status |
|---|---|---|
| tech-plan | `artifacts/architect/tech-plan.md` | ready |
| file-change-plan | `artifacts/architect/file-change-plan.md` | ready |
| risk-plan | `artifacts/architect/risk-plan.md` | ready |
| gate-failure-request | `messages/from-architect-001-gate-failure-request.md` | — |
| handoff | `messages/from-architect-001-handoff.md`（本文件） | — |

Architect 阶段完成。**不写代码**。等待 Controller 推进 state + Human Review。
