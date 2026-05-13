---
name: prompt-frontend-bugfix
description: 用户已经贴出 Network / Console / 截图，或明确说"修一个 bug / 修这个 warning / 联调坏了"时使用本 Skill，生成最小 diff 的 Bugfix Prompt。不用于初步路由（路由由 prompt-engineer-router 负责）。只生成 Prompt，不直接执行开发、不改代码。
---

# Prompt Frontend Bugfix

## 我是什么

- 输入：现象 + 预期 + (Network / Console / 截图 至少一个)
- 输出：可复制 Bugfix Prompt（mini / normal 两档）
- 不做：执行开发、自己猜根因

## 依赖

- `<see: <workspace>/.cursor/skills/shared/frontend-forbidden-paths.md>`
- `<see: <workspace>/.cursor/skills/shared/frontend-architecture-layers.md>`
- 涉及上传：`<see: <workspace>/.cursor/skills/shared/frontend-upload-workflow.md>`
- 涉及状态/按钮：`<see: <workspace>/.cursor/skills/shared/frontend-state-button-matrix.md>`

## Mini Bugfix Prompt（≤ 15 行）

适合：单 warning / 单文案 / 单 className / 单 mapper 字段 / 单 Tooltip / 单 Modal 兼容 / 单 if 分支。

```md
# Mini Fix：<问题一句话>

现象：<Network/Console 一行 或 用户描述一句>
预期：<一句话>
最小修改：<具体文件路径 1 个>
禁止：扩大重构 / 改无关文件 / 改 <see: shared/frontend-forbidden-paths.md>
约束：只动现象点；保持 mapper / ViewModel / service 分层不变
验收：报错消失；无新 Console error；lint / typecheck 不新增；功能链路其余正常
输出：根因一句话 + 修改文件 + 验证截图描述
```

## Normal Bugfix Prompt（~ 35 行）

适合：联调状态错位 / mapper 字段语义不一致 / SWR mutate 错 / 本地态污染后端态 / 多文件影响 ≤ 5。

```md
# Bugfix：<问题标题>

## 当前现象
<贴 Network 关键请求 / Console 错误 / 截图描述>

## 正确预期
<业务正确链路一段，状态 + 操作 + 接口顺序>

## 排查范围（请先读代码再判断，禁止盲改）
- services/<feature>.ts
- hooks/<feature>/base/*.ts
- hooks/<feature>/mappers.ts
- hooks/use<Feature>Page.ts
- types/<feature>.ts
- components/<feature>/*
- app/<route>/page.tsx

## 必须先判断（按顺序）
1. **根因一句话**：是什么导致的
2. **责任归属**：前端 / 后端 / 字段语义不一致 / 本地态污染 / 三方库 bug
3. **是否在 file-change-plan 白名单内**（如有 A2A 流程）
4. **是否触碰禁改集**：<see: shared/frontend-forbidden-paths.md>
5. **是否需要 blocker-request**

## 修复要求
- 最小 diff：只动根因路径，不顺手 cleanup
- 保持分层：<see: shared/frontend-architecture-layers.md>
- 不引入新依赖
- 不改无关页面 / hook / service
- 不为修 warning 改业务逻辑
- 后端 bug → 不能前端假成功；走 blocker-request 或 needs-confirmation

## 验收
- [ ] 现象消失：<具体 Network/Console/UI 表征>
- [ ] 业务链路其余正常（列 2-3 个回归点）
- [ ] 状态机回归：<相关状态列出>
- [ ] Console 无新 error / warning
- [ ] lint / typecheck / prettier 不新增错误
- [ ] 禁改集 0 触碰

## 输出
- 根因（一句话）
- 责任归属（前端/后端/字段语义/...）
- 修改文件清单（含每个文件的最小 diff 描述）
- 验证结果（Network / Console / 状态 / UI 各 1 条）
- 残余风险（潜在副作用 / 未覆盖场景）
```

## 责任归属判断速查

| 现象 | 大概率根因 | 优先排查 |
|---|---|---|
| `xxx is undefined` | unwrap 漏 / 字段名错 | service unwrap、types 字段 |
| Network 200 但 UI 错 | mapper / ViewModel 错 | mapper、ViewModel 类型 |
| Network 4xx | 请求体错 / 鉴权过期 | payload builder、拦截器 |
| Network 5xx | 后端 | 联系后端；前端**不要**假成功 |
| 按钮该亮没亮 / 该灰没灰 | canXxx 错位 | mapper、状态矩阵 |
| 切 Tab 数据没变 | SWR key / mutate 错 | hook 的 SWR 配置 |
| 重试后还显示老错误 | 本地态没清 | 重试 handler reset 本地 state |
| `PUT /buser/undefined` | uploadUrl unwrap 漏 | 见 shared/frontend-upload-workflow.md |

## 反模式（Prompt 里要明示让 Agent 避免）

- 不读代码就改
- 用 try/catch 把后端 bug 吞掉、前端显示成功
- "顺手" 改其他文件的格式 / import 排序
- 为一个 warning 全局升级依赖
- 修 bug 时引入新依赖

## 何时不用本 Skill

- 是新接口对接（不是改 bug） → `prompt-frontend-api-integration`
- 是页面布局问题 → `prompt-frontend-page-refactor`
- 是 A2A 流程内 bug 且 state = qa_processing → 走 `prompt-a2a-workflow`（QA fail → Controller）
- 用户只想知道"是不是 bug" → 不出 Prompt，直接分析
