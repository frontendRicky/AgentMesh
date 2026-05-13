# Artifact Schema

> Agent 产出的内容型文件。文件路径 `artifacts/<role>/<artifact-type>.md`。

## 1. 字段定义

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `artifact_id` | string | 是 | 全局唯一，格式 `A-<task_id>-<artifact-type>` |
| `task_id` | string | 是 | 所属 Task |
| `artifact_type` | enum | 是 | 见下方 16 类枚举 |
| `produced_by` | enum | 是 | `pm` / `architect` / `dev` / `qa` / `controller` / `human` |
| `consumed_by` | string[] | 是 | 下游消费角色列表 |
| `file_path` | string | 是 | 相对 workspace 的路径 |
| `version` | int | 是 | 版本号，从 1 起 |
| `status` | enum | 是 | `draft` / `ready` / `rejected` / `superseded` |
| `summary` | string | 是 | 1-2 句话 |
| `dependencies` | string[] | 否 | 依赖的上游 artifact_id 列表 |
| `validation_result` | enum | 是 | `pass` / `fail` / `pending` |
| `validation_notes` | string | 否 | 校验备注 |
| `created_at` | ISO8601 | 是 | 创建时间 |
| `schema_version` | string | 是 | 固定 `a2a/v1` |

## 2. artifact_type 枚举（16 类）

| artifact_type | produced_by | 典型 file_path |
|---|---|---|
| `requirement` | pm | `artifacts/pm/requirement.md` |
| `prd` | pm | `artifacts/pm/prd.md` |
| `bug_brief` | pm | `artifacts/pm/bug-brief.md`（仅 bugfix-flow） |
| `regression_scope` | pm | `artifacts/pm/regression-scope.md`（仅 bugfix-flow） |
| `task_breakdown` | pm | `artifacts/pm/task-breakdown.md` |
| `tech_plan` | architect | `artifacts/architect/tech-plan.md` |
| `file_change_plan` | architect | `artifacts/architect/file-change-plan.md` |
| `qa_file_change_plan` | qa | `artifacts/qa/qa-file-change-plan.md`（仅 QA 需新增测试文件时） |
| `risk_plan` | architect | `artifacts/architect/risk-plan.md` |
| `implementation_log` | dev | `artifacts/developer/implementation-log.md` |
| `changed_files` | dev | `artifacts/developer/changed-files.md` |
| `test_report` | qa | `artifacts/qa/test-report.md` |
| `acceptance_checklist` | qa | `artifacts/qa/acceptance-checklist.md` |
| `human_review_record` | human | `human-reviews/architect-review.md`（写入 `human-reviews/`，不在 `artifacts/<role>/`） |
| `final_review_record` | human | `human-reviews/final-review.md` |
| `final_delivery` | controller | `artifacts/final/final-delivery.md`（仅 final_review_status==approved 后） |

> 注意：`human_review_record` 与 `final_review_record` 虽然 artifact_type 算 Artifact，但**物理路径在 `human-reviews/`**，且**仅 Human Review Actor 可写**。Controller 可以把它们引用到 `final-delivery.md`，但不能修改。

## 3. 示例 Frontmatter

### 3.1 PRD

```yaml
---
artifact_id: A-T-2026-001-prd
task_id: T-2026-001
artifact_type: prd
produced_by: pm
consumed_by: [architect, dev, qa]
file_path: artifacts/pm/prd.md
version: 1
status: ready
summary: Settings 页面 PRD,含主题切换 / localStorage 持久化 / 权限要求
dependencies:
  - A-T-2026-001-requirement
validation_result: pass
validation_notes: PRD 6 项审核全过(用户角色/流程/权限/异常/边界/验收)
created_at: 2026-05-09T11:00:00+08:00
schema_version: a2a/v1
---
```

### 3.2 file-change-plan

```yaml
---
artifact_id: A-T-2026-001-file-change-plan
task_id: T-2026-001
artifact_type: file_change_plan
produced_by: architect
consumed_by: [dev, qa]
file_path: artifacts/architect/file-change-plan.md
version: 1
status: ready
summary: 9 个文件改动白名单,新增 4 个,修改 5 个,无删除
dependencies:
  - A-T-2026-001-tech-plan
validation_result: pass
created_at: 2026-05-09T13:00:00+08:00
schema_version: a2a/v1
---
```

### 3.3 final-delivery

```yaml
---
artifact_id: A-T-2026-001-final-delivery
task_id: T-2026-001
artifact_type: final_delivery
produced_by: controller
consumed_by: [user]
file_path: artifacts/final/final-delivery.md
version: 1
status: ready
summary: Settings 页面交付,含全部 13 件上游 artifact + 2 份 human-review record
dependencies:
  - A-T-2026-001-requirement
  - A-T-2026-001-prd
  - A-T-2026-001-task-breakdown
  - A-T-2026-001-tech-plan
  - A-T-2026-001-file-change-plan
  - A-T-2026-001-risk-plan
  - A-T-2026-001-implementation-log
  - A-T-2026-001-changed-files
  - A-T-2026-001-test-report
  - A-T-2026-001-acceptance-checklist
  - R-T-2026-001-architect
  - R-T-2026-001-final
validation_result: pass
created_at: 2026-05-09T18:00:00+08:00
schema_version: a2a/v1
---
```

## 4. 校验规则

- `artifact_id` 必须符合 `^A-T-\d{4}-\d{3}-[a-z_]+$`
- `produced_by` 必须有写权限（见 file-message-bus.md 路径权限速查）
- `dependencies` 中的 artifact_id 必须真实存在且 `status == ready`
- `final_delivery` 必须仅由 Controller 在 `state.final_review_status == approved` 后写
- 同一 task_id + artifact_type 默认只有一个 version；如需 v2，把 v1 移到 `archive/<artifact-type>.v1.md`，新版 version=2，status=ready，旧版 status=superseded

## 5. 常见违规示例

### 反例 1：把 message 当 artifact

```yaml
# 错误!这是 handoff message,不应有 artifact_id
artifact_id: A-T-2026-001-pm-handoff
file_path: messages/from-pm-002-handoff.md
```

### 反例 2：Architect 写 implementation_log

```yaml
artifact_type: implementation_log
produced_by: architect            # 错误!应是 dev
file_path: artifacts/architect/implementation-log.md   # 错误!应在 artifacts/developer/
```

### 反例 3：依赖未 ready 的上游

```yaml
artifact_id: A-T-2026-001-tech-plan
dependencies: [A-T-2026-001-prd]   # 但 prd.status == draft → 错误,Architect 不应启动
```

### 反例 4：final_delivery 在 final_review_status != approved 时被写

视为 Controller 越权，必须立即回滚并发 Blocker。

## 6. 下游使用方式

- 下游 Agent 启动前先 Read 自己的 input_artifacts（在 Card 中声明）
- 校验 status == ready 才使用
- 校验 dependencies 中的所有上游都已 ready
- 不满足 → 发 Blocker Request
