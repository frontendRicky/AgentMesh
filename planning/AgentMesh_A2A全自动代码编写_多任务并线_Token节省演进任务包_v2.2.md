# AgentMesh A2A 全自动代码编写与多任务并线演进计划

**副标题：从手动复制粘贴与人工审核，升级到策略驱动、多任务并线、Token 可控的自动编程系统**  
**版本：v2.2 · 2026-05-17**  
**用途：给自己长期复盘，也可以直接交给 Codex / Cursor 作为 AgentMesh 自升级、并线开发、多项目自动编程、Token 成本优化的任务包。**

---

## 0. 本次澄清后的真正目标

你原本的工作习惯是：自己手动复制 Prompt，开多个 Agent、多模型，让 PM / Architect / Developer / QA 分别工作，然后你人工检查、人工放行。  
这套方式的好处是安全、可控、容易理解；坏处是你本人会变成整个系统的瓶颈。

所以 AgentMesh 未来真正要走的方向不是“永远人工审核”，而是：

> **让人工审核从默认动作，逐步退化为异常处理；让 A2A 系统在策略、测试、沙箱和回滚保护下，自动规划、自动写代码、自动测试、自动修复、自动交付。**

这份计划的核心思想是：

- 早期人工审核是安全网，不是终点。
- 未来的核心不是“人每一步点确认”，而是“系统知道什么可以自动放行，什么必须停下来”。
- 人的角色从“流水线操作员”升级为“目标制定者、策略制定者、异常裁判”。
- AgentMesh 的商业价值从“多 Agent 协作门禁”升级为“可信自动编程流水线”。

### 0.1 本次新增的并线目标

你补充的关键需求是：**AgentMesh 不能只服务一个当前任务，它要能并线开发多个任务；系统自升级时，也不能阻塞你用它去做别的项目。**

这意味着 AgentMesh 未来不能停留在“active-task 单任务工作台”，而要升级为：

> **多任务 Task Pool + 多运行 Run Pool + 多项目 Project Pool 的 A2A 自动编程调度系统。**

最终你想要的体验应该是：

```txt
上午：AgentMesh 自己在后台升级 Console 的 Run Session 功能。
同时：另一个 Agent 线在生成客户项目 A 的后台管理系统。
同时：第三个 Agent 线在修复客户项目 B 的 bug。
同时：QA/Fix Agent 分别在不同沙箱里跑测试和自动修复。

你不需要每条线都盯着。
系统只在冲突、越权、预算超限、测试多轮失败、高风险文件被碰到时找你。
```

所以这版路线图新增一条长期主线：

```txt
单 active task
→ 多任务队列
→ 多 run 并发
→ 文件锁与项目隔离
→ 自升级后台通道
→ 多项目并线自动交付
```

### 0.2 本次新增的 Token 成本目标

你补充的新问题是：**当前 A2A 系统有没有节省 Token 的机制？如果没有，就要把它放进迭代 PRD。**

根据当前 PRD，AgentMesh 现在已经有一些“成本意识”的雏形：

- Runtime 有 `model list / policy / recommend`、`model-overrides.md`、CLI `--model` 等模型策略能力。
- Orchestrator 可以按 CLI / 环境变量 / `agents-model.config.ts` 配置不同 Agent 的模型。
- Console 有 Token 估算，但目前只是 `chars/3.5` 这种数量级参考。
- Roadmap 里提到过“成本估算”，但还没有形成系统级 Token 节省机制。

所以结论是：

> **当前 AgentMesh 有模型选择和 Token 估算的基础能力，但还没有真正的 Token 节省系统。未来如果要做全自动、多任务并线、自升级，这个能力必须进入 P0/P1 迭代。**

因为一旦系统进入自动编程阶段，Token 成本会从“小问题”变成“核心运行成本”：

```txt
单任务手动复制 Prompt：成本可控，因为人会停下来。
多 Agent 自动执行：成本开始放大。
多任务并线执行：成本成倍放大。
自动修复循环：成本可能失控。
AgentMesh 自升级 + 客户项目并行：必须有预算和节流机制。
```

因此这版 PRD 新增一条长期主线：

```txt
Token 估算
→ Token 记账
→ 上下文裁剪
→ Prompt 压缩
→ 模型成本路由
→ 预算门禁
→ 多任务 Token 调度
→ 成本可控的全自动编程
```

---

## 1. 产品北极星

### 1.1 一句话定位

**AgentMesh 是一个面向开发者和团队的 A2A 自动编程系统：用户给出目标，多个 Agent 自动拆解需求、设计架构、编写代码、运行测试、修复错误，并在风险可控时自动交付。**

### 1.2 最终用户体验

未来理想状态不是用户复制 Prompt，而是：

```txt
用户输入：我要做一个 SaaS 后台，包含登录、用户管理、账单页、数据看板。
↓
PM Agent 自动澄清和生成 PRD
↓
Architect Agent 自动设计目录、路由、组件、数据流、接口方案
↓
Policy Engine 判断：低风险范围自动放行，高风险范围暂停
↓
Developer Agent 自动生成代码
↓
QA Agent 自动运行 build/lint/test/e2e
↓
Fix Agent 自动修复失败
↓
Security Agent 自动检查越权、危险文件、密钥、依赖风险
↓
Delivery Agent 生成交付报告、diff、运行说明
↓
用户只看结果，必要时处理异常
```

### 1.3 不变的底层原则

即使未来全自动写代码，也不等于完全失控。AgentMesh 要坚持：

- **自动执行，但不越权。**
- **自动写代码，但必须在允许目录和允许任务范围内。**
- **自动修复，但必须有次数上限。**
- **自动交付，但必须有测试、diff、日志和回滚点。**
- **低风险自动放行，高风险才找人。**

---

## 2. 自动化等级：从 L0 到 L5

| 等级 | 名称 | 人工参与 | 系统能力 | 你的目标 |
|---|---|---:|---|---|
| L0 | 纯手动 Prompt | 很高 | 人复制粘贴，多模型手工协作 | 你过去的方式 |
| L1 | 任务包 + 门禁 | 高 | Runtime 管状态，Console 生成任务包 | 当前 AgentMesh 接近这里 |
| L2 | 半自动编排 | 中高 | Orchestrator 自动跑 Agent，但关键节点人审核 | 短期过渡 |
| L3 | 选择性自动 | 中低 | 低风险自动审批，高风险人工审批 | 第一个商业可用版本 |
| L4 | 自动编程闭环 | 低 | 自动写代码、测试、修复、交付；失败才找人 | 核心目标 |
| L5 | 多 Agent 自治工程团队 | 很低 | 多模型竞争、自动评审、自动回滚、自升级 | 长期愿景 |

