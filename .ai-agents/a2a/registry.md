# A2A Agent Registry

> 当前系统注册的所有 Agent 与 Actor。

## 1. 注册表

| agent_id | role | 文件 | 上游 | 下游 |
|---|---|---|---|---|
| pm-001 | pm | [agent-cards/product-manager.card.md](../agent-cards/product-manager.card.md) | User | architect-001 |
| architect-001 | architect | [agent-cards/architect.card.md](../agent-cards/architect.card.md) | pm-001 | human-review-actor |
| developer-001 | developer | [agent-cards/senior-frontend-developer.card.md](../agent-cards/senior-frontend-developer.card.md) | human-review-actor | qa-001 |
| qa-001 | qa | [agent-cards/qa-tester.card.md](../agent-cards/qa-tester.card.md) | developer-001 | human-review-actor (final) |
| controller-001 | controller | [agent-cards/flow-controller.card.md](../agent-cards/flow-controller.card.md) | (orchestrates all) | (orchestrates all) |
| human-review-actor | human | (用户本人通过 Cursor 代写 review record) | - | - |

## 2. 路径权限速查

| 角色 | 唯一可写路径 |
|---|---|
| pm | `artifacts/pm/**`、`messages/from-pm-*.md`（含 blocker-request） |
| architect | `artifacts/architect/**`、`messages/from-architect-*.md`（含 blocker-request） |
| developer | `artifacts/developer/**`、`messages/from-developer-*.md`（含 blocker-request、gate-failure-request）+ 命中 file-change-plan 白名单的源码 |
| qa | `artifacts/qa/**`、`messages/from-qa-*.md`（含 blocker-request）+ 经 qa-file-change-plan 授权的测试文件 |
| controller | `task.md`、`state.md`、`blockers/**`、`messages/from-controller-*.md`、`workspace/active-task.md`、`artifacts/final/**`（仅 final_review_status==approved 后） |
| human-review-actor | `human-reviews/architect-review.md`、`human-reviews/final-review.md` |

## 3. 严禁交叉

任何角色写出表中"唯一可写路径"之外的文件，都视为系统级违规。Cursor 必须在写之前自检，写错位 → 拒绝执行 → 发 Blocker Request。

## 4. Agent 加载

Cursor 根据 `state.current_agent` 加载对应 `agent-cards/<role>.card.md` 与 `agents/<role>.agent.md`。
