# Prompt Engineer Skills — Single Source of Truth

本目录是 Prompt Engineer v3 Skills 体系的**唯一维护源**。

## 铁律

- **只在本目录编辑**。所有 skills 文件以这里的版本为准
- 不要直接编辑 `~/.cursor/skills/prompt-*` / `~/.agents/skills/prompt-*` / `~/.codex/skills/prompt-*` / `<workspace>/.cursor/skills/prompt-*` 中的副本
- 编辑后跑 `.ai-agents/scripts/sync-skills --yes` 同步到所有目标

## 受管 Skill 清单（共 8 个）

| Skill | 定位 |
|---|---|
| `prompt-engineer-router` | 总路由：分类 + A2A 评分 + 信息门禁 + 调度 |
| `prompt-engineer-checklist` | Prompt 自检（10 项 ✓/✗），由 router 主动调用 |
| `prompt-frontend-api-integration` | API 对接 / 联调 Prompt 模板（normal + mini） |
| `prompt-frontend-bugfix` | Bugfix Prompt 模板（mini + normal） |
| `prompt-frontend-page-refactor` | Plan + 微调 Page Refactor Prompt |
| `prompt-frontend-qa` | 日常 QA / PR 验收 / hotfix 回归 |
| `prompt-a2a-workflow` | A2A 路由层 + 5 阶段模板（PM / Architect / Human Review / Developer / QA） |
| `shared/` | 单一事实源 snippets（禁改集 / 分层 / 上传 / 状态按钮 / 质量标尺） |

## 同步目标

同步脚本 `.ai-agents/scripts/sync-skills` 默认同步到：

- `~/.cursor/skills/` （Cursor）
- `~/.agents/skills/` （通用 AI Agent skills）
- `~/.codex/skills/` （仅当目录存在时；Codex CLI）

每个目标内只动 `prompt-*` 与 `shared/`，**不会触碰用户其他 skill**。

## 使用

详见 `.ai-agents/scripts/sync-skills --help`。最常用：

```bash
.ai-agents/scripts/sync-skills              # dry-run，看会发生什么
.ai-agents/scripts/sync-skills --yes        # 真正写入
.ai-agents/scripts/sync-skills --yes --clean  # 写入 + 删除目标端已不存在的本组 skill
```
