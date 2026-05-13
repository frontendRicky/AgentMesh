---
name: prompt-frontend-qa
description: 用户已经确认是"日常 QA / 上线前快速验收 / PR Review 前自检 / 非 A2A 流程的回归"时使用本 Skill，生成轻量 QA Prompt。不用于 A2A 流程内 QA 阶段（那条路走 prompt-a2a-workflow）。只生成 Prompt，不直接执行 QA、不改代码。
---

# Prompt Frontend QA（轻量验收）

## 我是什么

- 输入：改动范围（PR / 文件清单 / 任务描述）+ 验收维度
- 输出：日常验收 Prompt（不走 A2A test-report.md schema）
- 不做：执行 QA / 改代码 / 接管 A2A QA 阶段

## 何时走本 Skill vs A2A QA

| 场景 | 走 |
|---|---|
| 单个 PR 上线前自检 / 小功能验收 | **本 Skill** |
| 多人开发后局部回归 | **本 Skill** |
| 紧急 hotfix 后验收 | **本 Skill** |
| A2A 任务 state = qa_processing | `prompt-a2a-workflow` |
| 验收要产 `artifacts/qa/test-report.md` | `prompt-a2a-workflow` |

## 依赖

- `<see: <workspace>/.cursor/skills/shared/frontend-forbidden-paths.md>`
- `<see: <workspace>/.cursor/skills/shared/frontend-state-button-matrix.md>`
- 涉及上传：`<see: <workspace>/.cursor/skills/shared/frontend-upload-workflow.md>`

## 日常 QA Prompt 模板（normal，~ 35 行）

```md
# Frontend QA：<功能 / PR 名>

## 范围
- 改动文件：<列出，或 PR diff 链接>
- 受影响页面：<route 列表>
- 受影响接口：<API 列表>

## 验收维度
1. **接口链路**
   - Network 请求路径 / method / payload 正确
   - response unwrap 正确
   - Long ID 全 string
   - 错误码处理一致

2. **状态流转**
   - 列状态矩阵（见 <see: shared/frontend-state-button-matrix.md>）
   - 每个状态下：允许 / 禁用 / 隐藏的操作
   - 禁用按钮带 tooltip

3. **空态 / loading / error**
   - 首次加载 loading
   - 空数据 EmptyState 文案
   - 接口 error 时 UI 表现
   - 重试入口可用

4. **Console / Network**
   - Console 无新 error / warning
   - 没有重复请求
   - 没有 404 / CORS / mixed content

5. **禁改集未触碰**
   - 见 <see: shared/frontend-forbidden-paths.md>
   - 列出 PR diff 中触碰的文件，确认无越界

6. **lint / typecheck / prettier**
   - 不新增 lint error
   - 不新增 TS error
   - prettier 已格式化

7. **已知风险回归**
   - <从开发自报或 Architect 风险清单回归>

## 禁止
- 自己改源码修 bug（QA 不修代码）
- 改测试代码 / 改 fixture 让用例通过
- 跳过维度（任一维度跳过必须写理由）

## 输出
- 验收结论：pass / fail / needs-changes
- 每个维度的 ✓/✗ + 证据（Network 截图描述 / Console 截图描述 / UI 描述）
- 发现的 issue 清单（每条含：复现步骤 / 期望 / 实际 / 严重程度）
- 残余风险 / 建议下次验收点
```

## Mini QA Prompt（≤ 15 行，hotfix / 单点回归用）

```md
# Mini QA：<问题/功能>

范围：<1-2 文件 或 1 个交互>
回归路径：
1. <步骤 1 → 期望 UI / Network>
2. <步骤 2 → 期望状态>
3. <步骤 3 → 期望文案>
检查：
- Console 无新 error
- Network 无 4xx/5xx
- 不影响：<列 1-2 个最容易回归坏的功能>
输出：✓/✗ + 一句话证据
```

## 严重程度分级（issue 必须标）

| 级别 | 含义 | 处置 |
|---|---|---|
| **P0** | 阻塞上线、数据错乱、登录失败、支付错 | 立即修，不修不上 |
| **P1** | 核心流程不可用 / 状态错 / 数据丢失风险 | 修完再上 |
| **P2** | 体验问题、文案、视觉偏差、非关键路径 | 可下次迭代 |
| **P3** | warning、deprecated、内部信息 | 单独清理任务 |

## 反模式（Prompt 里要明示让 Agent 避免）

- 验收时改源码（QA 不修代码）
- 改 fixture / mock 让用例通过
- 跳过维度但不写理由
- 验收结论用"差不多"、"应该没问题"等非量化表述
- 把 P2 / P3 当 P0 上报，拖累上线

## 何时不用本 Skill

- A2A 流程内 QA 阶段 → 走 `prompt-a2a-workflow/prompt-a2a-qa.md`
- 用户问"怎么做单元测试" → 不是 QA 验收，不走本 skill
- 用户要做安全 / 性能专项 → 单独走对应 skill
