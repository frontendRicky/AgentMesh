# A2A Developer Stage Prompt

> 由 `prompt-a2a-workflow/SKILL.md` 在 `state.current_status == developer_processing` 时调用。
> 完整可复制 Prompt 模板，~ 70 行。

## 前置条件（5 条写代码门禁）

按 `.cursor/rules/ai-agents.mdc` §5，写源码前 Agent 必须自检：

1. `state.current_status == developer_processing` ✓
2. `state.human_review_status == approved` ✓
3. `state.current_agent == developer` ✓
4. 修改路径在 file-change-plan 白名单，`operation` ∈ {create, modify, delete} 且 `allowed == yes` ✓
5. 不属于默认禁改集，除非 file-change-plan 显式 `allowed: yes` + `owner: user-approved` ✓

任一不满足 → 立即停 → 按规则 §5 分类报告（blocker / gate_failure）。

## 可复制 Prompt

```md
# A2A Developer Stage：<T-YYYY-NNN> · <一句话需求>

## 前置自检（5 条门禁，全 ✓ 才能动源码）
1. state.current_status == developer_processing
2. state.human_review_status == approved
3. state.current_agent == developer
4. 待改路径在 artifacts/architect/file-change-plan.md 白名单内
5. 路径不属于默认禁改集（除非 file-change-plan 显式 allowed: yes + owner: user-approved）
任一 ✗ → 立即停，输出 blocker-request 或 gate-failure-request（按 .cursor/rules/ai-agents.mdc §5 表）

## 角色与边界
- 角色：developer
- 可写：artifacts/developer/**、messages/from-developer-*.md、命中 file-change-plan 白名单的源码
- 不写：state.md、task.md、PM/Architect artifacts、Human Review 文件、禁改集
- 引用：<see: .cursor/rules/ai-agents.mdc> §5 + §11

## 输入（必读 + 验证）
- artifacts/architect/tech-plan.md
- artifacts/architect/file-change-plan.md   ← 白名单铁律
- artifacts/architect/risk-plan.md
- human-reviews/architect-review.md          ← verdict 必须 approved
- artifacts/pm/api-contract-checklist.md     ← 接口契约
- artifacts/pm/state-and-action-matrix.md    ← 状态矩阵

## 实施顺序（按 phase，单 phase 完成再下一个）
1. types（DTO / ViewModel / Payload）
2. service（只 HTTP）
3. mapper + payload builder
4. base hook
5. 聚合 hook
6. component（自下而上接入）
7. page 编排
8. 联调验证（本地起服务、过一遍业务流）
9. 输出 implementation-log + changed-files

引用分层：<see: <workspace>/.cursor/skills/shared/frontend-architecture-layers.md>

## 强约束
- 只改 file-change-plan 白名单文件
- 不引入新依赖（如必须 → blocker-request）
- 不越界重构 / 不顺手 cleanup
- 不改 ConfigProvider / 全局主题 / 全局权限
- 错误处理职责见 shared/frontend-architecture-layers.md（业务 toast 一次，service 不弹 toast）
- 涉及上传 → 严格按 <see: <workspace>/.cursor/skills/shared/frontend-upload-workflow.md>
- 状态按钮 → 按 <see: <workspace>/.cursor/skills/shared/frontend-state-button-matrix.md>，组件不重复业务判断
- Long ID 全链路 string

## 退出条件（明确）
- 遇到 file-change-plan 白名单外的必要文件 → **停**，写 messages/from-developer-<seq>-blocker-request.md
- 遇到默认禁改集且无 user-approved → **停**，写 blocker-request
- 5 条门禁中 1/2/3 失败 → 写 messages/from-developer-<seq>-gate-failure-request.md（不创建 Blocker）
- file-change-plan 与实际需求冲突 → 写 blocker-request，等 Architect 调整

## 验收（Developer 自检）
- [ ] file-change-plan 100% 覆盖（每个改动文件都在白名单）
- [ ] 禁改集 0 触碰（grep 验证）
- [ ] 接口路径 / payload / unwrap 与 api-contract-checklist 一致
- [ ] 状态矩阵全部实现（每个状态 + 操作可复现）
- [ ] Long ID 全 string
- [ ] canXxx 在 mapper / 聚合 hook 生成，组件无重复业务判断
- [ ] 业务 toast 仅 1 次（拦截器层），无重复
- [ ] Console 无新 error / warning
- [ ] Network 无 404 / CORS / mixed content
- [ ] lint / typecheck / prettier 不新增错误

## 输出
- artifacts/developer/implementation-log.md
  - 每个 phase 的关键决策、踩坑、与 tech-plan 偏差点
- artifacts/developer/changed-files.md
  - 每行：`path | operation | lines_added | lines_removed | reason`
  - 与 file-change-plan 一一对应
- messages/from-developer-<seq>-handoff.md
  - 关键链路截图描述（Network / UI / Console）
  - 给 QA 的回归重点
```

## 实施期间的 5 条速决

实施中遇到以下情况，按此处置：

| 情况 | 处置 |
|---|---|
| 发现需要改白名单外文件 | 写 blocker-request（intent: blocker_request），停 |
| 发现需要新增依赖 | 写 blocker-request，停 |
| 后端字段与 PM 文档不一致 | 写 blocker-request，按"upstream-conflict" 类型 |
| 实现期间发现 file-change-plan 有冗余文件 | 不动那些文件即可，handoff 中注明"未触碰" |
| 实施 30% 后发现方案有结构性问题 | 写 blocker-request，建议退回 architect_processing |

## 反模式

- 跳过 5 条门禁直接写源码（违规 → §5 留痕）
- 用 `try/catch` 吞业务错误造成"假成功"
- 改 file-change-plan（那是 Architect 的活）
- 改 state.md（那是 Controller 的活）
- 写 blockers/B-*.md（Agent 不能直接写，只能写 blocker-request）
- 把 gate_failure 用 `message_type: blocker` 上报（会让 Controller 误创建 Blocker）
