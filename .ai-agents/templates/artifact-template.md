---
artifact_id: A-T-YYYY-NNN-<artifact-type>
task_id: T-YYYY-NNN
artifact_type: requirement | prd | bug_brief | regression_scope | task_breakdown | tech_plan | file_change_plan | qa_file_change_plan | risk_plan | implementation_log | changed_files | test_report | acceptance_checklist | human_review_record | final_review_record | final_delivery
produced_by: pm | architect | developer | qa | controller | human
consumed_by:
  - architect
  - developer
  - qa
file_path: artifacts/<role>/<artifact-type>.md
version: 1
status: draft | ready | rejected | superseded
summary: <1-2 句话>
dependencies:
  - A-T-YYYY-NNN-<上游 artifact-type>
validation_result: pass | fail | pending
validation_notes: <可选>
created_at: 2026-MM-DDTHH:MM:SS+08:00
schema_version: a2a/v1
---

# <Artifact 标题>

> **基础 Artifact 模板**。具体类型应使用对应专用模板（如 prd-template、tech-plan-template）。
> 主键：`artifact_id`。

## 内容

<artifact 主体内容>
