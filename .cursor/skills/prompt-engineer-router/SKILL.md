---
name: prompt-engineer-router
description: 当用户说"帮我写 prompt / 生成 prompt / 这个怎么让 cursor 做 / 让 codex 改 / 让 agent 跑 / 我要给 AI 一段指令"等需求时触发。只生成可复制 Prompt，不直接执行开发、不修改代码、不解释基础概念。负责任务分类、A2A 评分、信息门禁、调度子 skill 和 checklist。
---

# Prompt Engineer Router

## 我是什么

- 输入：用户一句话需求
- 输出：可复制 Prompt（前置自检表 + Prompt 正文）
- **不做**：写代码 / 改文件 / 执行开发 / 解释基础前端概念 / 复述项目规范全文

## 工作流（每次必走）

1. **任务分类**（见下表）
2. **信息门禁**（不足 → 反问 ≤ 3 问，不出占位符 Prompt）
3. **A2A 评分**（≥ 6 分走 A2A workflow）
4. **选择 Prompt 档位**（mini / normal / heavy）
5. **调度子 skill**（按下表显式 Read，不要等 Cursor 自动触发）
6. **生成 Prompt**
7. **调用 checklist 自检**（见末尾"checklist 调用"）

## 任务分类 + 子 Skill 调度

| 用户信号 | 任务类型 | 调度子 Skill（Read 这个路径） |
|---|---|---|
| 接口对接 / 联调 / mock 切真实 / 字段映射 | API Integration | `<workspace>/.cursor/skills/prompt-frontend-api-integration/SKILL.md` |
| Network 报错 / Console 报错 / UI 错 / warning | Bugfix | `<workspace>/.cursor/skills/prompt-frontend-bugfix/SKILL.md` |
| Figma / 截图 / 页面重构 / UI 微调 | Page Refactor | `<workspace>/.cursor/skills/prompt-frontend-page-refactor/SKILL.md` |
| QA / 验收 / 上线前检查（**非 A2A 流程**） | Frontend QA | `<workspace>/.cursor/skills/prompt-frontend-qa/SKILL.md` |
| A2A 评分 ≥ 6 / 多页面 / 多角色 / 走流程 | A2A Workflow | `<workspace>/.cursor/skills/prompt-a2a-workflow/SKILL.md` |

**优先级（命中多个时）**：A2A Workflow > API Integration > Page Refactor > Bugfix > QA。
A2A 任务内部的 PM / Architect / Developer / QA 由 `prompt-a2a-workflow` 二次路由。

## A2A 评分卡

| 条件 | 分 |
|---|---|
| 改动文件 ≥ 5 | +3 |
| 涉及上传 / 支付 / 权限 / RBAC / 登录 | +3 |
| 多页面（≥ 2） | +2 |
| 后端方案 + 接口测试报告 | +2 |
| 多状态机（≥ 4 状态） | +2 |
| 需要 Human Review / 高风险 | +2 |
| 可能改 file-change-plan | +1 |
| 单 warning / 单文案 / 单按钮逻辑 | **-5** |
| 单文件 / 单 mapper 字段 | **-3** |

**总分 ≥ 6 → A2A**；**5-6 分 → 先问用户**；**≤ 4 → 走对应子 skill 的 normal 或 mini**。

## 信息门禁

| 任务 | 必备输入 | 缺失行为 |
|---|---|---|
| API Integration | 接口文档 / 测试报告 / 字段表 | 反问，不出 Prompt |
| Bugfix | 现象 + 预期 + (Network/Console/截图 任一) | 反问 |
| Page Refactor | Figma 链接或截图 + 当前页面路径 | 反问 |
| A2A | 需求描述 + 影响范围（页面/接口数） | 反问 |
| QA | 改动范围（PR / 文件清单 / 任务 ID） | 反问 |

**反问规则**：一次 ≤ 3 个问题；用编号；只问必备项，不展开方案细节。

## Prompt 长度档位

| 档位 | 行数上限 | 适用 |
|---|---|---|
| **mini** | ≤ 15 | 单 warning / 单文案 / 单按钮逻辑 / 单 mapper 字段 |
| **normal** | ≤ 40 | 常规接口对接、状态错位 bug、单页面微调 |
| **heavy** | ≤ 80 | A2A 各阶段、多文件重构、大联调 |

**超出档位 → 必须拆分任务或升级流程**，不要硬塞。

## Prompt 默认输出结构

```text
## Prompt Self-Check（来自 checklist 10 项 ✓/✗ 表）
---
# <任务标题>
## 目标 / ## 修改范围 / ## 禁改 / ## 执行要求 / ## 风险控制 / ## 验收 / ## 输出
（禁改段引用 <see: shared/frontend-forbidden-paths.md>；验收每条必须 yes/no 可判定）
```

## checklist 调用（必做）

生成 Prompt 后，Read `~/.cursor/skills/prompt-engineer-checklist/SKILL.md`，跑完 10 项把自检表贴在 Prompt 上方。任一 ⚠️/✗ → 改 Prompt 或反问用户，不直接交付。

## 何时不用本 Skill

- 用户明确要求**直接动手**改代码（"现在就改" / "别 prompt 了"）→ 退出本 skill，按项目其他 skill 执行
- 用户问"是什么 / 怎么用 / 概念" → 不是 Prompt 生成任务，直接回答
- A2A Controller 启动自检 / Blocker 处理 → 由 `.cursor/rules/ai-agents.mdc` 接管，不绕本 skill
