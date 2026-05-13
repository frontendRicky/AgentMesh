# A2A QA Stage Prompt

> 由 `prompt-a2a-workflow/SKILL.md` 在 `state.current_status == qa_processing` 时调用。
> 完整可复制 Prompt 模板，~ 55 行。

## 前置条件

- `state.current_status == qa_processing`
- `state.current_agent == qa`
- Developer artifacts 完整：implementation-log + changed-files + handoff message

## QA 与 frontend-qa 的差异

| 维度 | 本 Skill（A2A QA） | `prompt-frontend-qa` |
|---|---|---|
| 走 A2A schema | ✅（artifacts/qa/test-report.md 等） | ❌ |
| 改源码权限 | ❌（默认只读） | ❌ |
| 触发 QA fail → Controller | ✅ | ❌（直接通知开发） |
| 适用 | A2A 流程内 | 日常 PR / hotfix |

## 可复制 Prompt

```md
# A2A QA Stage：<T-YYYY-NNN> · <一句话需求>

## 角色与边界
- 角色：qa
- 可写：artifacts/qa/**、messages/from-qa-*.md、经 qa-file-change-plan 授权的测试文件
- 默认：主业务源码只读
- 不允许：改业务源码 / 改 Developer artifacts / 直接修 bug / 改 state.md
- 引用：<see: .cursor/rules/ai-agents.mdc> §11

## 输入（必读）
- artifacts/developer/implementation-log.md
- artifacts/developer/changed-files.md           ← 验收变更白名单
- messages/from-developer-<seq>-handoff.md
- artifacts/architect/file-change-plan.md        ← 白名单铁律
- artifacts/architect/risk-plan.md               ← 风险回归点
- artifacts/pm/state-and-action-matrix.md        ← 状态矩阵

## 验收维度（按顺序，每条出证据）

### 1. 范围合规
- [ ] changed-files 中所有 path 在 file-change-plan 白名单内
- [ ] 禁改集 0 触碰（grep / diff 验证）
  - 见 <see: <workspace>/.cursor/skills/shared/frontend-forbidden-paths.md>

### 2. 接口链路
- [ ] Network 请求路径 / method / payload 与 api-contract-checklist 一致
- [ ] response unwrap 正确
- [ ] Long ID 全 string（DevTools 检查 ViewModel）

### 3. 状态流转
- [ ] state-and-action-matrix 中每个状态可达
- [ ] 每个状态下：允许 / 禁用 / 隐藏的操作符合预期
- [ ] 禁用按钮带 tooltip
- [ ] canXxx 派生字段值与业务规则一致
  - 见 <see: <workspace>/.cursor/skills/shared/frontend-state-button-matrix.md>

### 4. 操作矩阵 + 表单
- [ ] 每个操作点击 → 触发预期接口 + 成功后 mutate 范围正确
- [ ] 失败提示文案明确
- [ ] 表单校验：必填 / 格式 / 长度 / 业务规则
- [ ] optimistic update 失败回滚正确

### 5. 空态 / loading / error
- [ ] 首次 loading 表现
- [ ] 空数据 EmptyState 文案
- [ ] 接口 error 时 UI（重试入口 / 错误提示）
- [ ] 边界数据（极长字符 / 极大数字 / 空字段）

### 6. Console / Network
- [ ] Console 无新 error / warning
- [ ] Network 无 404 / CORS / mixed content
- [ ] 没有重复请求 / 请求风暴
- [ ] polling 在 hidden tab / 退出页面后停止

### 7. 风险回归
- [ ] artifacts/architect/risk-plan.md 中所有 P0/P1 风险回归
- [ ] Human Review 确认的 ✅ 待审项全部覆盖
- [ ] 涉及上传：按 <see: <workspace>/.cursor/skills/shared/frontend-upload-workflow.md> 跑全链路

### 8. 工程
- [ ] lint 不新增 error
- [ ] typecheck 不新增 error
- [ ] prettier 已格式化
- [ ] 不引入新依赖（package.json 未变）

## 强约束
- 默认主业务源码只读；如必须改测试文件，需 qa-file-change-plan 授权
- 发现 bug → **不直接修**，写 fail 进 test-report
- 发现 P0 → 立即标记 fail，handoff 中标 critical
- 不修改 Developer 的 implementation-log / changed-files

## 退出条件
- 全部维度 ✓ → 写 from-qa-<seq>-handoff.md，verdict=pass
- 任一维度 ✗ → test-report 标 fail，按严重程度处置：
  - P0/P1 → from-qa-<seq>-fail-handoff.md → Controller 退回 developer_processing
  - P2/P3 → handoff 中标 needs_changes，由 Final Review 决定是否阻塞

## 输出
- artifacts/qa/test-report.md
  - 每个维度的 ✓/✗ + 证据
  - 发现的 issue 清单（严重程度 P0-P3 / 复现步骤 / 期望 / 实际）
- artifacts/qa/acceptance-checklist.md
  - 8 大维度的最终勾选状态
- messages/from-qa-<seq>-handoff.md
  - verdict: pass | fail | needs_changes
  - 给 Final Review 的关键摘要
```

## 严重程度分级

| 级别 | 处置 |
|---|---|
| **P0** 阻塞上线 / 数据错乱 / 鉴权失败 / 支付错 | 立即退回 developer |
| **P1** 核心流程不可用 / 状态错 / 数据丢失风险 | 退回 developer |
| **P2** 体验问题 / 文案 / 视觉偏差 | needs_changes，Final Review 决定 |
| **P3** warning / deprecated / 内部信息 | 标记，可下次迭代 |

## 反模式

- QA 自己改源码修 bug
- 改测试 fixture / mock 让用例通过
- 跳过维度但不写理由
- 发现 P0 但 verdict 给 pass
- 改 implementation-log / changed-files / risk-plan
- 改 state.md（QA 不能写）
