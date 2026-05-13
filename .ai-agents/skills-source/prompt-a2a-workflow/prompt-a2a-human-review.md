# A2A Human Review Stage Prompt

> 由 `prompt-a2a-workflow/SKILL.md` 在 `state.current_status == human_review_required` 或 `final_review_required` 时调用。
> 包含 Architect Review 和 Final Review 两段模板。

## 前置条件

- `current_status` 是 `human_review_required` 或 `final_review_required`
- 对应 artifacts 已就绪：
  - architect review → artifacts/architect/{tech-plan,file-change-plan,risk-plan}.md
  - final review → artifacts/qa/test-report.md + artifacts/developer/changed-files.md

## 重要：Cursor 不自行翻状态

按 `.cursor/rules/ai-agents.mdc` §8：

- **禁止** Cursor 自行翻 `human_review_status` / `final_review_status`
- 用户必须先在对话中给出 verdict（approved / rejected / needs_changes）
- Cursor 按用户指令**代写** review record（reviewer 字段填用户 handle）
- 然后召唤 Controller 校验 review record → **双步翻状态**

---

## 模板 A：Architect Review Prompt（user 视角）

发给用户的 Prompt，让用户做出 verdict：

```md
# Human Review · Architect Stage：<T-YYYY-NNN>

## 待审材料
- artifacts/architect/tech-plan.md
- artifacts/architect/file-change-plan.md
- artifacts/architect/risk-plan.md
- messages/from-architect-<seq>-handoff.md

## 必须确认的决策点（请逐项 ✅ / ❌ / 修改建议）

### 范围
- [ ] file-change-plan 白名单是否完整覆盖目标改动
- [ ] file-change-plan 是否有越界路径
- [ ] 默认禁改集中的文件是否已显式 user-approved
  - 见 <see: <workspace>/.cursor/skills/shared/frontend-forbidden-paths.md>

### 风险
- [ ] P0/P1 风险是否被识别
- [ ] 缓解方案是否可接受
- [ ] 是否引入 mock / 灰度 / feature flag

### 技术决策
- [ ] SWR 策略（key 设计 / mutate 范围）
- [ ] optimistic update 方案
- [ ] polling 触发 / 停止条件
- [ ] retry 策略
- [ ] 请求 ID 类型（Long → string）

### 是否允许进入 Developer
- [ ] approved（无修改）
- [ ] needs_changes（列具体改动点）
- [ ] rejected（列拒绝理由 + 退回到哪个阶段）

## 你的 verdict
请明确给出三选一：approved / rejected / needs_changes
并说明理由 / 修改建议（如有）。
```

## 模板 B：Architect Review Record（Cursor 代写）

用户给出 verdict 后，Cursor 按指令写 `human-reviews/architect-review.md`：

```md
---
schema_version: a2a/v1
review_type: architect
task_id: <T-YYYY-NNN>
reviewer: <用户 handle>
reviewed_at: <ISO 时间>
verdict: approved | rejected | needs_changes
---

# Architect Review

## 审阅对象
- artifacts/architect/tech-plan.md（version: ...）
- artifacts/architect/file-change-plan.md（version: ...）
- artifacts/architect/risk-plan.md（version: ...）

## 决策摘要
<用户原话或 Cursor 转述>

## 范围确认
- file-change-plan 白名单：[approved / 修改如下]
- 默认禁改集例外：[无 / 列文件 + user-approved 依据]

## 风险确认
- P0：[approved / 修改]
- P1：[approved / 修改]

## 技术决策确认
- SWR / mutate：...
- optimistic update：...
- polling：...
- retry：...

## verdict
**approved | rejected | needs_changes**

## 修改建议（needs_changes 时必填）
1. ...
2. ...

## 退回 / 推进
- approved → Controller 双步翻状态（human_review_status=approved → current_status=developer_processing）
- needs_changes → 退回 architect_processing，列出待改清单
- rejected → 退回 pm_processing 或 archived
```

## 模板 C：Final Review Prompt（user 视角）

发给用户的 Prompt：

```md
# Final Review：<T-YYYY-NNN>

## 待审材料
- artifacts/developer/{implementation-log,changed-files}.md
- artifacts/qa/{test-report,acceptance-checklist}.md
- messages/from-qa-<seq>-handoff.md

## 必须确认
- [ ] 改动文件 100% 在 file-change-plan 白名单内（看 changed-files）
- [ ] 禁改集 0 触碰（grep / diff 验证）
- [ ] test-report 中无 P0/P1 未处理 fail
- [ ] 所有 ✅ 待审项均已 approved 或显式 deferred
- [ ] Architect 风险清单全部回归
- [ ] lint / typecheck / prettier 通过

## 你的 verdict
请明确：approved / rejected / needs_changes
```

## 模板 D：Final Review Record（Cursor 代写）

```md
---
schema_version: a2a/v1
review_type: final
task_id: <T-YYYY-NNN>
reviewer: <用户 handle>
reviewed_at: <ISO 时间>
verdict: approved | rejected | needs_changes
---

# Final Review

## 验证记录
- file-change-plan vs changed-files diff：[一致 / 列差异]
- 禁改集 0 触碰：[确认 / 列违规]
- test-report 结论：[pass / fail]
- 风险回归：[全部 / 列未回归]
- lint / typecheck / prettier：[pass / fail]

## verdict
**approved | rejected | needs_changes**

## 后续
- approved → Controller 双步翻状态（final_review_status=approved → current_status=completed）→ 写 artifacts/final/final-delivery.md
- needs_changes → 退回 qa_processing 或 developer_processing
- rejected → 列具体阻塞，退回到对应阶段
```

## 双步翻状态注意

按 `.cursor/rules/ai-agents.mdc` §8：

1. 第一步：state.human_review_status / final_review_status = approved
2. 第二步（独立）：state.current_status = developer_processing / completed
3. **禁止合并双步**
4. 中间被中断（如 session 切换）→ Controller 启动自检按 §4.5 自动补做第 2 步

## 反模式

- Cursor 自行决定 verdict
- 代写 review record 时 reviewer 字段填非用户 handle
- 把 verdict 默认成 approved
- 用 needs_changes 但没列具体改动点
- 双步翻状态合并写
