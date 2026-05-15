---
openspec_id: OS-2026-004
title: A2A Console — 中文小白模式与前端项目生成向导
status: draft
proposed_a2a_task_id: T-2026-004
owner: zhangxia
created_at: 2026-05-15
schema_version: openspec/v1
---

# OpenSpec: A2A Console 中文小白模式与前端项目生成向导

## 1. 背景与动机

当前 A2A Console 已能展示 Agent 协作、产物、Metrics、模型选择等信息，但默认面向懂前端 / 懂 A2A 文件结构的人。用户的新诉求是：

- 有些同事看不懂英文；
- 有些同事不懂前端技术，但会打字、能描述业务；
- 希望他们在页面里能看懂每一步、能自己选择模型 / 生成策略；
- 最终可以把页面当作“前端项目生成入口”，通过 A2A 流程生成一个前端项目。

本 OpenSpec 将 Console 从“技术驾驶舱”升级为“双模式产品”：

- **普通模式**：中文、低术语、向导式，面向非技术同事；
- **专家模式**：保留现有 A2A 细节、Artifacts、Metrics、契约调试能力，面向开发者 / 管理员。

## 2. 目标

### G1 — 全中文、低门槛的信息架构

- 页面主要文案必须为中文，不以英文术语作为默认入口名称。
- 对不可避免的术语提供中文解释，例如：
  - Task → 任务
  - Agent → 角色助手
  - Artifact → 产物文档
  - Model → 模型
  - Context → 上下文容量
- 非技术用户默认进入“生成项目”向导，而不是直接看到状态机、token、frontmatter。
- 专家信息默认折叠，允许通过“专家模式”开关展开。

### G2 — 前端项目生成向导

新增一个面向非技术同事的主流程：

1. 选择项目类型：官网 / 后台管理 / CRM / 数据看板 / 表单系统 / 电商页面 / 自定义。
2. 用中文描述业务：用户可以像发消息一样输入需求。
3. 选择页面范围：页面清单、核心字段、是否需要登录、是否需要图表、是否接真实接口。
4. 选择视觉风格：稳重商务 / 科技感 / 极简 / 活泼 / 按参考截图或文字描述。
5. 选择生成策略：
   - 快速出稿
   - 质量优先
   - 成本优先
   - 严格还原设计
6. 选择模型：用“推荐 / 更快 / 更强 / 更省”这种中文标签展示，不要求用户理解模型 slug。
7. 生成并预览 A2A 任务计划：页面先生成 PRD / OpenSpec / 页面清单摘要，用户确认后再进入 A2A 执行。

### G3 — 模型选择对非技术用户可理解

- 模型选择不只展示 slug，需要展示中文解释：
  - 适合做什么
  - 速度
  - 质量
  - 预估成本等级
  - 上下文容量
- 支持三类入口：
  - “系统推荐”
  - “我想更快”
  - “我想效果更好”
- 专家模式下仍显示真实模型 slug、role override、context size。
- 模型选择应落地到 A2A 任务配置或本地配置，Architect 必须在 tech-plan 中锁定写入位置。

### G4 — 通过 A2A 生成前端项目

从向导提交后，Console 应创建或驱动一个 A2A 任务，让 PM / Architect / Developer / QA 按现有流程生成前端项目。

推荐 MVP 路径：

1. Console 先创建“生成任务包”：
   - requirement.md
   - prd.md
   - openspec snapshot
   - model selection snapshot
   - user input snapshot
2. 用户确认后才允许启动 A2A 执行。
3. 执行方式必须由 Architect 明确：
   - A. 仅生成任务包，由技术同事在 Cursor / Codex 中继续跑；
   - B. Console 调用本地受控 A2A runner；
   - C. 引入 server-side job queue，异步执行并展示进度。

若选择 B/C，必须满足：

- 不在浏览器保存 API Key；
- 不在日志中输出 secret；
- 不允许任意命令执行；
- 只能在白名单 workspace/output 目录写入；
- 每次真正执行前需要用户确认。

### G5 — 生成过程可被非技术同事看懂

执行中的页面不展示“pm_processing / architect_completed”等内部状态作为主文案，而是展示：

- 正在整理需求
- 正在设计页面结构
- 正在生成代码
- 正在检查质量
- 等待你确认
- 已完成，可以预览

专家模式下可以显示原始 A2A 状态、messages、artifacts。

### G6 — 生成结果可预览、可交接

完成后，普通用户至少能看到：

- 项目名称
- 页面列表
- 预览入口或本地运行说明
- 生成文件摘要
- 下一步建议

专家模式下可进入现有 Artifacts / Metrics / Reviews。

## 3. 非目标

- 本期不把 A2A Console 做成 SaaS 平台。
- 本期不做多用户登录、权限系统、云端存储。
- 本期不保证一次生成即可生产上线。
- 本期不自动部署到 Vercel / Netlify，除非 Architect 明确拆成后续任务。
- 本期不移除现有专家视图。
- 不允许为方便实现而绕过 path-guard、file-size-guard、TASK_ID 校验。

## 4. 关键接口草案

字段名以 Architect tech-plan 为准；以下为产品级建议。

### 4.1 获取生成模板

`GET /api/a2a/project-generator/templates`

```json
{
  "ok": true,
  "data": {
    "items": [
      {
        "id": "admin-dashboard",
        "name": "后台管理系统",
        "description": "适合客户管理、订单管理、数据表格、权限页面",
        "recommended_strategy": "quality"
      }
    ]
  }
}
```

### 4.2 创建生成草稿