**建议目标：先做到 L3，再冲 L4。不要从 L1 直接跳 L5。**

### 2.1 横向并发等级：从单任务到多项目并线

自动化等级 L0-L5 解决的是“一个任务能不能越来越自动”。还需要一条并发等级 S0-S5，解决“系统能不能同时做很多事”。

| 并发等级 | 名称 | 系统状态 | 目标 |
|---|---|---|---|
| S0 | 单任务手动 | 只能盯一个任务 | 当前早期心智 |
| S1 | 多任务列表 | 能创建多个任务，但一次主要处理一个 | Console 任务管理 |
| S2 | 多 Run 队列 | 多任务可排队，Runner 一个个执行 | 减少手工切换 |
| S3 | 多 Run 并发 | 多个低风险任务可同时执行 | 并线开发 MVP |
| S4 | 多项目并线 | 不同项目 root 独立执行，互不污染 | 做客户项目 + 自己项目 |
| S5 | 自升级后台通道 | AgentMesh 自己升级自己，同时继续服务其他项目 | 长期目标 |

建议目标：**先做到 L3 + S3，再冲 L4 + S4，最后做 L5 + S5。**


---

## 3. 当前现状与目标差距

根据当前 PRD，AgentMesh 现在的核心能力是本地 Markdown 文件驱动的多 Agent 协作与工作流门禁系统。Python Runtime 负责状态机、门禁、Prompt 文案生成，不直接调 LLM，也不直接写业务源码；Console 普通模式主要生成任务包，不写真实业务源码。

这说明当前系统有很好的“安全地基”，但离“全自动编写代码”还差几块关键能力。

### 3.1 并线开发的现状差距

当前系统已经支持每个任务独占 `.ai-agents/workspace/<task-id>/` 目录，这是并线开发的基础；但它仍然存在 `active-task.md` 这种“当前活跃任务”的单任务心智。未来要把它从“一个 active task”升级为“多个 active tasks / run sessions / project lanes”。

| 当前单任务心智 | 未来并线心智 |
|---|---|
| active-task.md 指向一个当前任务 | task-pool 管理多个可运行任务 |
| 用户手动切换任务 | Scheduler 自动选择下一个可跑任务 |
| 一个 Orchestrator 跑一条线 | 多 Runner 并发跑多条线 |
| 一个项目 root | Project Registry 管多个项目 root |
| 人判断冲突 | Lock Manager 自动判断文件/项目冲突 |
| 自升级会占用全部注意力 | Self-Upgrade Lane 后台运行，候选版本通过 canary 后再切换 |


| 当前能力 | 当前状态 | 要升级成什么 |
|---|---|---|
| Runtime | 状态机 + 门禁 + Prompt 生成 | 继续保持纯净，不直接变成大脑 |
| Orchestrator | 可选调用 Cursor SDK | 升级为统一 Runner Adapter |
| Console | 任务包生成 + 可视化查看 | 升级为自动执行控制台 |
| Human Review | 人工双步审批 | 升级为 Policy Gate 自动审批 |
| Developer Gate | 检查能不能写 | 升级为自动白名单 + diff 风险分析 |
| QA | 人工或 Agent 产物 | 升级为自动 build/lint/test/e2e |
| 失败恢复 | 依赖人处理 | 升级为自动修复循环 + 快照回滚 |
| 生成项目 | 当前不写真实项目源码 | 升级为沙箱内自动生成项目 |
| Token 成本治理 | 当前只有估算和模型选择雏形 | 升级为 Token Economy Engine |

---

## 4. 最大的产品转向：从 Human Gate 到 Policy Gate

你原先认为“人工审核”是保证安全的核心。现在需要升级认知：

> **未来真正的核心不是 Human Review，而是 Policy Review。**

也就是让系统内置规则判断：

- 这个任务是不是低风险？
- 改动是不是在允许目录？
- 有没有碰 `.env`、`.github`、CI/CD、密钥、生产配置？
- 有没有引入危险依赖？
- 有没有删除重要文件？
- 测试是否通过？
- diff 是否符合任务目标？
- 修复次数是否超限？

当系统能回答这些问题，就可以把大量人工审核变成自动审核。

### 4.1 审核策略进化

```txt
阶段 1：所有关键节点都人工审核
阶段 2：低风险任务自动审核，关键文件人工审核
阶段 3：低/中风险任务自动审核，高风险人工审核
阶段 4：默认自动审核，只有异常、越权、失败才找人
阶段 5：系统自动提出策略调整，人只批准策略本身
```

### 4.2 人工审核不消失，而是变成异常处理

未来仍然应该保留人工暂停点，但它不应该阻塞所有任务。

必须人工的情况：

- 改认证、支付、权限、数据库迁移、生产配置。
- 修改 CI/CD、部署脚本、密钥、环境变量。
- 删除大量文件或重构核心架构。
- 自动测试多次失败仍无法修复。
- Agent 之间评审结果冲突严重。
- 成本超过预算。
- 系统无法判断风险等级。

其它低风险代码任务，应该允许自动完成。

---

## 5. 未来目标架构

```txt
┌──────────────────────────────────────────────────────────────┐
│                       用户目标 / 业务需求                     │
└───────────────────────────────┬──────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────┐
│ PM Agent：澄清需求、PRD、任务拆解、验收标准                   │
└───────────────────────────────┬──────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────┐
│ Architect Agent：技术方案、目录计划、file-change-plan         │
└───────────────────────────────┬──────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────┐
│ Policy Engine：风险评分、自动审批、强制暂停规则               │
└───────────────────────────────┬──────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────┐
│ Sandbox Workspace：隔离写代码，不直接污染真实项目             │
└───────────────────────────────┬──────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────┐
│ Developer Agent：自动写代码 / 修改代码                       │
└───────────────────────────────┬──────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────┐
│ QA + Test Runner：build / lint / unit / e2e / typecheck       │
└───────────────────────────────┬──────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────┐
│ Fix Agent：根据失败日志自动修复，最多 N 轮                    │
└───────────────────────────────┬──────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────┐
│ Reviewer Agent：检查 diff、越权、需求覆盖、风险               │
└───────────────────────────────┬──────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────┐
│ Delivery Agent：生成交付报告、运行说明、回滚点、最终产物       │
└──────────────────────────────────────────────────────────────┘
```

并线版本要在 Policy Engine 和 Sandbox 之外，再增加三层：

```txt
Project Registry：登记多个项目 root，例如 AgentMesh 自身、客户项目 A、客户项目 B
Task Pool：保存所有待执行、执行中、暂停、完成、失败的任务
Scheduler + Lock Manager：决定哪些任务可以同时跑，哪些任务必须等待
```

---

## 6. 核心模块拆解

### 6.1 Runtime：继续做“法官”，不要做“写手”

