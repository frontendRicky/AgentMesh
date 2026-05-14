# CHANGELOG

本系统按 `schema_version` 演进，重大调整须升级 `a2a/v*` 版本号。

## v1.0.0 兼容扩展 — 2026-05-14（Per-Agent Model Override）

性质：**协议向后兼容的运行时扩展**，未升级 schema_version，未破坏 v1.0.0 冻结声明。

新增工件：

- `agent-cards/model-overrides.md`：用户级模型选择文件，支持 `## <role>` + `- [x] <model-slug>` checklist 语法
- 各 `agent-cards/<role>.card.md` frontmatter 新增可选 `model:` 字段（fallback 用，留空即不生效）

新增字段：

- `AgentCard.model: str | None`（agent-card schema 向后兼容，旧卡片无此字段仍可用）
- `ModelSelectionResult.override_source: str`（`cli` / `overrides_file` / `agent_card` / `default`）

Override 优先级（高 → 低）：

1. CLI `--model <slug>`
2. `model-overrides.md` body checklist
3. `model-overrides.md` frontmatter `overrides:` 映射
4. 各 `<role>.card.md` frontmatter 的 `model:` 字段
5. `DEFAULT_MODEL_PREFERENCES`（按 role 默认）

不变项：

- A2A schema 全部不变
- state.md / task.md / message / artifact / blocker / review schema 不变
- Developer Gate / Human Review 双步 / Blocker 两阶段 / P0/P1 Risk Gate / Final Delivery 全部规则保持
- P0/P1 风险高推理模型升级策略**不可被 override 绕过**
- Runtime 仍不调用 LLM、不切换 Cursor 模型、不执行 Codex

详见 [agent-cards/model-overrides.md](agent-cards/model-overrides.md) 与 `.cursor/rules/ai-agents.mdc` §16。

---

## v1.0.0 — Markdown File-based A2A Protocol Frozen

日期：2026-05-11

内容：

- F-01 ~ F-09 已全部修复
- mini regression T-2026-002 已通过
- task_id 与 workspace 目录名一致规则已冻结
- role 统一为 developer
- gate_failure 与 blocker_request 已区分
- Blocker 两阶段机制已冻结
- Human Review / Final Review 双步流转已冻结
- Controller 中断恢复规则已冻结
- QA not_executed 试运行规则已冻结
- 当前协议版本可作为 Python Agents Runtime v1 的实现基准

### 冻结后的修改纪律

- 任何破坏性协议改动必须升级为 v2（新建 `a2a/v2/**` 与新 schema_version）
- v1 Task 不强制迁移到 v2
- Python Runtime V1 必须兼容本版本，**只能读取与执行协议，不允许修改协议结构**
- 详 [a2a/protocol.md](a2a/protocol.md) §6 v1.0.0 冻结声明

### 关联工件

- mini regression 归档：[workspace/T-2026-002/](workspace/T-2026-002/)（含 F-01~F-09 验证证据链 + 19 条 state 写入历史）
- 试运行历史归档：[examples/feature-add-settings-page/T-2026-001/](examples/feature-add-settings-page/T-2026-001/)

---

## a2a/v1 — 2026-05-09

初始版本。建立完整 A2A 协作系统骨架。

### 系统结构

- 4 核心 Agent：PM / Architect / Senior FE Dev / QA Tester
- 1 Flow Controller：仅调度、校验、状态流转
- 1 Human Review Actor：用户给出 verdict 后由 Cursor 代写 review record
- 8 套 Schema：agent-card / task / state / message / artifact / handoff-contract / blocker / review
- 6 条 Flow：feature / refactor / bugfix / ui-redesign / permission / api-integration
- 7 套 Rule：global / a2a / frontend / code-change / review / test / cursor
- 16 套 Template
- Cursor Rule：alwaysApply 强制 [A2A] 回复头 + 4 步 Task 识别 + 5 条写代码门禁

### 关键设计决策

1. `task.md` 与 `state.md` 严格分离：task 仅静态元信息，state 是唯一动态状态源（仅 Controller 写）
2. 写代码双门禁：`current_status == developer_processing` AND `human_review_status == approved` 同时满足才允许
3. Blocker 两阶段：Agent 只能发 `from-<role>-*-blocker-request.md`；正式 Blocker 与 state 唯一由 Controller 写
4. Human Review 双角色：Actor 写 review record，Controller 只读校验，禁止伪造
5. 审核翻转双步：先翻 `*_status` 字段，再独立推 `current_status`
6. Handoff Contract 严格区分 input/output × artifact/message/review_record 六类字段
7. Architect / QA 默认源码只读；QA 写测试文件须经 `qa-file-change-plan.md` 授权
8. file-change-plan 7 字段白名单（path / operation / allowed / reason / risk / owner / notes）
9. QA 用例 5 状态：pass / fail / blocked / not_executed / manual_required；禁止伪造 pass
10. final-delivery 仅在 `final_review_status == approved` 后由 Controller 写，且只引用不改写

### 已知限制

- 当前为本地 File-based 模式，无 HTTP API
- 不支持多 Task 并发自动调度（同一时间一个 active-task）
- 不绑定具体技术栈，frontend-rules 仅通用规范；项目接入时可新增 `rules/stack-<框架>.md` 扩展
