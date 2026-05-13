---
name: prompt-frontend-api-integration
description: 用户已经确认任务类型为"前端接口对接 / 联调 / mock 切真实接口 / 字段映射 / DTO 改造"时使用本 Skill，生成可复制 API Integration Prompt。不做初步路由判断（路由由 prompt-engineer-router 负责）。只生成 Prompt，不直接执行开发、不改代码。
---

# Prompt Frontend API Integration

## 我是什么

- 输入：接口文档 / 测试报告 / 字段表 + 页面路径
- 输出：可复制的接口对接 / 联调 Prompt
- 不做：执行开发、解释 SWR / mapper 是什么

## 依赖（生成 Prompt 时引用）

- `<see: <workspace>/.cursor/skills/shared/frontend-forbidden-paths.md>`
- `<see: <workspace>/.cursor/skills/shared/frontend-architecture-layers.md>`
- `<see: <workspace>/.cursor/skills/shared/frontend-state-button-matrix.md>`
- 涉及上传：`<see: <workspace>/.cursor/skills/shared/frontend-upload-workflow.md>`

## 联调必查项（写进 Prompt 「执行要求」段）

- 接口路径 / method / baseURL
- request body / query / header
- response unwrap（`{ code, data, msg }` vs 直接 data）
- DTO 字段类型与文档对齐
- string / number normalize
- **Long ID 全链路 string**（mapper 转一次，组件别再转）
- 状态枚举映射（数字 → 业务 enum）
- Tab key 与 status 对齐
- mutate 策略（success → invalidate 哪些 key）
- optimistic update 回滚方式
- polling 触发条件 + 停止条件

## 完整可复制 Prompt 模板（normal，~ 40 行）

```md
# Frontend API Integration：<功能名>

## 目标
基于 <后端文档链接 / 测试报告 路径>，完成 <页面> 的接口对接与联调。

## 修改范围
允许修改：
- services/<feature>.ts
- types/<feature>.ts
- hooks/<feature>/{base,mappers,payloads,use<Feature>Page}.ts
- components/<feature>/*
- app/<route>/page.tsx

禁改：
<see: shared/frontend-forbidden-paths.md>
本次额外解禁：<无 / 列文件 + 批准来源>

## 分层与约束
<see: shared/frontend-architecture-layers.md>
按层实施顺序：types → service → mapper + payload → base hook → 聚合 hook → component → page。

## 执行要求
1. 接口契约：先对照后端文档，列出字段表（field / type / nullable / 业务含义），不臆造
2. service 只做 HTTP，返回 DTO，不 toast、不 normalize
3. mapper 把 DTO → ViewModel，Long ID 强制 string，生成 canXxx
4. payload builder 统一生成 request body，trim / 默认值集中处理
5. 聚合 hook 编排 SWR、mutate、handlers、UI state；不在 component 请求
6. component 只消费 ViewModel + callbacks，不写业务状态判断
7. 状态按钮：<see: shared/frontend-state-button-matrix.md>，输出状态矩阵
8. 错误处理：业务 toast 走拦截器一次；hook / page / component 不重复 toast
9. <如涉及上传：见 shared/frontend-upload-workflow.md>

## 风险控制
- P0/P1 风险：<列 1-2 条，如：mutate 影响列表分页 / 字段语义与旧版不一致>
- 退出条件：实施中发现需要改禁改集 → 输出 blocker-request，停止修改

## 验收
- [ ] Network 中接口路径 / method / payload 与文档一致
- [ ] response unwrap 正确，组件不再消费 raw
- [ ] Long ID 在 ViewModel 全为 string
- [ ] 状态矩阵中所有状态 + 操作均可复现
- [ ] canXxx 在 mapper / 聚合 hook 生成，组件无重复业务判断
- [ ] 业务 toast 只出现 1 次
- [ ] lint / typecheck / prettier 不新增错误

## 输出
- 字段表（field / type / nullable）
- 状态矩阵
- 修改文件清单
- 残余风险
```

## 缩减版（mini，对接单接口、~ 15 行）

```md
# API Integration Mini：<接口名>

接口：<METHOD path>，文档：<link>
页面：<route>
修改：services/<f>.ts + hooks/<f>/{mappers,base}.ts + 1 个组件
禁改：<see: shared/frontend-forbidden-paths.md>
约束：service 只 HTTP；mapper 出 ViewModel + canXxx；Long ID = string
验收：Network 对齐文档；ViewModel 类型稳定；无重复 toast；lint 不新增
```

## 反模式（Prompt 里要明示让 Agent 避免）

- 组件里直接消费 raw response
- 组件里写 normalize 逻辑
- service 里 toast
- 拦截器 + hook 双重 toast
- Long ID 在某些层是 number、某些层是 string
- 状态枚举数字直接进 JSX 三元

## 何时不用本 Skill

- 是 bugfix（联调发现错） → 走 `prompt-frontend-bugfix`
- 是页面布局 / UI 还原 → 走 `prompt-frontend-page-refactor`
- 任务复杂度 A2A 评分 ≥ 6 → 走 `prompt-a2a-workflow`
- 用户只想要"字段表" → 不需要完整 Prompt，直接出表
