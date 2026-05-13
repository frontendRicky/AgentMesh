---
blocker_id: B-T-YYYY-NNN-SSS
task_id: T-YYYY-NNN
blocked_from_agent: pm | architect | developer | qa
blocked_from_status: <state.current_status before blocked>
resume_to_agent: pm | architect | developer | qa
resume_to_status: <state.current_status target after fix>
blocking_reason: <一句话根因>
missing_artifacts:
  - <artifact-type>
required_fix: <一句话修复指引>
created_by: controller                           # 永远是 controller
source_request_message: M-T-YYYY-NNN-SSS         # 触发它的 blocker request message_id；若 Controller 自校验失败则 null
created_at: 2026-MM-DDTHH:MM:SS+08:00
schema_version: a2a/v1
---

# Blocker: <blocking_reason>

> **仅 Flow Controller 创建**。Agent 严禁直接写本文件，应发 `from-<role>-<seq>-blocker-request.md`。
> 主键：`blocker_id`。**禁止**给本文件添加 artifact_id。

## 1. 已读取的上游 Artifact 与缺漏点

- A-T-YYYY-NNN-prd: ready
- A-T-YYYY-NNN-tech-plan: ready
- A-T-YYYY-NNN-file-change-plan: ready, 但缺 src/services/settings.ts 条目

## 2. 触发场景

- **触发 Agent**: <pm | architect | developer | qa>
- **触发状态**: <state.current_status>
- **触发动作**: <例: developer 试图创建 src/services/settings.ts，但该路径不在 file-change-plan 白名单>

## 3. 给 resume_to_agent 的具体修复指引

1. <步骤 1>
2. <步骤 2>
3. <步骤 3>

例（针对"file-change-plan 缺条目"）：

1. 重新打开 `artifacts/architect/file-change-plan.md`
2. 在白名单表追加一行：
   ```yaml
   - path: src/services/settings.ts
     operation: create
     allowed: yes
     reason: 实现 Settings 持久化需要 service
     risk: 低,新增独立文件
     owner: developer
     notes: 与 useSettings hook 配合
   ```
3. 把 file_change_plan 的 status 设为 ready，version 升到 2，把 v1 移到 `archive/file-change-plan.v1.md`
4. 通知 Controller 校验已补齐

## 4. 估计修复成本（可选）

- <X 分钟 / Y 小时>

## 5. Controller 同步动作

Controller 创建本文件时同步执行：

- [ ] state.previous_status = state.current_status
- [ ] state.current_status = blocked
- [ ] state.blocked_context: 镜像本 Blocker 的 11 字段
- [ ] state.active_blocker = `blocker_id`
- [ ] state.blockers_history: 追加 `blocker_id`
- [ ] 写 `messages/from-controller-<seq>-blocker.md` 通知 `resume_to_agent`

## 6. 恢复条件

`missing_artifacts` 中所有项已补齐（status: ready） → Controller 推进 `state.current_status` 到 `resume_to_status`，清空 `blocked_context` 与 `active_blocker`。
