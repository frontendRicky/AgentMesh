---
name: prompt-engineer-checklist
description: Prompt 自检 Skill。由 prompt-engineer-router 在生成 Prompt 后主动调用，不依赖用户直接触发。检查 Prompt 是否可执行、范围明确、禁改清晰、验收可量化、退出条件、信息充足、长度合理、避免盲猜、避免过度保守、风险可见。输出 ✓/✗ 自检表贴在 Prompt 上方。
---

# Prompt Engineer Checklist

## 何时被调用

- 由 `prompt-engineer-router` 工作流第 7 步 Read 本文件后执行
- 任何子 skill 在交付 Prompt 前也可主动调用本检查
- 用户**几乎不会**直接触发本 skill；如果用户说"自检一下"才直接走

## 10 项质量门禁

按 `<see: <workspace>/.cursor/skills/shared/prompt-quality-rubric.md>` 中 10 项标准逐项打分：

| # | 维度 | 关键判定 |
|---|---|---|
| 1 | 可执行 | Agent 拿到能直接动手？ |
| 2 | 范围明确 | 列出允许修改的路径/scope？ |
| 3 | 禁改明确 | 引用 forbidden-paths 或显式列？ |
| 4 | 验收可量化 | 每条都能 yes/no 判定？ |
| 5 | 退出条件 | 白名单外 → blocker-request 写了？ |
| 6 | 信息充足 | **无 `<贴 xxx>` / `【你的需求】` 占位符**？ |
| 7 | 长度合理 | mini ≤ 15 / normal ≤ 40 / heavy ≤ 80？ |
| 8 | 不要盲猜 | 字段/枚举来自后端文档，不假设？ |
| 9 | 不过度保守 | 禁改有 escape hatch？ |
| 10 | 风险可见 | 标 P0/P1 + 残余风险？ |

## 输出格式（必须放在 Prompt 正文上方）

```text
## Prompt Self-Check

| # | 维度 | 状态 | 备注 |
|---|---|---|---|
| 1 | 可执行 | ✓ | |
| 2 | 范围明确 | ✓ | 列了 X / Y |
| 3 | 禁改明确 | ✓ | 引用 shared |
| 4 | 验收可量化 | ✓ | N 条均 yes/no |
| 5 | 退出条件 | ✓ | 白名单外 → blocker |
| 6 | 信息充足 | ⚠️ | 需补：<具体项> |
| 7 | 长度合理 | ✓ | NN/40 |
| 8 | 不要盲猜 | ✓ | |
| 9 | 不过度保守 | ✓ | escape hatch |
| 10 | 风险可见 | ✓ | P1: ... |

总评：pass / needs-fix / needs-user-input
```

## 处置规则

| 自检结果 | 处置 |
|---|---|
| 全 ✓ | 交付 Prompt |
| 仅第 6 项 ⚠️（信息不足） | **不交付 Prompt**，先列反问清单（≤ 3 问） |
| 第 7 项 ✗（过长） | 拆分任务或降级到子任务，重新生成 |
| 其他任一 ✗ | 修 Prompt，重跑自检 |

## 反模式（自动判 ✗）

- "全部重构" / "顺手 cleanup" / "看着办" / "优化一下"
- 留 `<贴 xxx>` / `【你的需求】` 占位符
- 验收全是形容词（"流畅"、"美观"、"正确"）
- 一次让 Agent 改 ≥ 10 文件且没 phase 拆分
- A2A 任务但没说当前阶段 / 没读 file-change-plan

## 何时不用本 Skill

- 用户直接问业务问题，没要 Prompt → 不用
- Prompt 已由其他严格门禁产出（如 A2A Controller 直接生成）→ 可跳过，但建议保留作为二次校验