Runtime 不建议直接接 LLM，也不建议直接写业务代码。Runtime 应该继续负责：

- 状态机。
- 门禁。
- 风险判断。
- 策略执行。
- 产物校验。
- 最终交付检查。

这样它才能成为可信底座。

### 6.2 Runner Adapter：接不同模型和工具

新增一层 Runner Adapter，用来统一调用不同执行器：

```txt
Cursor SDK Runner
Codex Runner
Claude Code Runner
OpenAI Runner
Local Shell Runner
Future MCP Tool Runner
```

Console 不应该直接调用 Cursor SDK。它应该调用统一的 Runner API，由 Runner Adapter 决定用哪个工具执行。

### 6.3 Policy Engine：自动审批大脑

Policy Engine 是减少人工审核的关键。

它要输入：

- 任务类型。
- 目标目录。
- file-change-plan。
- diff。
- 风险等级。
- 测试结果。
- 模型置信度。
- 历史失败记录。

它要输出：

```txt
AUTO_APPROVE
AUTO_REJECT
NEED_HUMAN_REVIEW
NEED_MORE_TESTS
NEED_FIX_LOOP
```

### 6.4 Sandbox Workspace：安全写代码

自动写代码不能直接在主项目乱改。建议使用隔离目录：

```txt
.agentmesh/runs/<run-id>/workspace-copy/
.agentmesh/runs/<run-id>/patches/
.agentmesh/runs/<run-id>/logs/
.agentmesh/runs/<run-id>/test-results/
```

生成或修改完成后，再把 patch 合并到真实项目。

### 6.5 Test Runner：自动化质量闸门

没有测试，自动写代码就是盲飞。最少要支持：

- `npm install` 或依赖检查。
- `npm run build`。
- `npm run lint`。
- `npm run typecheck`。
- `npm test`。
- 可选：Playwright e2e。

### 6.6 Auto Fix Loop：自动修复循环

典型逻辑：

```txt
运行测试
↓
失败
↓
把失败日志交给 Fix Agent
↓
Fix Agent 修改代码
↓
再次运行测试
↓
最多 3 轮
↓
成功则交付，失败则进入人工异常处理
```

建议默认最多 3 轮，不要无限循环。


### 6.7 Multi-Task Scheduler：多任务并线调度器

这是新增的核心模块。它负责决定“现在谁可以跑，谁必须等”。

它要管理：

- task queue：等待执行的任务。
- run pool：正在执行的 run。
- project lanes：每个项目自己的执行通道。
- priority：优先级，例如客户项目高于自升级，紧急 bug 高于新功能。
- resource budget：模型调用、Token、并发数、修复次数。
- dependency：任务之间是否有前后依赖。
- lock：文件锁、目录锁、项目锁、全局锁。

建议配置：

```yaml
scheduler:
  max_parallel_runs: 3
  max_parallel_per_project: 2
  max_parallel_self_upgrade_runs: 1
  default_priority: normal
  allow_background_self_upgrade: true
  pause_self_upgrade_when_user_project_is_high_risk: true
  require_version_pin_for_running_tasks: true
```

调度规则示例：

```txt
普通页面生成任务：可以和其它低风险任务并发。
同一项目同一文件修改：不能并发，必须排队。
package.json / 构建配置 / 权限 / 支付 / 认证：加项目级独占锁。
AgentMesh 自升级：只能在 self-upgrade lane 运行，不能污染正在服务其它项目的 runtime。
```

### 6.8 Lock Manager：文件锁、目录锁、项目锁

并线开发最大的风险是两个 Agent 同时改同一个文件，或者一个 Agent 在升级系统本体时另一个任务正依赖旧版本 Runtime。

建议设计三种锁：

| 锁类型 | 作用 | 示例 |
|---|---|---|
| file lock | 防止两个任务同时改同一文件 | `src/pages/Dashboard.tsx` |
| directory lock | 防止同一模块被并发大改 | `src/auth/**` |
| project lock | 高风险变更时锁住整个项目 | `package.json`、构建配置、认证系统 |
| runtime version lock | 运行中的任务固定使用某个 Runtime 版本 | 自升级期间不影响老任务 |

文件锁必须来自 Architect 的 file-change-plan。Developer Agent 开始写代码前，Scheduler 要先申请锁。拿不到锁，就进入 queued/waiting_for_lock，而不是强行执行。

### 6.9 Project Registry：多项目根目录管理

要满足“自升级的同时做别的项目”，AgentMesh 需要知道自己正在服务哪些项目。

建议新增：

```txt
.agentmesh/projects/registry.json
.agentmesh/projects/<project-id>/config.yaml
.agentmesh/projects/<project-id>/tasks/
.agentmesh/projects/<project-id>/runs/
```

每个项目至少记录：

```yaml
project_id: agentmesh-core
project_name: AgentMesh 自身
project_root: /path/to/AgentMesh
project_type: self_upgrade | client_project | generated_project | maintenance
automation_mode: selective_auto
max_parallel_runs: 1
allowed_paths:
  - apps/a2a-console/**
  - a2a_runtime/**
blocked_paths:
  - .env
  - .github/**
  - secrets/**
```

这样 Console 可以从“一个项目驾驶舱”升级为“多项目控制台”。

### 6.10 Self-Upgrade Lane：自升级后台通道

AgentMesh 自升级不能和普通项目开发混在一起。建议为自升级单独建立 lane：

```txt
self_upgrade_lane
├── candidate workspace：候选版本代码
├── regression tests：回归测试
├── canary tasks：金丝雀任务
├── compatibility check：旧任务兼容检查
└── promote / rollback：升级或回滚
```

关键原则：

- 自升级永远先在候选沙箱里跑。
- 正在执行的用户项目必须 pin 到当前稳定 Runtime 版本。
- 候选版本必须通过回归测试和 canary 任务，才能成为默认版本。
- 如果用户项目处于高风险任务执行中，自升级可以继续写候选版本，但不能替换生产执行器。
- 自升级失败不能影响客户项目或其它项目。

### 6.11 Context Isolation：上下文隔离

并线时，每条任务线必须只看到自己该看的项目、任务、文件和日志。

必须避免：

- AgentMesh 自升级任务误读客户项目需求。
- 客户项目 A 的 Agent 修改客户项目 B 的文件。
- 多个任务的 Prompt、日志、diff 混在一起。
- 一个任务的失败日志污染另一个任务的 Fix Agent。

每个 Run 的 Prompt 都应该包含明确的上下文边界：

```txt
你只能处理 project_id = client-a 的 task_id = T-2026-001。
你只能读取本 run workspace 和被授权的 project_root 文件。
你不能访问其它 project_id、其它 task_id 的 artifacts。
你不能修改未被 file-change-plan 授权的路径。
```


