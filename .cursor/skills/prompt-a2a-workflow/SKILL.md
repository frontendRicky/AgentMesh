---
name: prompt-a2a-workflow
description: 用户已经确认是 A2A / AgentMesh 多 Agent 流程（PM / Architect / Human Review / Developer / QA）时使用本 Skill，仅做阶段路由，按当前 state.current_status 加载对应阶段模板文件。不直接生成完整 Prompt（模板在子文件里）。只生成 Prompt，不直接执行开发、不写源码、不改 state.md。
---

# Prompt A2A Workflow（路由层）

## 我是什么

- 输入：A2A 任务（task_id + 当前阶段）
- 输出：按当前阶段路由到对应模板文件，要求 Agent Read 模板后填空
- **不做**：直接生成 80 行长 Prompt、写 state.md、改源码、跳过 Human Review

## 前置门禁（路由前必走）

1. 读 `.ai-agents/workspace/active-task.md` 拿 `active_task_id`
2. 读 `.ai-agents/workspace/<task-id>/state.md` 拿 `current_status` / `current_agent` / `human_review_status`
3. 校验 task_id 匹配 `^T-\d{4}-\d{3}$`
4. 缺任一 → 反问用户 / 让 Controller 重建，**不出 Prompt**

## 阶段路由表

按 `state.current_status` 路由到模板文件：

| current_status | 模板文件（Read 后填空） | 备注 |
|---|---|---|
| `pm_processing` | `./prompt-a2a-pm.md` | PM 拆需求 |
| `architect_processing` | `./prompt-a2a-architect.md` | Architect 出 tech-plan + file-change-plan + risk-plan |
| `human_review_required` | `./prompt-a2a-human-review.md` | 让用户审 Architect 产出 |
| `developer_processing` | `./prompt-a2a-developer.md` | 必须 human_review_status == approved |
| `qa_processing` | `./prompt-a2a-qa.md` | 走 A2A QA schema（区别于 prompt-frontend-qa） |
| `final_review_required` | `./prompt-a2a-human-review.md`（final 段） | final-review |
| `blocked` | **不出 Prompt** | 让 Controller 处理 |
| `completed` | **不出 Prompt** | 任务已完成 |

完整路径（绝对）：`<workspace>/.cursor/skills/prompt-a2a-workflow/prompt-a2a-<stage>.md`。

## 推荐启动命令

新任务：
```bash
ls .ai-agents/scripts/                                  # 先确认脚本名
cat .ai-agents/scripts/README.md                        # 看具体参数
# 然后按 README 启动，例如：
# ./start-task --type feature --priority P2 --owner <handle> "需求：..."
```

继续任务：
```bash
ls .ai-agents/scripts/
# ./resume-task <T-YYYY-NNN>
```

**不要凭记忆输出命令**，先 `ls` 验证脚本名和参数。

## 角色与写权限（Prompt 必须强约束）

按 `.cursor/rules/ai-agents.mdc` §11：

| 角色 | 可写 |
|---|---|
| pm | `artifacts/pm/**`、`messages/from-pm-*.md` |
| architect | `artifacts/architect/**`、`messages/from-architect-*.md`，**严禁源码 Write** |
| developer | `artifacts/developer/**`、`messages/from-developer-*.md`（含 blocker-request、gate-failure-request）、命中 file-change-plan 白名单的源码（双门禁后） |
| qa | `artifacts/qa/**`、`messages/from-qa-*.md`、经 qa-file-change-plan 授权的测试文件 |
| controller | `task.md`（仅创建时）、`state.md`、`blockers/**`、`messages/from-controller-*.md`、`workspace/active-task.md`、`artifacts/final/**` |
| human | `human-reviews/architect-review.md`、`human-reviews/final-review.md` |

**角色名严格 6 选 1**：`pm / architect / developer / qa / controller / human`。**禁止** 用 `dev`。

## 全 A2A Prompt 通用约束（写进每个阶段模板顶部）

- 严格按当前阶段 agent-card 的 `writable_paths`
- 不修改 state.md（只有 Controller 可写）
- 真实流程阻塞 → 写 `messages/from-<role>-<seq>-blocker-request.md`
- Agent 误启动门禁失败 → 写 `messages/from-<role>-<seq>-gate-failure-request.md`（不创建 Blocker）
- Developer 写源码前过 5 条门禁：见 `.cursor/rules/ai-agents.mdc` §5
- Architect / PM **严禁源码 Write**

## 何时不用本 Skill

- 非 A2A 任务（A2A 评分 < 6） → 走对应日常 skill（api-integration / bugfix / ...）
- 任务在 `blocked` / `completed` 状态 → 让 Controller 处理，不出 Prompt
- 用户只想"问 A2A 是什么" → 直接答，不路由
- 任务的 state.md 缺失 → 拒绝路由，要求 Controller 重建

## 引用

- Shared snippets：`<workspace>/.cursor/skills/shared/*.md`
- A2A 硬规则：`/Users/zhangxia/work/projects/AgentMesh/.cursor/rules/ai-agents.mdc`
- A2A schema：`.ai-agents/a2a/{state.schema,blocker.schema,message.schema,review.schema}.md`
