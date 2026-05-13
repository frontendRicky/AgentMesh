# A2A Examples

本目录存放完整的 A2A Task 工作流示例，供参考和学习。

每个示例对应一个真实运行过的完整 Task 目录，包含：

- `task.md` — 任务元信息
- `state.md` — 状态机全历史
- `messages/` — Agent 之间的所有 Handoff 消息
- `artifacts/pm/` — PM Agent 产物（需求分析、范围界定等）
- `artifacts/architect/` — Architect Agent 产物（技术方案、file-change-plan、风险计划）
- `human-reviews/` — Human Review Actor 的审核记录

## 示例列表

| 目录 | 说明 | 最终状态 |
|---|---|---|
| `T-2026-001/` | Runtime 0.1.0rc5 开发任务：A2A Cursor SDK Orchestrator 集成（.ai-agents/scripts/）| `developer_processing`（PM→Architect→Human Review→Developer 全链路已走通） |

## 注意事项

- 这些目录仅供参考，**不是活跃 workspace**。
- 活跃 Task 工作区在项目根的 `.ai-agents/workspace/<task-id>/`，不提交到本仓库。
- 若要在你自己的项目中使用 A2A，请参考 [根目录 README.md](../../README.md) 和 `a2a-bootstrap-project` 工具。
