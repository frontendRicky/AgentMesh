---
schema_version: a2a/v1
---

# Agent Model Selection

每个 agent 下面是 runtime 给出的可选模型清单。**把你想用的那一项的 `- [ ]` 改成 `- [x]` 即可**。每个 agent 最多勾选一个；不勾任何一项 = 使用 runtime 默认推荐。

> Runtime 仅推荐，不会自动切换 Cursor 模型、不会自动执行 Codex。
> 高风险（P0/P1）任务会强制升档到高推理模型，覆盖你的勾选；prompt 顶部的 `Warnings` 会明示。

## 解析优先级（高 → 低）

1. CLI `--model <slug>`（一次性）
2. **本文件 `## <role>` 下勾选的 `- [x] <model>`**
3. `agent-cards/<role>.card.md` frontmatter 的 `model:` 字段
4. `DEFAULT_MODEL_PREFERENCES` 兜底

## 如何加自定义模型

清单里没有的 slug，直接在对应 `## <role>` 下加一行 `- [x] your-custom-slug` 即可。runtime 不会校验 slug 是否真实存在，由你自己保证 Cursor 能识别。

---

## pm

- [ ] claude-4.6-sonnet-medium-thinking  -- 默认推荐 / fallback
- [ ] gpt-5.5
- [ ] claude-opus-4-7-thinking-high

## architect

- [ ] claude-opus-4-7-thinking-high  -- 默认推荐
- [ ] gpt-5.5
- [ ] claude-4.6-sonnet-medium-thinking

## developer

- [ ] gpt-5.5  -- 默认推荐 (codex 可用)
- [ ] claude-4.6-sonnet-medium-thinking
- [ ] claude-opus-4-7-thinking-high

## qa

- [ ] claude-opus-4-7-thinking-high  -- 默认推荐
- [ ] gpt-5.5
- [ ] claude-4.6-sonnet-medium-thinking

## controller

- [ ] gpt-5.5-mini  -- 默认推荐 (轻量)
- [ ] gpt-5.5
- [ ] claude-4.6-sonnet-medium-thinking

## risk

- [ ] claude-opus-4-7-thinking-high  -- 默认推荐 (P0/P1 必备)
- [ ] gpt-5.5
- [ ] claude-4.6-sonnet-medium-thinking