### 6.12 Token Economy Engine：Token 节省与预算控制系统

这是新增的核心模块。它的目标不是“少用模型”，而是：**让系统在不明显牺牲质量的前提下，自动减少无效 Token、控制预算、避免自动化失控烧钱。**

它应该放在 Runner Adapter / Orchestrator / Console 层，而不是塞进 Runtime 核心。原因是当前 Runtime 的优势是“本地可信法官”：它不直接调 LLM，只负责状态机、门禁、Prompt 文案和授权判断。Token 统计、上下文裁剪、模型路由，属于执行层和观测层。

#### 6.12.1 当前已有的弱能力

| 已有能力 | 当前价值 | 局限 |
|---|---|---|
| 模型策略 / 推荐 | 可以给不同 Agent 选择不同模型 | 还不是按成本、质量、风险自动路由 |
| 模型 override | 用户可以手动指定模型 | 依赖人工配置，不能自动节流 |
| Console Token 估算 | 能看到大概 Token 量 | `chars/3.5` 只是粗估，不等于真实消耗 |
| 大文件截断预览 | Console 不一次性展示超大文件 | 不等于 Runner Prompt 不会带入过多上下文 |
| Roadmap 成本估算 | 已有产品意识 | 还没有预算门禁、Token 账本、自动优化 |

#### 6.12.2 必须新增的 8 个能力

| 能力 | 说明 | 优先级 |
|---|---|---|
| Token Ledger | 记录每个 project / task / run / agent 的输入、输出、模型、费用 | P0 |
| Token Budget Gate | 超过预算时暂停、降级模型、压缩上下文或请求用户放行 | P0 |
| Context Pack Builder | 每次只给 Agent 当前阶段真正需要的上下文 | P0 |
| Artifact Summarizer | 对长 PRD、长日志、长 diff 生成摘要，避免反复塞全文 | P1 |
| Prompt Cache | 对重复的系统 Prompt、Agent 角色 Prompt、项目摘要做缓存复用 | P1 |
| Model Cost Router | 低风险用便宜模型，高风险/复杂任务才用强模型 | P1 |
| Auto Fix Cost Guard | 自动修复循环每轮都记账，超过成本或轮数上限立刻停止 | P0 |
| Cost Dashboard | Console 展示本日、本项目、本任务、本 Agent 成本 | P2 |

#### 6.12.3 推荐配置

```yaml
token_economy:
  enabled: true
  mode: balanced # conservative | balanced | aggressive

  default_budgets:
    max_input_tokens_per_run: 80000
    max_output_tokens_per_run: 20000
    max_cost_usd_per_run: 2.0
    max_cost_usd_per_task: 8.0
    max_cost_usd_per_project_per_day: 30.0

  per_agent_budget:
    pm:
      model_tier: cheap
      max_input_tokens: 12000
      max_output_tokens: 4000
    architect:
      model_tier: strong
      max_input_tokens: 24000
      max_output_tokens: 8000
    developer:
      model_tier: balanced
      max_input_tokens: 32000
      max_output_tokens: 12000
    qa:
      model_tier: cheap
      max_input_tokens: 16000
      max_output_tokens: 6000
    fix:
      model_tier: balanced
      max_attempts: 3
      max_cost_usd_total: 3.0

  context_policy:
    include_full_history: false
    include_full_files_by_default: false
    prefer_artifact_summaries: true
    max_files_per_prompt: 20
    max_diff_chars: 30000
    max_log_chars: 20000
    require_reason_for_full_file_context: true

  parallel_budget:
    max_parallel_token_burn_rate: medium
    pause_background_self_upgrade_when_budget_low: true
    reserve_budget_for_user_projects: true
```

#### 6.12.4 Context Pack Builder 的原则

每个 Agent 不应该默认拿到所有历史文件。应该按阶段生成最小上下文包：

```txt
PM Agent：用户需求 + 业务背景 + 产品约束，不需要源码全文。
Architect Agent：需求 + 项目结构摘要 + 关键文件目录，不需要全部实现细节。
Developer Agent：file-change-plan + 被授权文件 + 相关接口/组件摘要，不需要完整聊天历史。
QA Agent：验收标准 + diff + 测试日志 + 关键风险，不需要 PM 全文。
Fix Agent：失败日志 + 相关文件 + 上一轮修改 diff，不需要重新看所有项目上下文。
Security Agent：diff + 敏感路径规则 + 依赖变化，不需要所有业务文案。
```

这会显著减少“每一轮都把所有内容再发一遍”的浪费。

#### 6.12.5 Token Ledger 数据结构

建议新增：

```txt
.agentmesh/usage/token-ledger.jsonl
.agentmesh/usage/daily-summary.json
.agentmesh/projects/<project-id>/usage/token-ledger.jsonl
.ai-agents/workspace/<task-id>/runs/<run-id>/usage.json
```

每条记录至少包含：

```json
{
  "project_id": "client-a",
  "task_id": "T-2026-001",
  "run_id": "R-2026-001",
  "agent": "developer",
  "model": "balanced-model-name",
  "input_tokens_estimated": 18000,
  "output_tokens_estimated": 6000,
  "input_tokens_actual": 17250,
  "output_tokens_actual": 5400,
  "cost_usd_estimated": 0.85,
  "cost_usd_actual": 0.78,
  "context_pack_id": "ctx-dev-001",
  "optimization_applied": ["summary", "file_slice", "cheap_model"],
  "created_at": "2026-05-17T00:00:00Z"
}
```

#### 6.12.6 预算门禁规则

```txt
如果 run 预计成本超过预算：先尝试压缩上下文。
如果压缩后仍超预算：尝试降低模型档位。
如果任务是高风险：不允许为了省钱降低到弱模型。
如果自动修复超过 3 轮或预算：停止并生成失败报告。
如果 self-upgrade lane 消耗过高：暂停后台自升级，优先保留用户项目预算。
如果多个并线任务同时烧 Token：Scheduler 限流，低优先级任务排队。
```

#### 6.12.7 验收标准

| 验收项 | 标准 |
|---|---|
| 每个 run 有 Token 记录 | input/output、模型、Agent、任务、项目都能追踪 |
| 每次执行前有预算预估 | Console 展示预计成本和剩余额度 |
| 超预算自动处理 | 压缩上下文、降级模型、暂停或请求放行 |
| 不再默认带全量历史 | 每个 Agent 使用 context pack，而不是全文堆叠 |
| 自动修复不烧穿预算 | max_attempts 和 max_cost 双限制 |
| 多任务预算隔离 | 自升级不能抢光客户项目预算 |
| 成本报告可读 | 用户能看到“钱花在哪个 Agent / 哪个任务 / 哪个模型” |


