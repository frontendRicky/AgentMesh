---
artifact_id: A-T-YYYY-NNN-file-change-plan
task_id: T-YYYY-NNN
artifact_type: file_change_plan
produced_by: architect
consumed_by:
  - developer
  - qa
file_path: artifacts/architect/file-change-plan.md
version: 1
status: draft
summary: <N 个文件改动白名单,新增 X / 修改 Y / 删除 Z>
dependencies:
  - A-T-YYYY-NNN-tech-plan
validation_result: pending
created_at: 2026-MM-DDTHH:MM:SS+08:00
schema_version: a2a/v1
---

# File Change Plan: <task_title>

> **Developer 写代码门禁的唯一依据**。每个文件条目必须含 7 字段。
>
> **重要**：
> - 新增文件**也必须**预先列入（operation: create）
> - **默认 forbidden 集**（package.json / lock / .github/** / .gitlab-ci.yml / Dockerfile / CI 配置）默认 operation: forbidden,除非用户明确批准并由 Architect 写入 allowed: yes 且 owner: user-approved
> - Developer 严禁修改 file-change-plan 之外的源码

## 1. 白名单（每条目必含 7 字段）

```yaml
- path: src/pages/settings/index.tsx
  operation: create               # create | modify | delete | readonly | forbidden
  allowed: yes                    # yes | no
  reason: 新增 Settings 页面入口
  risk: 低,新增独立文件
  owner: developer                # developer | qa | developer+qa-approved | user-approved
  notes: 与 useSettings hook 配合

- path: src/components/AppLayout.tsx
  operation: modify
  allowed: yes
  reason: 在主导航增加 Settings 菜单项(权限受控)
  risk: 中,影响所有页面入口
  owner: developer
  notes: 必须保持现有菜单顺序与权限拦截

- path: src/services/legacy.ts
  operation: readonly
  allowed: no
  reason: 不应被本 Task 触碰,避免污染旧逻辑
  risk: 高,旧业务依赖
  owner: developer
  notes: 即使 import 也不要修改其导出

- path: package.json
  operation: forbidden            # 默认 forbidden
  allowed: no
  reason: 本 Task 不引入新依赖
  risk: 高,改后影响整个工程
  owner: user-approved            # 如需改,必须 user-approved
  notes: 默认禁改集
```

## 2. 默认禁改集（**必须**显式列出）

以下文件**默认 forbidden**，除非用户在 Architect Review 时明确批准且 owner: user-approved：

| path | 默认 operation | 默认 allowed |
|---|---|---|
| package.json | forbidden | no |
| package-lock.json | forbidden | no |
| pnpm-lock.yaml | forbidden | no |
| yarn.lock | forbidden | no |
| .github/** | forbidden | no |
| .gitlab-ci.yml | forbidden | no |
| Dockerfile | forbidden | no |
| .docker/** | forbidden | no |
| .gitlab/** | forbidden | no |
| .husky/** | forbidden | no |
| .eslintrc* | forbidden | no |
| tsconfig.json | forbidden | no |

## 3. 汇总

- 新增文件数：N
- 修改文件数：N
- 删除文件数：N
- 显式 readonly 文件数：N
- 触碰默认禁改集（user-approved）：N

## 4. 边界声明

- 本计划之外的任何文件 = forbidden
- Developer 严禁触碰本计划之外的文件
- 实施过程中发现需新增白名单外的文件 → 发 `from-developer-<seq>-blocker-request.md`（`message_type: blocker`）让 Architect 补
- 5 条门禁未达（Developer 在错误状态下被误启动） → 发 `from-developer-<seq>-gate-failure-request.md`（`message_type: gate_failure`），**不**触发正式 Blocker、**不**改 state
- 任何越界改动都视为系统级违规，必须回滚
