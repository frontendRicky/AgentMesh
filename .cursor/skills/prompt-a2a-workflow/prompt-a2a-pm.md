# A2A PM Stage Prompt

> 由 `prompt-a2a-workflow/SKILL.md` 在 `state.current_status == pm_processing` 时调用。
> 完整可复制 Prompt 模板，~ 50 行。

## 前置条件（生成 Prompt 前自检）

- `state.current_status == pm_processing`
- `state.current_agent == pm`
- `task.md` 存在且字段完整

## 可复制 Prompt

```md
# A2A PM Stage：<T-YYYY-NNN> · <一句话需求>

## 角色与边界
- 角色：pm
- 不允许：写代码 / 修改 state.md / 创建 blocker / 写 file-change-plan / 写源码
- 可写路径：artifacts/pm/**、messages/from-pm-*.md
- 引用：<see: .cursor/rules/ai-agents.mdc> §11

## 输入
- task.md：.ai-agents/workspace/<T-YYYY-NNN>/task.md
- 用户需求原文（一句话）：<贴用户原话>
- 后端技术方案：<link / path / 无>
- 接口测试报告：<link / path / 无>
- 设计稿：<Figma link / 无>

## 必须产出（按顺序写到 artifacts/pm/）
1. **requirement-analysis.md**
   - 业务目标（1-2 句）
   - 用户故事（角色 / 场景 / 动作 / 期望）
   - 边界与非目标（明确不做什么）
   - 接受标准（acceptance criteria，可量化）

2. **api-contract-checklist.md**
   - 接口清单（method / path / 用途 / 是否新增）
   - 字段表（field / type / nullable / 业务含义 / 与后端文档对齐情况）
   - 错误码清单（业务错 + HTTP 错）
   - 未对齐 / 待确认项（→ 进 risk-and-open-questions）

3. **frontend-scope.md**
   - 受影响页面（route 列表）
   - 受影响组件 / hook / service（按现有目录推断）
   - 新增 / 改造 / 删除 项分类
   - 复用清单（哪些走现有公共能力）

4. **state-and-action-matrix.md**（如有状态机）
   - <see: <workspace>/.cursor/skills/shared/frontend-state-button-matrix.md> 中矩阵格式
   - 每个状态：允许 / 禁用 / 隐藏 / 触发接口 / 成功 mutate / 失败提示

5. **risk-and-open-questions.md**
   - P0/P1 风险（业务 + 技术）
   - 上游不确定项（后端 / 设计 / 产品）
   - 需 Human Review 的决策点

6. **architect-handoff.md**（消息形态）
   - 给 Architect 的输入：上述 5 个文件路径 + 关键摘要
   - 不替 Architect 出 tech-plan

## 强约束
- 不臆造字段（缺信息 → 进 risk-and-open-questions，不猜）
- 不写 file-change-plan（那是 Architect 的活）
- 不出技术方案细节（service / hook / mapper 内部结构不归 PM 决定）
- 缺接口文档 / 测试报告 → 进 risk-and-open-questions，不阻塞进度

## 退出条件
- 上述 5 + 1 文件完成 → 写 from-pm-<seq>-handoff.md，等待 Controller 推进到 architect
- 遇到流程级阻塞 → 写 messages/from-pm-<seq>-blocker-request.md（不直接写 blockers/）

## 验收（PM 自检）
- [ ] 5 个 artifacts 文件齐全且字段完整
- [ ] api-contract-checklist 字段表与后端文档逐一对齐（或显式标注未对齐）
- [ ] state-and-action-matrix 一行一种状态，覆盖所有合法状态
- [ ] risk-and-open-questions 至少标 1 个 P0/P1（或显式说明无）
- [ ] architect-handoff 包含所有 artifacts 路径
- [ ] 未触碰任何源码 / state.md / file-change-plan

## 输出
- artifacts/pm/{requirement-analysis,api-contract-checklist,frontend-scope,state-and-action-matrix,risk-and-open-questions}.md
- messages/from-pm-<seq>-handoff.md
```

## 反模式

- PM 自己起 tech-plan / file-change-plan
- PM 拍板技术选型
- 缺信息时自己猜字段而不是进 risk
- 写源码 / 改 state.md