---

## 7. 自动化模式设计

建议在配置里加入：

```yaml
automation_mode: manual | assisted | selective_auto | full_auto
risk_budget: low | medium | high
max_fix_attempts: 3
allow_auto_code_write: true
allow_auto_dependency_install: false
allow_auto_git_commit: false
allow_auto_merge_to_project: false
require_tests_before_delivery: true

multi_task:
  enabled: true
  max_parallel_runs: 3
  max_parallel_per_project: 2
  allow_self_upgrade_in_background: true
  self_upgrade_priority: background
  conflict_policy: wait_for_lock
  context_isolation: strict
```

### 7.1 四种模式

| 模式 | 适合阶段 | 行为 |
|---|---|---|
| manual | 当前用户习惯 | 复制 Prompt，人审每一步 |
| assisted | 过渡期 | Agent 自动跑，但关键节点人审 |
| selective_auto | 第一个商业版本 | 低风险自动写，风险任务暂停 |
| full_auto | 长期目标 | 自动规划、写代码、测试、修复、交付 |

### 7.2 默认建议

开发早期默认 `assisted`，内部测试稳定后默认 `selective_auto`，不要一开始默认 `full_auto`。

### 7.3 并线模式设计

建议新增 `concurrency_mode`：

```yaml
concurrency_mode: single_task | queued | parallel_safe | parallel_projects | background_self_upgrade
```

| 模式 | 适合阶段 | 行为 |
|---|---|---|
| single_task | 当前默认 | 一次主要跑一个任务 |
| queued | 早期升级 | 多任务排队，Runner 按顺序执行 |
| parallel_safe | 并线 MVP | 低风险、不冲突任务可以并发 |
| parallel_projects | 多项目阶段 | 不同 project root 可以并线执行 |
| background_self_upgrade | 长期目标 | AgentMesh 自升级在后台候选 lane 运行 |

默认建议：先做 `queued`，再做 `parallel_safe`，最后做 `parallel_projects` 和 `background_self_upgrade`。


---

## 8. 风险分级与自动放行规则

### 8.1 可自动放行的低风险任务

适合自动执行：

- 新增普通页面。
- 新增组件。
- 修改样式。
- 增加 mock 数据。
- 新增路由页面。
- 修改文案。
- 补充单元测试。
- 修复简单类型错误。
- 根据现有模板生成项目骨架。

### 8.2 需要谨慎的中风险任务

可以在策略允许下自动执行，但要更严格测试：

- 修改状态管理。
- 修改接口请求封装。
- 改表单校验。
- 新增依赖。
- 重构组件结构。
- 调整构建配置。

### 8.3 必须人工处理的高风险任务

默认暂停：

- 登录、认证、权限。
- 支付、账单、订单。
- 数据库迁移。
- 生产环境配置。
- `.env`、密钥、token。
- `.github`、CI/CD、部署脚本。
- 删除大量文件。
- 跨项目大重构。
- 安装不可信依赖。

未来即便要全自动，也建议先让这些高风险项保留人工异常处理。

### 8.4 并线开发的风险规则

多任务并线时，是否自动执行不仅看任务风险，还要看冲突风险。

可以并发的情况：

- 不同项目 root。
- 同一项目但修改完全不同目录。
- 只读分析任务。
- QA/Test Runner 只读取代码，不写业务文件。
- 自升级候选版本只在 sandbox 中运行。

必须排队或暂停的情况：

- 两个任务要改同一个文件。
- 两个任务都要改 `package.json`、路由总表、状态管理核心文件。
- 一个任务正在改测试框架，另一个任务依赖测试结果。
- 自升级任务要替换 Runner / Policy / Runtime，而此时有用户项目正在执行。
- 任一任务触发项目级高风险锁。


### 8.5 Token 成本风险规则

Token 成本本身也要进入风险分级。未来 AgentMesh 不应该只判断“能不能改代码”，还要判断“这次自动执行值不值得花这么多 Token”。

| 成本风险 | 触发条件 | 系统动作 |
|---|---|---|
| 低成本 | 小任务、少量文件、单轮执行 | 自动放行 |
| 中成本 | 多 Agent、多文件、多轮执行 | 先预算预估，再执行 |
| 高成本 | 大上下文、自动修复多轮、并线任务很多 | 启用压缩、限流、模型路由 |
| 超预算 | 超过 task / project / day 限额 | 暂停并请求用户确认 |

必须注意：**不能为了省 Token 牺牲安全。** 例如认证、支付、权限、数据库迁移、生产配置等高风险任务，即使成本高，也不能简单降级到弱模型；应该优先缩小任务范围和上下文，而不是牺牲判断质量。


---

## 9. 六个月路线图

### Phase 0：把产品叙事改成“减少人工审核”

**时间：第 1 周**  
**目标：明确 AgentMesh 不只是人工门禁，而是自动编程系统的安全底座。**

P0 任务：

- 修改 README / PRODUCT / Console 文案。
- 把“Human Review 是终点”的表述改成“Human Review 是冷启动安全网”。
- 增加自动化等级 L0-L5。
- 增加 `automation_mode` 概念。
- 明确长期目标：全自动编写代码。

验收标准：

- 新用户能明白：当前是半自动，未来要做全自动。
- 文档不再让人误解为永远人工审批。

---

### Phase 1：Runner Adapter + Run Session

**时间：第 2–4 周**  
**目标：减少复制粘贴，让系统能自动调用 Agent。**

P0 任务：

- 新增 Run Session 模型。
- 新增 Runner Adapter 接口。
- 把 Cursor SDK Orchestrator 包装成一个 Runner。
- Console 增加“开始执行 / 暂停 / 继续 / 取消”。
- 运行日志事件化。

验收标准：

- 用户不需要手动复制 PM / Architect Prompt。
- 一个任务可以被自动推进到 `human_review_required`。
- 每次执行都有 run-id、日志、状态、失败原因。


### Phase 1.5：Task Pool + 多任务队列

**时间：第 4–6 周，可与 Phase 2 部分并行**  
**目标：让 AgentMesh 从单 active task 升级为多任务队列，为并线开发打基础。**

P0 任务：

- 新增 Task Pool 概念。
- 新增 Run Pool 概念。
- Console 展示 queued / running / paused / failed / completed。
- 将 `active-task.md` 的产品心智从“唯一当前任务”降级为“当前查看任务”。
- 支持多个任务同时处于可运行状态。
- 支持任务优先级：urgent / high / normal / background。
- 新增 run-level 日志，避免多任务日志混在一起。

验收标准：

- Console 能同时看到多个任务的执行状态。
- 用户可以让一个任务暂停，同时启动另一个任务。
- 一个任务失败不会阻塞其它任务继续执行。
- 自升级任务可以被标记为 background，不抢占用户项目。

