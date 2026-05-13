---
contract_id: HC-<from>-to-<to>
from_agent: pm | architect | developer | qa | controller | human
to_agent: pm | architect | developer | qa | controller | human
schema_version: a2a/v1
---

> **Handoff Contract 模板**。主键：`contract_id`。**禁止**给本文件添加 artifact_id。

## required_input_artifacts

- artifact_type: <type>, status: ready

## required_output_artifacts

- artifact_type: <type>, status: ready

## required_input_messages

- file: messages/<from-controller-or-other>-<seq>-<intent>.md
  message_type: handoff
  intent: <intent>

## required_output_messages

- file: messages/from-<role>-<seq>-handoff.md
  message_type: handoff
  intent: <intent>
  to_agent: <next>
  payload 必含:
    - <字段 1>
    - <字段 2>

## required_input_review_records

- (无 / 或: file: human-reviews/<review-type>.md, verdict: approved)

## required_output_review_records

- (通常为空 — review record 由 Human Review Actor 产出)

## acceptance_criteria

- [ ] <可校验条件 1>
- [ ] <可校验条件 2>
- [ ] <可校验条件 3>

## validation_questions

- <问 1>
- <问 2>

## allowed_next_actions

- <下一步允许>

## forbidden_next_actions

- <下一步禁止>

## blocker_conditions

- <触发 Blocker 条件 1>
- <触发 Blocker 条件 2>

## flow_variants

### task_type == <variant>

- <变体差异>

(若全 flow 通用,写 "全 flow 通用,无变体")
