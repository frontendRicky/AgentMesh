# Agent Card Schema

> 描述每个 Agent 的能力、读写权限、上下游、禁止事项。机器可读，是 Cursor 路径权限校验的依据。

## 1. 字段定义

### Frontmatter（YAML）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `agent_id` | string | 是 | 全局唯一，如 `pm-001` |
| `agent_name` | string | 是 | 人类可读名称 |
| `role` | enum | 是 | `pm` / `architect` / `dev` / `qa` / `controller` / `human` |
| `version` | string | 是 | Card 版本，如 `1.0.0` |
| `schema_version` | string | 是 | 固定 `a2a/v1` |

### 正文 sections（Markdown）

按以下顺序，每节都必须存在：

1. `## description` — 一段话描述 Agent 职责
2. `## capabilities` — 具体能做的事（bullet list）
3. `## input_artifacts` — 启动前必读的上游 Artifact 列表
4. `## output_artifacts` — 必须产出的 Artifact 列表
5. `## readable_paths` — 可读路径白名单（glob 形式）
6. `## writable_paths` — 可写路径白名单（glob 形式）
7. `## allowed_actions` — 显式允许的操作
8. `## forbidden_actions` — 显式禁止的操作
9. `## upstream_agents` — 上游 Agent ID 列表
10. `## downstream_agents` — 下游 Agent ID 列表
11. `## handoff_contracts` — `in:` 与 `out:` 引用的 Handoff Contract 文件
12. `## validation_checklist` — 自检清单（checkbox 形式）
13. `## stop_conditions` — 停止条件（什么情况下应停下）

## 2. 示例 Frontmatter

```yaml
---
agent_id: pm-001
agent_name: Product Manager Agent
role: pm
version: 1.0.0
schema_version: a2a/v1
---
```

## 3. 校验规则

- **path 字段必须用 glob**，如 `workspace/<id>/artifacts/pm/**`，不能用具体文件名
- **`writable_paths` 是写权限唯一依据**：Cursor 每次写文件前必须自检目标路径命中此白名单
- **`forbidden_actions` 是负向约束**：即使路径在 writable_paths，如违反 forbidden 也拒绝
- **`upstream_agents` / `downstream_agents` 不能成环**

## 4. 常见违规示例

### 反例 1：Architect Card writable_paths 含源码路径

```yaml
writable_paths:
  - src/**          # 错误!Architect 严禁写源码
```

### 反例 2：QA Card 默认允许写主业务代码

```yaml
writable_paths:
  - src/**          # 错误!QA 默认源码只读;写测试文件须经 qa-file-change-plan 授权
```

### 反例 3：Controller Card writable_paths 含 artifacts/<role>/

```yaml
writable_paths:
  - artifacts/architect/**   # 错误!Controller 严禁写专业 Agent 的 artifacts
```

### 反例 4：Agent Card 缺 forbidden_actions

```yaml
# 没写 forbidden 章节        # 错误!必须显式列出禁止行为,否则 Cursor 无负向约束
```

## 5. 下游使用方式

- Cursor 加载 `state.current_agent` 后，立即 Read `agent-cards/<role>.card.md`
- 写文件前先校验 writable_paths
- 启动前先按 input_artifacts 逐个 Read
- 不满足 stop_conditions 时不允许产出最终 Artifact，应继续工作或发 Blocker Request