---

### Phase 1.6：Lock Manager + 冲突检测

**时间：第 6–8 周**  
**目标：让多个任务可以安全并发，而不是盲目并发。**

P0 任务：

- 从 file-change-plan 解析目标文件。
- 新增 file lock / directory lock / project lock。
- 申请锁失败时进入 waiting_for_lock。
- Console 显示“为什么这个任务在等”。
- 高风险文件自动触发 project lock。

验收标准：

- 两个任务不能同时修改同一文件。
- 不同目录的低风险任务可以并发。
- Scheduler 能解释每个任务是 running、queued 还是 waiting_for_lock。
- 锁释放后，队列任务能自动继续。

---

### Phase 1.7：Project Registry + 多项目并线

**时间：第 8–10 周**  
**目标：支持 AgentMesh 自升级的同时，继续做其它项目。**

P0 任务：

- 新增 Project Registry。
- 每个项目有独立 config、workspace、runs、logs、artifacts。
- Console 支持项目切换。
- Scheduler 支持 max_parallel_per_project。
- 自升级项目 `agentmesh-core` 固定走 self-upgrade lane。
- 运行中的任务 pin Runtime 版本，避免自升级影响旧 run。

验收标准：

- AgentMesh 可以后台跑自升级候选任务。
- 同时可以在另一个 project root 生成或修改客户项目。
- 两个项目的日志、diff、测试报告互不污染。
- 自升级失败不会影响其它项目 run。

---


### Phase 1.8：Token Telemetry + Budget Gate

**时间：第 8–10 周，可与多任务并线一起做**  
**目标：先看见 Token，再控制 Token。**

P0 任务：

- 新增 Token Ledger，记录 project / task / run / agent / model 的 Token 和成本。
- Console 在 Run 详情里展示预计 Token、实际 Token、预计成本、实际成本。
- 新增 budget config：按 run、task、project、day 设置预算。
- 自动修复循环接入成本上限。
- Self-Upgrade Lane 使用后台预算，不能抢占用户项目预算。

验收标准：

- 任意一次 Runner 调用都能追踪 Token 和模型。
- 超过预算时，系统不会继续静默执行。
- 用户能看懂钱花在哪个 Agent 和哪个任务上。
- 并线任务不会互相抢预算。

---

### Phase 2.5：Context Pack Builder + Prompt 压缩

**时间：第 12–16 周**  
**目标：从“看见成本”升级为“主动节省成本”。**

P0/P1 任务：

- 每个 Agent 阶段生成 context pack。
- 默认不向 Agent 传全量历史。
- 长 PRD、长日志、长 diff 先摘要，再按需展开。
- Runner 调用前显示“本次上下文由哪些文件/摘要组成”。
- 对重复角色 Prompt、项目摘要、测试摘要做缓存。

验收标准：

- 同类任务的平均输入 Token 明显下降。
- Agent 输出质量不明显下降。
- 用户可以追溯“为什么这次只给了这些上下文”。
- 高风险任务仍可申请 full context，但必须给出理由并记录成本。

---

### Phase 2：Policy Engine 替代一部分人工审核

**时间：第 5–8 周**  
**目标：低风险任务自动放行。**

P0 任务：

- 新增风险评分规则。
- 新增自动审批策略。
- 新增 blocked paths / allowed paths 配置。
- file-change-plan 低风险自动 approve。
- 高风险自动暂停。
- Console 显示“为什么自动放行 / 为什么暂停”。

验收标准：

- 新增普通页面、组件、样式类任务可自动进入 Developer 阶段。
- 涉及认证、支付、CI/CD、密钥的任务会自动暂停。
- 低风险自动放行准确率达到 80% 以上。

---

### Phase 3：Sandbox 自动写代码 MVP

**时间：第 9–12 周**  
**目标：系统能在沙箱里自动写代码。**

P0 任务：

- 新增 Sandbox Workspace。
- Developer Agent 在沙箱内写代码。
- 生成 patch，而不是直接污染真实项目。
- 增加 diff 展示。
- 增加一键应用 patch。
- 支持 `apps/generated-projects/<task-id>/` 自动生成项目。

验收标准：

- 输入一个 Todo / Dashboard / CRM Mini App 需求，系统能自动生成项目目录。
- 生成项目能运行 `npm run build`。
- 所有修改都有 diff。
- 越权路径写入次数为 0。

---

### Phase 4：Test Runner + Auto Fix Loop

**时间：第 13–16 周**  
**目标：自动写代码后能自动验证和修复。**

P0 任务：

- 自动运行 build/lint/typecheck/test 命令。
- 捕获失败日志。
- Fix Agent 根据失败日志修复。
- 最多 3 轮修复。
- 失败后自动进入异常处理。
- 生成测试报告和修复记录。

验收标准：

- 生成项目 build 通过率达到 85% 以上。
- 简单错误可自动修复。
- 修复循环不会无限运行。
- 用户能看到每一轮失败和修复原因。

---

### Phase 5：Full Auto Project Generation Beta

**时间：第 17–24 周**  
**目标：实现“从需求到可运行项目”的自动闭环。**

P0 任务：

- Console 支持 Full Auto 创建任务。
- PM → Architect → Policy → Developer → QA → Fix → Delivery 自动串联。
- 支持模板选择：Vite / Next.js / Admin / Landing Page。
- 支持自动生成 final-delivery。
- 支持导出项目。
- 支持失败回滚。

验收标准：

- 用户只输入需求，系统自动产出可运行项目。
- 人工介入次数低于 1 次 / 低风险任务。
- 生成项目可构建、可预览、有交付报告。
- 失败任务能自动说明原因。

---

### Phase 6：AgentMesh 自升级闭环

**时间：第 6–12 个月**  
**目标：让 AgentMesh 用自己的流程升级自己。**

P0 任务：

- 使用 AgentMesh 管理 AgentMesh 自身迭代。
- 每次自升级必须生成 PRD、方案、diff、测试报告、交付报告。
- 引入回归测试集。
- 引入 canary 任务。
- 引入版本回滚。

验收标准：

- Codex/Cursor 可以根据本任务包升级 AgentMesh。
- 升级后测试必须通过。
- 文档和代码保持一致。
- 每次版本变化都有可追溯记录。

---

## 10. 给 Codex / Cursor 的总任务 Prompt

你可以把下面这段直接复制给 Codex 或 Cursor。

