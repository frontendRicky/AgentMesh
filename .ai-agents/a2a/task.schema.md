# Task Schema

> `task.md` 是 Task 的**静态元信息**，**创建后不再变更**。所有运行时状态都不在这里。

## 1. 字段定义（仅静态元信息）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `task_id` | string | 是 | 全局唯一，格式 `T-YYYY-NNN` |
| `task_type` | enum | 是 | `feature` / `refactor` / `bugfix` / `ui-redesign` / `permission` / `api-integration` |
| `task_title` | string | 是 | 一句话标题 |
| `created_by` | string | 是 | 通常是 `user` |
| `human_owner` | string | 是 | 用户 handle |
| `priority` | enum | 是 | `P0` / `P1` / `P2` |
| `scope.in_scope` | string[] | 是 | 明确包含的范围 |
| `scope.out_of_scope` | string[] | 是 | 明确排除的范围 |
| `constraints` | string[] | 是 | 约束（技术 / 时间 / 兼容性等） |
| `initial_input_messages` | string[] | 否 | 启动时的用户输入 message_id 列表 |
| `required_artifacts` | string[] | 是 | 本 Task 必须产出的 artifact_type 清单 |
| `created_at` | ISO8601 | 是 | 创建时间 |
| `schema_version` | string | 是 | 固定 `a2a/v1` |

## 2. 严禁字段（动态状态，必须放 state.md）

`task.md` **禁止包含**以下任一字段：

```
current_status
previous_status
current_agent
next_agent
human_review_status
final_review_status
produced_artifacts
blockers
checkpoints
final_status
updated_at
```

如发现 `task.md` 含上述字段，视为 schema 违规，Controller 必须发 Blocker。

## 3. 示例 Frontmatter

```yaml
---
task_id: T-2026-001
task_type: feature
task_title: 添加 Settings 页面,支持主题切换
created_by: user
human_owner: zhangxia
priority: P1
scope:
  in_scope:
    - 新增 /settings 路由
    - 主题切换(light / dark)
    - 用户偏好持久化(localStorage)
  out_of_scope:
    - 多语言切换
    - 账户设置
constraints:
  - 兼容现有路由权限
  - 不引入新 UI 库
initial_input_messages:
  - M-T-2026-001-000
required_artifacts:
  - requirement
  - prd
  - task_breakdown
  - tech_plan
  - file_change_plan
  - risk_plan
  - implementation_log
  - changed_files
  - test_report
  - acceptance_checklist
  - human_review_record
  - final_review_record
  - final_delivery
created_at: 2026-05-09T10:00:00+08:00
schema_version: a2a/v1
---
```

## 4. 校验规则

- `task_id` 必须符合 `^T-\d{4}-\d{3}$`
- `task_type` 必须是 6 个枚举值之一
- `scope.in_scope` 与 `scope.out_of_scope` 都必须非空（即使写"暂无"也要明示）
- 创建后 frontmatter 不可修改；如需调整范围 / 优先级，应通过新 Task 或 Blocker 流程

## 5. 常见违规示例

### 反例 1：把动态状态写进 task.md

```yaml
task_id: T-2026-001
task_status: pm_processing    # 错误!应放 state.md
current_agent: pm             # 错误!
```

### 反例 2：scope 留空

```yaml
scope:
  in_scope: []                # 错误!即使范围模糊也要列点东西
```

### 反例 3：required_artifacts 漏 review record

```yaml
required_artifacts:
  - prd
  - tech_plan
  - implementation_log        # 错误!漏了 human_review_record / final_review_record / final_delivery
```

## 6. 下游使用方式

- Controller 创建 Task 时一次性写定 task.md
- 后续所有 Agent 只读不写 task.md
- 如需修改 scope / priority：建议新建 Task 或在 state.blockers_history 中记录变更原因
