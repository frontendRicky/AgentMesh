# Handoff Contract Schema

> Agent → Agent（或 Agent → Human Review Actor → Agent）的交接契约。**严格区分 Artifact / Message / Review Record 三类输入输出**。

## 1. 字段定义

### Frontmatter

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `contract_id` | string | 是 | 全局唯一，如 `HC-pm-to-architect` |
| `from_agent` | enum | 是 | 来源角色 |
| `to_agent` | enum | 是 | 目标角色 |
| `schema_version` | string | 是 | 固定 `a2a/v1` |

### 正文 sections（六类输入输出严格分开）

1. `## required_input_artifacts` — from_agent 启动前必读的上游 Artifact
2. `## required_output_artifacts` — from_agent 必须产出的 Artifact
3. `## required_input_messages` — from_agent 启动前必须收到的 Message（如 controller handoff）
4. `## required_output_messages` — from_agent 必须发出的 Message（如 handoff message）
5. `## required_input_review_records` — 启动前必须存在的 Review Record（如 human-review-to-developer 必填 architect-review.md）
6. `## required_output_review_records` — 通常为空（Review Record 由 Human Review Actor 写，不属于 Agent Handoff 产物）
7. `## acceptance_criteria` — checkbox 形式的验收清单
8. `## validation_questions` — Controller 在校验时应自问的问题
9. `## allowed_next_actions` — 通过后允许的下一步
10. `## forbidden_next_actions` — 即使通过也禁止的行为
11. `## blocker_conditions` — 触发 Blocker 的条件
12. `## flow_variants` — 按 task_type 的变体规则（如 bugfix）

## 2. 关键约束

- **不允许把 message_type: handoff 的文件归类到 `required_output_artifacts`**
- handoff message 永远是 Message，不是 Artifact，应放 `required_output_messages`
- Review Record 永远是 Review Record，不是 Artifact，应放 `required_input_review_records` 或留 Actor 自己写

## 3. 示例（pm → architect）

```markdown
---
contract_id: HC-pm-to-architect
from_agent: pm
to_agent: architect
schema_version: a2a/v1
---

## required_input_artifacts
- artifact_type: requirement, status: ready

## required_output_artifacts
- artifact_type: requirement, status: ready
- artifact_type: prd, status: ready
- artifact_type: task_breakdown, status: ready

## required_input_messages
- (空 / 或: from-controller-001-handoff)

## required_output_messages
- file: messages/from-pm-<seq>-handoff.md
  message_type: handoff
  intent: pm_to_architect_handoff
  to_agent: architect

## required_input_review_records
- (空)

## required_output_review_records
- (空)

## acceptance_criteria
- [ ] PRD 包含 用户角色 / 页面交互 / 权限规则 / 异常状态 / 边界场景
- [ ] PRD 标注所有"待确认"问题
- [ ] task-breakdown 中每个子任务可独立估期
- [ ] required_output_messages 中的 handoff message 已生成,且明确列出"Architect 必须回答的问题"

## validation_questions
- PRD 是否覆盖所有"待确认"标记?
- 验收标准是否可被 QA 直接转为测试用例?
- 是否定义了所有页面状态(loading/empty/error/success)?

## allowed_next_actions
- Architect Agent 读取 PRD,启动 architect_processing

## forbidden_next_actions
- 跳过 PRD 直接写 Tech Plan
- 直接写代码
- 把 handoff message 归类为 Artifact

## blocker_conditions
- 必填 Artifact 缺失或字段不完整
- 必填 Message 缺失
- 任一 acceptance_criteria 未满足

## flow_variants

### task_type == bugfix

- required_output_artifacts 替换为:
  - artifact_type: requirement (lightweight,3 段)
  - artifact_type: bug_brief
  - artifact_type: regression_scope
  - 不要求 prd / task_breakdown
- acceptance_criteria 替换为:
  - bug_brief 含 复现步骤 / 根因假设 / 预期修复点 / 优先级 4 段
  - regression_scope 至少列 1 个回归模块
  - handoff message 列出"Architect 必须回答的最小修复方案问题"
- blocker_conditions 替换为: 根因不明、无复现步骤、bug_brief 缺"预期修复点"
```

## 4. 校验规则

- `contract_id` 必须符合 `^HC-[a-z-]+-to-[a-z-]+$`
- 每份 Contract 必须有六类 input/output 章节（即使为空也要保留章节标题，明确"无"）
- `acceptance_criteria` 至少 3 条
- `blocker_conditions` 至少 1 条
- `flow_variants` 章节必须存在；不需要变体时写"全 flow 通用，无变体"

## 5. 常见违规示例

### 反例 1：把 handoff message 放 artifacts

```markdown
## required_output_artifacts
- pm-to-architect-handoff.md (message_type: handoff)   # 错误!应放 required_output_messages
```

### 反例 2：六类章节缺失

```markdown
## required_input_artifacts
...
## required_output_artifacts
...
## acceptance_criteria
...
# 缺 required_*_messages / required_*_review_records   # 错误!即使为空也要保留
```

### 反例 3：Review Record 放进 artifacts

```markdown
## required_input_artifacts
- architect-review.md   # 错误!应放 required_input_review_records
```

### 反例 4：bugfix 变体里把 PM 跳过

```markdown
## flow_variants
### task_type == bugfix
- 跳过 PM Agent,直接 Architect    # 错误!bugfix 不裁 PM,只是 PM 出轻量产物
```

## 6. 下游使用方式

- Controller 在推进状态前 Read 对应 Handoff Contract
- 按六类 input 逐一校验
- 任一缺失 → 进入 Blocker 创建流程
- 全部通过 → 推进 state.md → 写 from-controller-*-handoff Message 召唤下游