`POST /api/a2a/project-generator/drafts`

```json
{
  "project_name": "客户管理后台",
  "project_type": "admin-dashboard",
  "business_description": "给销售团队使用，管理客户、跟进记录和合同金额",
  "pages": ["首页看板", "客户列表", "客户详情", "合同管理"],
  "style_preference": "稳重商务",
  "generation_strategy": "quality",
  "model_profile": "recommended"
}
```

返回：

```json
{
  "ok": true,
  "data": {
    "draft_id": "D-2026-004-001",
    "summary": "将生成一个后台管理系统，包含 4 个页面，偏稳重商务风格。",
    "prd_preview": "...",
    "openspec_preview": "..."
  }
}
```

### 4.3 将草稿转为 A2A 任务

`POST /api/a2a/project-generator/drafts/:draftId/tasks`

返回：

```json
{
  "ok": true,
  "data": {
    "task_id": "T-2026-005",
    "task_path": ".ai-agents/workspace/T-2026-005",
    "next_action": "confirm_to_start"
  }
}
```

### 4.4 启动或继续生成

`POST /api/a2a/project-generator/tasks/:taskId/start`

是否实现由 Architect 决定。若实现，必须是本地受控 job，不能让用户传入任意 shell 命令。

## 5. 数据与契约要求

- 延续 OS-2026-003 的 contract 思路：新增 payload 必须有 zod schema。
- client/server 对以下 payload 做 safeParse：
  - generator templates
  - generator draft request/response
  - model profile selection
  - task creation response
  - generation job status
- 所有写入路径必须使用 path-guard 同类校验。
- 所有 taskId 必须继续使用 `^T-\d{4}-\d{3}$`。

## 6. 页面要求

### 6.1 生成项目首页

- 默认第一屏就是“你想生成什么项目？”
- 输入框文案必须鼓励中文表达，例如：“把你的业务想法写在这里，不用写技术名词。”
- 提供模板按钮：官网、后台管理、CRM、数据看板、表单系统、电商页面、自定义。
- 展示“下一步：我会帮你整理页面和需求”的中文说明。

### 6.2 需求确认页

- 展示系统整理后的页面清单、功能点、数据字段、风格偏好。
- 用户可以编辑中文文本。
- 不展示 markdown frontmatter。

### 6.3 模型选择页

- 默认“系统推荐”。
- 卡片展示：
  - 更快
  - 更强
  - 更省
  - 专家自定义
- 每张卡片必须说明适用场景。

### 6.4 生成进度页

- 用普通中文展示阶段。
- 可以展开专家详情查看 A2A 原始消息。
- 遇到 blocker 时，用用户能懂的话说明“缺少什么信息”和“你需要补充什么”。

### 6.5 结果页

- 展示页面预览入口、文件摘要、如何继续修改。
- 如果无法自动启动 dev server，给出中文步骤，不要求用户理解 npm 细节。

## 7. 验收标准

| ID | 描述 |
|----|------|
| AC-01 | 非专家默认入口为“生成项目”向导，主要可见文案为中文 |
| AC-02 | 用户不懂前端术语也能完成：项目类型、业务描述、页面范围、风格、模型策略选择 |
| AC-03 | 模型选择展示中文解释，不只展示 slug；专家模式仍可看 slug |
| AC-04 | 向导提交后能生成 PRD/OpenSpec/用户输入快照，并能转成 A2A task |
| AC-05 | 若实现一键启动执行，必须有确认步骤、job 状态、取消/失败态、受控命令边界 |
| AC-06 | 所有新增 API 使用共享 contract schema，并在 client/server safeParse |
| AC-07 | 新增写入路径全部防路径穿越；taskId 校验无回归 |
| AC-08 | 普通模式不展示 frontmatter、tokens、raw status 作为主内容 |
| AC-09 | 专家模式保留现有 A2A Console 能力，不破坏 T-2026-002/T-2026-003 功能 |
| AC-10 | client/server typecheck 通过，必要的 QA 手工用例通过 |

## 8. 风险与待确认

| 风险 | 缓解 |
|------|------|
| 一键执行 A2A 涉及 LLM/API key/命令执行风险 | Architect 必须先给执行架构和安全边界；默认先做“生成任务包” |
| 非技术用户输入过于模糊 | 需求确认页必须有可编辑摘要和缺失信息提示 |
| 中文化后专家效率下降 | 双模式，专家能力不移除 |
| 生成项目输出目录越界 | output_root 白名单 + path-guard + slug 校验 |
| 模型选择误导成本 | 展示“预估等级”，不承诺精确价格 |

## 9. A2A 执行计划

| 阶段 | 产物 |
|------|------|
| PM | requirement.md / prd.md / task-breakdown.md |
| Architect | tech-plan.md / file-change-plan.md / risk-plan.md，重点锁定执行架构与写入边界 |
| Human Review | 审核是否允许 Console 写 task / 启动本地 A2A job |
| Developer | 代码实现 + implementation-log.md / changed-files.md |
| QA | test-report.md / acceptance-checklist.md，覆盖非技术用户完整流程 |

## 附录 A：给 Architect 的重点问题

1. MVP 是否只做“生成任务包”，还是允许“一键启动 A2A 执行”？
2. 如果允许执行，调用现有 `.ai-agents/scripts` 的方式是什么，如何避免任意命令执行？
3. 生成项目保存到哪里，如何命名，是否允许覆盖？
4. 模型选择快照写入 `.ai-agents`、apps config，还是只进 task artifact？
5. UI 采用双模式路由还是同页面折叠专家信息？