```txt
你是 AgentMesh 项目的资深产品工程师 + 架构师。

项目目标：
把 AgentMesh 从“人工审核为主的多 Agent 门禁系统”，升级为“策略驱动、可自动写代码、自动测试、自动修复、自动交付的 A2A 自动编程系统”。

重要原则：
1. 不要把 Python Runtime 变成直接调用 LLM 和直接写代码的模块。
2. Runtime 继续负责状态机、门禁、风险、策略、交付校验。
3. 新增 Runner Adapter 层，用于统一 Cursor SDK / Codex / 未来模型执行器。
4. 新增 Policy Engine，用策略替代一部分人工审核。
5. 新增 Sandbox Workspace，让 AI 在隔离环境写代码并生成 patch。
6. 新增 Test Runner 和 Auto Fix Loop，代码必须经过 build/lint/typecheck/test 命令。
7. 高风险任务必须暂停；低风险任务可以自动放行。
8. 所有变更必须有 diff、日志、测试结果、交付报告。
9. 不要一次性做完全部功能；按 Phase 0 到 Phase 5 分阶段实现。

10. 新增 Multi-Task Scheduler、Task Pool、Run Pool，让系统支持多任务排队和安全并发。
11. 新增 Lock Manager，避免多个 Agent 同时修改同一文件、同一目录或同一项目关键配置。
12. 新增 Project Registry，让 AgentMesh 可以同时服务多个 project root。
13. 新增 Self-Upgrade Lane，让 AgentMesh 自升级在后台候选沙箱运行，不阻塞客户项目或其它项目。
14. 运行中的任务必须 pin 当前 Runtime / Policy / Runner 版本，自升级候选版本通过回归测试和 canary 后才能提升为默认版本。
15. 新增 Token Economy Engine：Token Ledger、Budget Gate、Context Pack Builder、Prompt 压缩、模型成本路由、Cost Dashboard。
16. 所有 Runner 调用必须记录 Token 和成本；超预算时必须压缩上下文、降级非关键模型、暂停或请求用户放行。

当前优先实现：
Phase 0：更新文档叙事，加入 automation_mode 和 L0-L5 自动化等级。
Phase 1：实现 Run Session + Runner Adapter，减少手动复制 Prompt。
Phase 1.5：实现 Task Pool / Run Pool，让多个任务可以排队和并线。
Phase 1.6：实现 Lock Manager，解决并发冲突。
Phase 1.7：实现 Project Registry / Self-Upgrade Lane，让自升级不阻塞其它项目。
Phase 1.8：实现 Token Telemetry / Budget Gate，让系统先看见成本、再限制成本。
Phase 2：实现 Policy Engine，让低风险 file-change-plan 自动放行。
Phase 2.5：实现 Context Pack Builder / Prompt 压缩，让系统主动减少无效 Token。

请先阅读现有 PRD、README、Runtime、Console、Orchestrator 代码，然后输出：
- 代码改动计划
- 文件级修改清单
- 风险点
- 分阶段实现方案
- 第一阶段最小可运行 patch
```

---

## 11. 每个 Agent 的职责重定义

### PM Agent

过去：生成 PRD，交给人看。  
未来：自动澄清需求、生成验收标准、判断需求是否足够进入开发。

### Architect Agent

过去：写方案和 file-change-plan，等人审批。  
未来：输出可被 Policy Engine 自动判断的结构化计划。

### Developer Agent

过去：人复制 Prompt 后让它写代码。  
未来：在 Sandbox 中自动写代码，并输出 patch。

### QA Agent

过去：写测试建议。  
未来：调用 Test Runner，分析失败日志，判断是否允许交付。

### Fix Agent

新增角色：根据测试失败日志自动修复代码。

### Reviewer Agent

新增角色：模拟人工审核，检查 diff 是否符合任务目标。

### Security Agent

新增角色：检查密钥、危险文件、依赖、越权路径、潜在安全风险。

### Controller Agent

过去：推动状态。  
未来：根据 Policy Engine 决策自动推进流程。


### Scheduler Agent

新增角色：根据任务优先级、锁、预算、项目状态，决定哪个任务先跑、哪个任务并发、哪个任务等待。

### Project Manager Agent

新增角色：管理多个 project root 的上下文，防止任务跑错项目。

### Upgrade Guardian Agent

新增角色：专门负责 AgentMesh 自升级。它检查候选版本、回归测试、canary 任务和回滚方案，避免自升级影响正在执行的其它项目。


### Cost Guardian Agent

新增角色：专门负责 Token 预算、模型成本、上下文压缩和自动修复成本控制。它不写业务代码，只判断“这次调用是否值得、是否超预算、是否需要压缩上下文或排队”。



---

## 12. 小白知识盲区地图

### 12.1 盲区：全自动不等于无审核

正确理解：审核可以从“人审”变成“机器策略审”。如果没有策略、测试、沙箱、回滚，全自动只是赌博。

### 12.2 盲区：为什么 Runtime 不直接调 LLM？

因为 Runtime 是可信法官。如果它既当法官又当写手，后面很难解释谁在授权、谁在执行、谁在越权。

### 12.3 盲区：为什么要 Sandbox？

自动代码生成一定会出错。Sandbox 可以让错误发生在隔离环境，不污染真实项目。

### 12.4 盲区：为什么要 Test Runner？

自动写代码没有测试，就无法知道是否真的成功。测试是自动化系统的眼睛。

### 12.5 盲区：为什么要 Patch 而不是直接改项目？

Patch 可以被审查、回滚、统计、对比；直接改项目会让问题难以追踪。

### 12.6 盲区：为什么要限制修复次数？

AI 可能陷入循环修复。最多 3 轮能防止成本失控和项目被越改越乱。

### 12.7 盲区：为什么要分 L0-L5？

因为产品不能一下子从手动跳到全自动。分级可以让你知道每个版本到底进步在哪里。

### 12.8 盲区：并线开发不是越多越好

正确理解：并线的目标不是把所有 Agent 一起开到最大，而是让“不冲突的任务同时跑，冲突的任务自动排队”。没有锁、队列、预算和上下文隔离的并发，只会把项目越改越乱。

### 12.9 盲区：自升级不能直接替换正在运行的系统

正确理解：AgentMesh 自升级必须像发布新版本一样，有候选版本、回归测试、canary、版本固定和回滚。正在执行的用户项目应该继续使用稳定版本，不能被半成品升级影响。


### 12.10 盲区：Token 不是小钱问题，而是自动化系统的燃料问题

手动复制 Prompt 时，你本人会天然限制调用次数；全自动以后，系统可能连续调用 PM、Architect、Developer、QA、Fix、Security 多个 Agent。如果没有预算门禁和上下文压缩，自动化越强，成本越容易失控。

### 12.11 盲区：省 Token 不能只靠换便宜模型

真正的节省顺序应该是：先减少无效上下文，再避免重复调用，再做模型路由。不能简单把所有任务都换成便宜模型，否则高风险任务的判断质量会下降。



---

## 13. 跌倒恢复手册

