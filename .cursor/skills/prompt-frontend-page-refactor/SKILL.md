---
name: prompt-frontend-page-refactor
description: 用户已经确认任务类型为"页面生成 / Figma 还原 / 页面重构 / UI 微调 / 中后台页面组件化"时使用本 Skill，生成 Plan Prompt 或微调 Prompt。不用于初步路由判断（路由由 prompt-engineer-router 负责）。只生成 Prompt，不直接执行开发、不改代码、不改业务逻辑 / submit / auth / route。
---

# Prompt Frontend Page Refactor

## 我是什么

- 输入：Figma 链接或截图 + 当前页面路径
- 输出：Plan Prompt（先 Plan 不实现）或微调 Prompt（一次一个视觉问题）
- 不做：执行开发、改业务逻辑、改 submit / auth / route

## 依赖

- `<see: <workspace>/.cursor/skills/shared/frontend-forbidden-paths.md>`
- `<see: <workspace>/.cursor/skills/shared/frontend-architecture-layers.md>`
- 涉及按钮显隐：`<see: <workspace>/.cursor/skills/shared/frontend-state-button-matrix.md>`

## 核心原则

1. **先 Plan 后实现**：第一次必出 Plan Prompt，用户确认后再出实现 Prompt
2. **优先复用**：现有 component / hook / token / style 常量；不复制 JSX
3. **只提取差异**：不重写整页
4. **不改业务**：submit / auth / reporter / timer / registry / route / handler 不动
5. **微调一次一个问题**

## 页面结构拆解（Plan 必须按这层级拆）

```text
Page
├── Shell / Layout           (Sider + Topbar + Container)
├── Header                   (面包屑 / 页面标题 / 全局操作)
├── Content
│   ├── Filter / Toolbar
│   ├── DataView (Table / List / Grid)
│   └── EmptyState / LoadingState / ErrorState
├── Action / Footer          (批量操作 / 分页)
├── Feedback                 (toast / Notification)
└── Modal / Drawer           (新建 / 编辑 / 详情)
```

## Figma 必备输入（信息门禁）

生成 Prompt 前必须从用户拿到：

- Figma 链接（或截图）
- nodeId（如有）
- 当前页面路径（`app/<route>/page.tsx`）
- 目标设备宽度 + 断点（PC / iPad / 移动端）
- 必须复用的组件清单（如已知）
- 明确**不改**的范围（兜底，防止跑偏）

缺任一 → 反问 ≤ 3 问，不出 Prompt。

## Plan Prompt 模板（不实现，~ 35 行）

```md
# Page Refactor Plan：<页面名>

## 目标
基于 Figma <link/nodeId> + 当前代码 <path>，输出一次性 Plan，不要写代码。

## 输入
- Figma：<link 或 截图>
- nodeId：<id>
- 当前页面：<path>
- 设备宽度 + 断点：<PC 1440 / iPad 1024 / mobile>
- 必须复用：<列出已知公共组件 / token>
- 明确不改：<submit / auth / route / 业务接口 / 状态机>

## Plan 必须输出
1. **当前页面结构树**（Shell → Header → Content → ...）
2. **目标页面结构树**（按 Figma）
3. **差异点清单**（新增 / 删除 / 移位 / 样式调整 / 文案）
4. **可复用清单**：现有 component / hook / token / style 常量
5. **新增 / 扩展清单**：必须新建的 component 或 token（每个写一句为什么）
6. **修改文件范围**（白名单）
7. **不改动范围**（业务逻辑 / submit / auth / route / 状态机）
8. **风险点**（P0/P1，例：影响列表 mutate / 影响 Modal 表单回填）
9. **回归 checklist**（点 N 个交互、看 N 个状态）

## 禁止
- 直接实现
- 大范围重构
- 复制已有页面整段 JSX
- 新增重复 token / 重复 className
- 改业务逻辑 / submit / reporter / timer / registry / auth / route / 状态机
- 改 <see: shared/frontend-forbidden-paths.md>

## 输出
- 上述 9 段 Plan
- 等待用户确认后再生成实现 Prompt
```

## 微调 Prompt 模板（一次一个问题，~ 15 行）

适合：按钮间距 / 弹窗样式 / 边框 / placeholder / 列宽 / 空态文案 / Tooltip / loading 等单点问题。

```md
# UI Tweak：<一句话问题>

页面：<path>
当前：<现状描述 + 截图描述>
目标：<期望描述 + Figma 节点>
最小修改：<具体 component / className / token>
约束：
- 只动视觉，不动业务
- 优先用现有 token（不要新建）
- 不改 <see: shared/frontend-forbidden-paths.md>
- 不改其他视觉问题（一次一个）
验收：单点视觉一致；其他视觉点不变；状态/交互不变；lint 不新增
```

## 复用判断优先级

```text
1. 业务组件（已有 + 同语义）
2. 通用组件（项目内 / antd / 业务包）
3. 现有 hook（页面数据 / 表单 / 弹窗管理）
4. 现有 service / mapper（不为 UI 重新发请求）
5. 现有 token / Tailwind class 常量
6. 现有 styles 常量 / class 组合
```

复用前先 `Glob` 现有同名 / 同语义文件，找到就用，找不到才考虑新建（新建必须列理由）。

## 反模式（Prompt 里要明示让 Agent 避免）

- 复制已有页面整段 JSX 改皮
- 为一次性 UI 抽象出"通用组件"
- 改业务 hook / state 来适配新 UI
- 改 ConfigProvider / 全局主题
- 改 submit / auth / route 来适配新交互
- 一次微调同时改 5 个视觉点

## 何时不用本 Skill

- 是 bugfix（页面有报错） → `prompt-frontend-bugfix`
- 是接口对接 → `prompt-frontend-api-integration`
- 多页面 + 多接口 + 多状态 → A2A 评分 ≥ 6，走 `prompt-a2a-workflow`
- 用户只想要"组件复用清单" → 不需要 Plan Prompt，直接出表
