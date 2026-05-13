# Review Record Schema

> 人工审核留痕。**仅 Human Review Actor 创建**：用户在对话中给出明确 verdict 后，由 Cursor 按用户指令代写 review record。**Controller 与所有专业 Agent 都不允许写。**

## 1. 双角色双步流转

### 角色 1：Human Review Actor（用户 + Cursor 代写）

- 用户在对话中给出明确 verdict（approved / rejected / needs_changes）
- Cursor 按用户指令代写 `human-reviews/architect-review.md` 或 `human-reviews/final-review.md`
- 写入完成后，Cursor 在回复中明示"Human Review Actor 已写入 review record"

### 角色 2：Flow Controller（只读校验 + 翻状态）

- Controller 读取 review record，校验字段完整性
- 校验通过 + verdict == approved → **第一步**：翻 `state.human_review_status = approved`
- **第二步**（独立）：推 `state.current_status = developer_processing`（或 `completed`）
- 校验失败 → 进入 Blocker 创建流程

> **Controller 严禁创建、修改、伪造任何 review record。**

## 2. 字段定义

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `review_id` | string | 是 | 全局唯一，格式 `R-<task_id>-<review_type>` |
| `task_id` | string | 是 | 所属 Task |
| `review_type` | enum | 是 | `architect_review` / `final_review` |
| `reviewed_artifacts` | string[] | 是 | 审核覆盖的 artifact_id 列表 |
| `reviewer` | string | 是 | 用户 handle |
| `reviewed_at` | ISO8601 | 是 | 审核时间 |
| `verdict` | enum | 是 | `approved` / `rejected` / `needs_changes` |
| `issues` | array | 否 | 审核发现的问题（见下方子结构） |
| `followup_required` | bool | 是 | 是否需要后续跟进 |
| `notes` | string | 否 | 备注 |
| `schema_version` | string | 是 | 固定 `a2a/v1` |

### issues 子结构

```yaml
issues:
  - severity: blocker | major | minor
    description: <问题描述>
    affected_artifact: <artifact-id>
```

## 3. 文件路径约定

固定两个文件名：

- `human-reviews/architect-review.md`（架构审核，对应 architect_completed → human_review_required → developer_processing 流转）
- `human-reviews/final-review.md`（最终验收，对应 qa_completed → final_review_required → completed 流转）

## 4. 示例 Frontmatter

### 4.1 Architect Review 通过

```yaml
---
review_id: R-T-2026-001-architect
task_id: T-2026-001
review_type: architect_review
reviewed_artifacts:
  - A-T-2026-001-tech-plan
  - A-T-2026-001-file-change-plan
  - A-T-2026-001-risk-plan
reviewer: zhangxia
reviewed_at: 2026-05-09T14:00:00+08:00
verdict: approved
issues: []
followup_required: false
notes: 方案合理,file-change-plan 9 个文件清晰,风险点已覆盖
schema_version: a2a/v1
---
```

### 4.2 Architect Review 退回

```yaml
---
review_id: R-T-2026-001-architect
task_id: T-2026-001
review_type: architect_review
reviewed_artifacts:
  - A-T-2026-001-tech-plan
  - A-T-2026-001-file-change-plan
  - A-T-2026-001-risk-plan
reviewer: zhangxia
reviewed_at: 2026-05-09T14:00:00+08:00
verdict: needs_changes
issues:
  - severity: major
    description: 主题切换的状态管理建议放全局,而不是页面级
    affected_artifact: A-T-2026-001-tech-plan
  - severity: minor
    description: file-change-plan 缺 src/types/settings.ts 条目
    affected_artifact: A-T-2026-001-file-change-plan
followup_required: true
notes: 调整后再走一次 review
schema_version: a2a/v1
---
```

### 4.3 Final Review 通过

```yaml
---
review_id: R-T-2026-001-final
task_id: T-2026-001
review_type: final_review
reviewed_artifacts:
  - A-T-2026-001-test-report
  - A-T-2026-001-acceptance-checklist
reviewer: zhangxia
reviewed_at: 2026-05-09T17:00:00+08:00
verdict: approved
issues: []
followup_required: false
notes: 测试报告 7 维全过,验收清单 12 项全勾
schema_version: a2a/v1
---
```

## 5. 文件正文要求

frontmatter 之后建议包含：

```markdown
## 我审阅了什么
- artifacts/architect/tech-plan.md
- artifacts/architect/file-change-plan.md
- artifacts/architect/risk-plan.md

## 我的判断
verdict: approved

## 我对下游 Agent 的额外要求
- (无 / 或具体要求)

## 备注
方案合理,file-change-plan 9 个文件清晰,风险点已覆盖
```

## 6. 校验规则

- `review_id` 必须符合 `^R-T-\d{4}-\d{3}-(architect|final)$`
- `verdict` 必须是 3 个枚举值之一
- `verdict == rejected` 或 `needs_changes` 时 `issues` 必须非空
- `verdict == approved` 时 `issues` 可以为空，但 `notes` 建议填写
- `reviewed_artifacts` 必须真实存在（artifact_id 都能找到）
- `reviewer` 不能是 `controller`、`pm`、`architect`、`dev`、`qa`（必须是真实用户 handle）

## 7. 常见违规示例

### 反例 1：Controller 写 review record

任何由 Controller 写入 `human-reviews/*.md` 的行为都视为伪造审核，必须立即回滚。

### 反例 2：跳过 review record 直接翻 state

```
用户对话: "我同意,直接进开发"
Controller 直接 state.human_review_status = approved   # 错误!必须先有 review record 文件,再校验
```

### 反例 3：reviewer 字段填角色名

```yaml
reviewer: pm   # 错误!应是真实用户 handle
```

### 反例 4：rejected 但 issues 空

```yaml
verdict: rejected
issues: []     # 错误!rejected 必须说明原因
```

## 8. 下游使用方式

- Controller 校验通过 → 第一步翻 `state.human_review_status` / `final_review_status` → 第二步独立推 `state.current_status`
- `final-delivery.md` 必须引用 `R-T-*-architect` 与 `R-T-*-final` 作为审核留痕
- Review Record 自身也算 Artifact（artifact_type = human_review_record / final_review_record），可被 final-delivery 的 dependencies 字段引用