### 情况 A：AI 把代码改乱了

处理：

1. 不要继续让同一个 Agent 修。
2. 回到最近的 Sandbox 快照。
3. 查看 diff 和测试失败日志。
4. 降级到 `assisted` 模式。
5. 让 Architect 重新生成更小的 file-change-plan。

### 情况 B：自动修复循环一直失败

处理：

1. 停止修复循环。
2. 保存失败日志。
3. 把任务拆小。
4. 只允许修改失败相关文件。
5. 重新运行 Test Runner。

### 情况 C：Agent 越权修改文件

处理：

1. 立即拒绝 patch。
2. 标记为 policy violation。
3. 更新 blocked paths。
4. 降低该任务 automation_mode。
5. 要求 Developer Agent 重新生成 file-change-plan。

### 情况 D：文档说能做，代码其实没做

处理：

1. 优先相信代码事实。
2. 在 PRD 里标记“愿景 / 已实现 / 未实现”。
3. 把文档债列入 Phase 0。
4. 不要让 Codex/Cursor 基于错误文档继续开发。

### 情况 E：成本失控

处理：

1. 查看 Token Ledger，先确认哪个 project / task / run / agent 在烧钱。
2. 设置 max_runs、max_fix_attempts、max_cost_usd_per_task。
3. 对不同 Agent 设置模型档位。
4. 先压缩上下文，再考虑模型降级。
5. 低价值任务使用便宜模型；高风险任务不要盲目降级。


### 情况 F：两个任务同时想改同一个文件

处理：

1. 不要让两个 Developer Agent 同时写。
2. 让 Lock Manager 保留优先级更高的任务。
3. 另一个任务进入 waiting_for_lock。
4. 第一个任务交付后，第二个任务重新读取最新代码和 diff。
5. 必要时让 Architect 重新生成 file-change-plan。

### 情况 G：自升级影响了其它项目

处理：

1. 立即回滚到稳定 Runtime 版本。
2. 暂停 self-upgrade lane。
3. 检查哪些 run 没有正确 version pin。
4. 补充回归测试和 canary 任务。
5. 候选版本通过后再恢复后台自升级。

### 情况 H：Token 或成本突然失控

处理：

1. 暂停低优先级任务和 self-upgrade lane。
2. 查看最近 10 次 Runner 调用的 Token Ledger。
3. 找出是否有 Agent 默认带入了全量历史、全量日志或过多源码文件。
4. 启用 conservative token_economy 模式。
5. 把大任务拆成更小任务，并让 Context Pack Builder 只带必要文件。


---

## 14. 成功指标

| 指标 | 目标 |
|---|---:|
| 人工介入次数 / 低风险任务 | ≤ 1 次 |
| 低风险自动审批准确率 | ≥ 80% 起步，逐步到 95% |
| 生成项目 build 通过率 | ≥ 85% |
| 自动修复成功率 | ≥ 60% 起步 |
| 越权写文件次数 | 0 |
| 自动任务平均完成时间 | 比人工复制 Prompt 降低 50% |
| 失败任务可解释率 | 100% |
| 每次交付是否有 diff / 日志 / 测试报告 | 100% |
| 多任务日志串线次数 | 0 |
| 并发文件冲突自动拦截率 | 100% |
| 自升级影响其它项目次数 | 0 |
| 低风险并发任务成功完成率 | ≥ 80% 起步 |
| 每个 Runner 调用 Token 记录覆盖率 | 100% |
| 超预算静默继续执行次数 | 0 |
| 低风险任务平均输入 Token 降幅 | ≥ 30% 起步 |
| 自动修复循环预算超限拦截率 | 100% |
| 自升级抢占用户项目预算次数 | 0 |

---

## 15. 不要做清单

短期不要做：

- 不要直接把 Runtime 改成 LLM Agent。
- 不要一开始默认 full_auto。
- 不要允许 AI 直接 git commit / push。
- 不要跳过测试直接交付。
- 不要让 AI 修改 `.env`、密钥、CI/CD、生产部署配置。
- 不要先做 SaaS 再补本地自动化。
- 不要做太多模板市场、社区功能，先做自动编程闭环。
- 不要让 Console 直接写真实项目，必须先经过 Runner / Sandbox / Policy。
- 不要为了并发而并发；没有锁和隔离之前不要开 full parallel。
- 不要让 AgentMesh 自升级直接替换正在服务其它项目的 Runtime。
- 不要让多个任务共享同一份 Prompt 日志、测试日志或 diff 目录。
- 不要让自动修复循环无限烧 Token。
- 不要为了省 Token 把高风险任务强行交给弱模型。
- 不要默认把全量历史、全量日志、全量源码都塞进每个 Agent Prompt。

---

## 16. 推荐的下一步执行顺序

```txt
1. 修改产品文案：明确目标是减少人工审核，未来自动写代码
2. 增加 automation_mode 配置
3. 增加 L0-L5 自动化等级文档
4. 增加 Run Session 数据结构
5. 新增 Runner Adapter 接口
6. 把 Cursor SDK Orchestrator 包装成 Runner
7. Console 增加开始/暂停/继续/取消执行
8. 新增 Policy Engine
9. 低风险 file-change-plan 自动审批
10. 新增 Sandbox Workspace
11. Developer Agent 在 Sandbox 中自动写代码
12. 生成 patch 和 diff
13. 新增 Test Runner
14. 新增 Auto Fix Loop
15. Full Auto 低风险项目生成 Demo
16. 用 AgentMesh 升级 AgentMesh 自己
17. 新增 Task Pool / Run Pool
18. 新增 Scheduler 和 Lock Manager
19. 新增 Project Registry
20. 新增 Self-Upgrade Lane
21. 让 AgentMesh 自升级后台运行，同时继续服务其它项目
22. 新增 Token Ledger / Budget Gate
23. 新增 Context Pack Builder
24. 新增 Prompt 压缩和 Artifact Summary
25. 新增 Model Cost Router
26. Console 增加 Cost Dashboard
```

---

## 17. 最终战略判断

AgentMesh 的长期价值不是“让人类更方便地审核 AI”，而是：

> **让 AI 可以越来越少地依赖人类审核，但仍然不会失控。**

你的产品未来应该从“人工门禁系统”升级成“自动编程操作系统”。

最正确的演进路线是：

```txt
人工复制粘贴
→ 半自动编排
→ 策略自动审批
→ 沙箱自动写代码
→ 自动测试修复
→ 自动交付
→ 多任务并线开发
→ 自升级后台通道
→ AgentMesh 自升级同时服务其它项目
→ Token 可控与成本可观测
→ 成本可控的多任务全自动编程系统
```

这条路既符合你现在的习惯，也能逐步把你从流程里解放出来。
