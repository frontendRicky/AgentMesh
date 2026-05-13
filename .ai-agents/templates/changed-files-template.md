---
artifact_id: A-T-YYYY-NNN-changed-files
task_id: T-YYYY-NNN
artifact_type: changed_files
produced_by: developer
consumed_by:
  - qa
  - human-review-actor
file_path: artifacts/developer/changed-files.md
version: 1
status: draft
summary: <N 个改动文件,X 越界,Y 依赖文件改动>
dependencies:
  - A-T-YYYY-NNN-file-change-plan
  - A-T-YYYY-NNN-implementation-log
validation_result: pending
created_at: 2026-MM-DDTHH:MM:SS+08:00
schema_version: a2a/v1
---

# Changed Files: <task_title>

> **越界审计表**。每条目必含 8 字段。末尾必须汇总。

## 1. 改动文件清单（每条目 8 字段）

| path | operation_actual | lines_changed | in_file_change_plan | operation_match | out_of_scope | is_dependency_file | remediation |
|---|---|---|---|---|---|---|---|
| src/pages/settings/index.tsx | create | +120 / -0 | yes | yes | no | no | - |
| src/hooks/useSettings.ts | create | +60 / -0 | yes | yes | no | no | - |
| src/components/AppLayout.tsx | modify | +5 / -1 | yes | yes | no | no | - |
| src/services/legacy.ts | modify | +0 / -3 | no | n/a | **yes** | no | rollback 或发 blocker-request 让 Architect 评估补 file-change-plan |
| package.json | modify | +1 / -0 | no | n/a | yes | **yes** | **rollback**,默认 forbidden 集 |

## 2. 字段说明

| 字段 | 含义 |
|---|---|
| `path` | 实际改动路径 |
| `operation_actual` | 实际操作：create / modify / delete |
| `lines_changed` | +N / -N 行数变更 |
| `in_file_change_plan` | 该文件是否在 file-change-plan 中（yes / no） |
| `operation_match` | 实际操作是否与 file-change-plan 中 operation 一致（yes / no / n/a） |
| `out_of_scope` | 是否越界（in_file_change_plan == no 即 yes） |
| `is_dependency_file` | 是否触碰 package.json / lock / .github/** / .gitlab-ci.yml / Dockerfile / CI 配置（yes / no） |
| `remediation` | 若越界 / 不匹配 / 依赖文件，给出处理建议（rollback / 补 file-change-plan / 用户特批） |

## 3. 汇总

- **越界文件数（out_of_scope == yes）**：N
- **依赖文件改动数（is_dependency_file == yes）**：N
- **operation_match == no 数**：N
- **是否阻塞 QA**：yes / no
  - 越界 > 0 → **阻塞**
  - 依赖文件改动 > 0 且无 user-approved → **阻塞**

## 4. 处理建议

> 如有越界 / 依赖文件改动 / operation 不匹配，必须在此节给出处理路径：

- **越界文件**：
  - <path>：建议 rollback / 发 blocker-request 让 Architect 补 file-change-plan
- **依赖文件改动**：
  - <path>：建议 rollback / 提示用户走 user-approved 流程
- **operation 不匹配**：
  - <path>：建议 ...

## 5. 自检结论

- [ ] 越界文件数 == 0
- [ ] 依赖文件改动数 == 0（除非 file-change-plan 显式 user-approved）
- [ ] operation_match 中没有 no
- [ ] 可以交付 QA：yes / no（任一不通过则 no）
