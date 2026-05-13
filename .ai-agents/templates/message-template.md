---
message_id: M-T-YYYY-NNN-SSS
task_id: T-YYYY-NNN
from_agent: pm | architect | developer | qa | controller | human
to_agent: pm | architect | developer | qa | controller | human
message_type: request | response | handoff | review | blocker | gate_failure | status | final
intent: <kebab-case 短描述>
summary: <1-2 句话>
payload:
  <key1>: <value1>
  <key2>: <value2>
referenced_artifacts:
  - A-T-YYYY-NNN-<artifact-type>
required_response: true | false
blockers: []
created_at: 2026-MM-DDTHH:MM:SS+08:00
schema_version: a2a/v1
---

# Message: <intent>

> 文件路径：`messages/from-<role>-<seq>-<intent>.md`
> 主键：`message_id`，**不要**误加 artifact_id。

## 详情

<可选,展开 payload 的人类可读说明>

## 引用上游 Artifact 的关键内容

<如有,贴关键摘要,便于下游不必重新打开 artifact 也能理解上下文>
