# Code Change Rules — 代码改动规则

> 规范 Senior FE Dev Agent 的代码改动行为。**核心**：file-change-plan 是写权限的唯一依据。

## 1. 改前必须说明影响范围

- 在 `implementation-log.md` 中记录："本次改动会影响 X 模块的 Y 行为"
- 在 changed-files.md 末尾汇总："越界文件数 / 依赖文件改动数 / 是否阻塞 QA"

## 2. 只修改技术方案允许的文件（file-change-plan 白名单）

`file-change-plan.md` 是 Architect 产出的白名单文件，每条目 7 字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `path` | string | 相对路径 |
| `operation` | enum | `create` / `modify` / `delete` / `readonly` / `forbidden`（默认 forbidden） |
| `allowed` | enum | `yes` / `no`（默认 no） |
| `reason` | string | 为什么改 |
| `risk` | enum + string | 低 / 中 / 高 + 一句话 |
| `owner` | enum | `developer` / `qa` / `developer+qa-approved` / `user-approved` |
| `notes` | string | 补充 |

**Dev 写代码门禁**：仅可改 `operation` ∈ {create, modify, delete} 且 `allowed == yes` 的文件。

## 3. 新增文件必须说明原因

- 任何新增文件必须**预先**列入 file-change-plan（operation: create）
- 如果实施过程中发现需要新增白名单外的文件 → **不允许**直接新建 → 发 blocker-request 让 Architect 补 file-change-plan

## 4. 不允许擅自改依赖

`package.json` / `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` **默认 operation: forbidden**。

如需改：
- Architect 在 file-change-plan 显式列出 path / operation / allowed: yes / owner: user-approved
- 用户在 Architect Review 阶段明确批准
- 不允许 Dev 擅自加 / 升 / 降依赖

## 5. 不允许擅自改 lock 文件

`package-lock.json` / `pnpm-lock.yaml` / `yarn.lock` 受 R-A2A-4 默认 forbidden 集保护，与 R-A2A-4 同等约束。

## 6. 不允许擅自改 CI/CD

`.github/**` / `.gitlab-ci.yml` / `Dockerfile` / 其他 CI 配置 默认 operation: forbidden。

如需改：与依赖改动同等流程（用户批准 + owner: user-approved + 显式 allowed: yes）。

## 7. 不允许删除旧逻辑

- 删除 = file-change-plan operation: delete
- 默认 operation: modify 不允许把整段旧代码替换成新代码（应保留兼容性）
- "看起来无用"的旧逻辑 → **不删**，应在 implementation-log 标注"建议后续 Task 评估删除"

## 8. 不允许大范围重构无关代码

- "顺手优化"是 refactor / cleanup 范畴，不属于本 Task
- 如确实必要 → 发 blocker-request 让 Architect 评估是否扩容 file-change-plan
- 改完后 changed-files 越界审计应为 0

## 9. 越界审计（changed-files.md）

每条目必含 8 字段：

- `path`
- `operation_actual`：create / modify / delete
- `lines_changed`：+N / -N
- `in_file_change_plan`：yes / no
- `operation_match`：yes / no / n/a
- `out_of_scope`：yes / no
- `is_dependency_file`：yes / no
- `remediation`：若越界 / 不匹配，给出处理建议（rollback / 补 file-change-plan / 用户特批）

文件末尾汇总：
- 越界文件数（`out_of_scope == yes` 计数）
- 依赖文件改动数（`is_dependency_file == yes` 计数）
- 是否阻塞 QA（任何越界都视为阻塞）

## 10. 默认禁改集（Dev 永远不能擅自改）

- `package.json`
- `package-lock.json`
- `pnpm-lock.yaml`
- `yarn.lock`
- `.github/**`
- `.gitlab-ci.yml`
- `Dockerfile`
- `.docker/**`
- `.gitlab/**`
- `.husky/**`
- `.eslintrc*`（除非 file-change-plan 显式允许）
- `tsconfig.json`（除非 file-change-plan 显式允许）
- 其他 CI / CD / build / lint 配置文件

如需改：必须 user-approved + 显式写入 file-change-plan + owner: user-approved。

## 11. 风险标注

每个高风险改动（risk: 高）必须在 implementation-log 中：
- 详细记录改动前后行为对比
- 给出回滚步骤（git revert / patch 撤回）
- 提示 QA 重点测试方向
