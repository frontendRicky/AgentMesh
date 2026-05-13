# Global Rules — 全局规则

> 本系统所有 Agent / Controller / Cursor 必须遵守的全局规则。其他 rule 与本规则冲突时，以本规则为准。

## 1. 角色边界

- **PM Agent**：只产 PRD / requirement / task-breakdown / bug-brief / regression-scope；不写代码、不做技术决策
- **Architect Agent**：只产 tech-plan / file-change-plan / risk-plan；**严禁**任何源码 Write / StrReplace / Delete / Create
- **Senior FE Dev Agent**：写源码（**双门禁**），产 implementation-log / changed-files；只能改 file-change-plan 白名单中 operation ∈ {create, modify, delete} 且 allowed == yes 的文件
- **QA Agent**：产 test-report / acceptance-checklist / qa-file-change-plan；**默认主业务代码只读**，写测试文件须经 qa-file-change-plan 授权
- **Flow Controller**：调度 / 校验 / 状态流转 / 创建正式 Blocker；不写 artifacts/{pm,architect,developer,qa}/、不写源码、不写 human-reviews/
- **Human Review Actor**：用户给 verdict 后由 Cursor 代写 human-reviews/*.md

## 2. 阶段边界

- 每阶段必有上游 artifact / message 校验通过才能启动
- 每阶段必有下游交接（artifact + handoff message）
- 任一阶段缺产物 → 触发 Blocker（两阶段流程）
- **禁止跨阶段越权**（PM 写 tech-plan、Dev 写 PRD、QA 改业务代码 等）

## 3. 人工审核点（不可跳过）

- **Architect Review**（必经）：架构方案 + file-change-plan + 风险方案
- **Final Review**（必经）：测试报告 + 验收清单
- 审核必须是真人决策；Cursor 只能在用户给 verdict 后**代写** review record，不能模拟、不能伪造
- 审核翻转必须**双步**：第一步翻 *_status，第二步独立推 current_status

## 4. 禁止跳步

- 不允许：original_request → 直接写代码
- 不允许：PRD → 直接写代码（缺 Architect / 缺审核）
- 不允许：Architect → 直接写代码（缺审核）
- 不允许：Dev → 直接交付（缺 QA / 缺 Final Review）
- 不允许：QA → 直接 completed（缺 Final Review）
- 不允许：Final Review → final-delivery（必须 final_review_status == approved AND current_status == completed 同时满足）

## 5. 禁止越权

- Agent 严禁写其他 role 的 `artifacts/<role>/`
- Agent 严禁写 `state.md`（仅 Controller）
- Agent 严禁写 `blockers/**`（仅 Controller，且必须基于 blocker request 或自校验失败）
- Agent 严禁写 `human-reviews/**`（仅 Human Review Actor）
- Controller 严禁写 `artifacts/{pm,architect,developer,qa}/`
- Controller 严禁写 `human-reviews/**`
- Controller 严禁写源码
- 任何角色都严禁绕过双门禁写源码

## 6. 输出格式要求

- 所有 Cursor 回复必须以 `[A2A]` 头开始（详见 cursor-rules.md）
- 所有产物必须含完整 frontmatter（按对应 schema）
- 所有产物必须含 `task_id` / `schema_version` / `created_at`
- 所有产物按文件类型补对应主键（artifact_id / message_id / blocker_id / review_id / contract_id）
- Artifact 必含 `produced_by` / `consumed_by` / `status` / `validation_result`

## 7. 冲突优先级

当多个 rule 给出不一致指示时：

1. **global-rules.md**（本规则）
2. **a2a-rules.md**（16 条硬约束）
3. **cursor-rules.md**（Cursor 操作规则）
4. **code-change-rules.md** / **review-rules.md** / **test-rules.md**
5. **frontend-rules.md**

行为规则与 schema 规则冲突时，schema 规则为准（因 schema 决定可被自动校验的边界）。

## 8. 轻量模式

允许在简单任务中使用轻量模式：

- ✅ 缩短模板（如 PRD 压到 1 页、tech-plan 压到 5 节）
- ❌ **禁止合并 Agent 职责**（不允许 PM 兼写 tech-plan）
- ✅ 仍必须有 task / state / message / artifact / handoff
- ✅ 仍必须经过 Architect Review 与 Final Review
- ❌ **禁止跳过审核**

## 9. 标"待确认"原则

任何不确定点（用户未明示、需求模糊、技术未验证）必须**显式标"待确认"**，不能假设、不能臆断。"待确认"出现在 PRD 与 tech-plan 中是合法的，由用户在审核时给出方向。
