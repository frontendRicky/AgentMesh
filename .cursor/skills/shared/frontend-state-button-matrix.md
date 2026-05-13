# Frontend State & Button Matrix（状态按钮矩阵）

> 单一事实源。涉及"按钮显隐 / 禁用 / 状态流转"的 Prompt 引用本文件。

## canXxx 派生字段：生成位置

| 类型 | 在哪里生成 | 为什么 |
|---|---|---|
| **业务级** `canInvite` / `canApprove` / `canRefund` | mapper（raw → ViewModel） | 业务规则稳定、可单测、不依赖 UI |
| **会话级** `canSubmitting` / `canRetry` | 聚合 hook | 依赖 UI state（submitting、modal 是否打开） |
| **本地交互级** `canExpand` | 组件本地 | 与业务无关，纯交互 |

铁律：
- **组件不重复判断业务状态**（不在 JSX 里写 `if (status === 1 && !isOwner && ...)`）
- 业务派生字段集中在 mapper / 聚合 hook，**单一来源**
- mapper 失败 / 上游字段缺失时 `canXxx = false`（保守）

## 状态矩阵模板（生成 Prompt 时要求 Agent 填）

```text
| 状态 | 允许操作 | 禁用操作 | 隐藏操作 | 触发接口 | 成功后 mutate | 失败提示 |
|---|---|---|---|---|---|---|
| draft | submit, save, delete | publish | — | POST /xxx | invalidate(list) | toast(失败原因) |
| pending | recall | submit | publish, delete | POST /xxx/recall | invalidate(detail) | toast |
| approved | publish | submit, recall | delete | POST /xxx/publish | invalidate(list+detail) | toast |
| rejected | resubmit | publish | — | POST /xxx/resubmit | invalidate(detail) | toast |
| published | — | submit, recall, publish | delete | — | — | — |
```

**Prompt 要求**：
- 一行一种状态
- "允许 / 禁用 / 隐藏" 三态严格区分（不允许混）
- 接口幂等性必须标注
- 成功后 mutate 范围必须明确（不能只写"刷新"）

## 按钮三态规则

| 态 | 行为 | 用户感知 |
|---|---|---|
| **允许** | 可点击，触发对应接口 | 正常 |
| **禁用** `disabled` | 渲染但置灰 + tooltip 解释原因 | 知道这个能力存在，当前不可用 |
| **隐藏** 不渲染 | 完全不出现 | 不知道这个能力存在 |

判断顺序：

1. **权限维度**：当前用户无权 → **隐藏**
2. **状态维度**：状态不允许 → **禁用** + tooltip
3. **进行中维度**：submitting / loading → **禁用** + spinner

## 反模式

- ❌ 组件里写 `status === 'draft' && role === 'owner'`
- ❌ 同一个按钮在多处分别判断 disabled
- ❌ 禁用了按钮但没 tooltip
- ❌ 隐藏了按钮但状态变化后不重新评估
- ❌ canXxx 和 disabled 混用（一份字段 = 一个职责）

## Prompt 引用片段

```text
状态 + 按钮矩阵：<see: shared/frontend-state-button-matrix.md>
关键约束：
- 业务级 canXxx 在 mapper 生成
- 会话级 canXxx 在聚合 hook 生成
- 组件只消费 canXxx + onXxx，不重复业务判断
- 按钮三态（允许/禁用/隐藏）严格区分
- 禁用必须带 tooltip 解释原因
- 必须输出状态矩阵表，一行一种状态
```
