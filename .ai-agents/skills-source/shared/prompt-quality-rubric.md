# Prompt Quality Rubric（Prompt 质量标尺）

> 单一事实源。被 `prompt-engineer-checklist` 引用，所有模板"自检"用同一把尺。

## 10 项质量门禁

每生成一个 Prompt，按下表逐项 ✓/✗ 自检：

| # | 维度 | 通过标准 | 常见失败 |
|---|---|---|---|
| 1 | **可执行** | Agent 拿到能直接动手，不需要再问 | 模糊指令 "优化一下"、"看着改" |
| 2 | **范围明确** | 列出**允许修改**的具体路径或 scope | 只说"修这个 bug" 没说改哪些文件 |
| 3 | **禁改明确** | 引用 `<see: shared/frontend-forbidden-paths.md>` 或单列 | 漏掉 `axiosConfig` / `middleware` |
| 4 | **验收可量化** | 验收条件能 yes/no 判定 | "状态正确"（错）→ "draft 状态下 submit 按钮 enabled"（对） |
| 5 | **退出条件** | 遇到 X 时停止 / 反馈 | 没写"白名单外路径 → blocker-request" |
| 6 | **信息充足** | 模板里没有 `【贴 Network】` `<你的需求>` 这种占位符 | 留了一堆 placeholder |
| 7 | **长度合理** | 在档位上限内（mini ≤ 15 / normal ≤ 40 / heavy ≤ 80） | 一个 warning 修复给了 80 行 |
| 8 | **不要 AI 盲猜** | 不假定接口字段 / 不假定状态枚举 | "应该有个 status 字段" |
| 9 | **不过度保守** | 禁改有 escape hatch | "绝对不许改 X" 没说例外条件 |
| 10 | **风险可见** | 标注 P0/P1 风险点 + 残余风险 | 完全没写"潜在副作用" |

## 输出格式

每次生成 Prompt 后，**Prompt 上方**贴一张自检表：

```text
## Prompt Self-Check

| # | 维度 | 状态 | 备注 |
|---|---|---|---|
| 1 | 可执行 | ✓ | |
| 2 | 范围明确 | ✓ | 列出 services/foo.ts + hooks/useFoo.ts |
| 3 | 禁改明确 | ✓ | 引用 shared/frontend-forbidden-paths |
| 4 | 验收可量化 | ✓ | 4 条验收均可 yes/no |
| 5 | 退出条件 | ✓ | 白名单外 → blocker-request |
| 6 | 信息充足 | ⚠️ | 需要用户补：接口测试报告 |
| 7 | 长度合理 | ✓ | 35/40 行 |
| 8 | 不要盲猜 | ✓ | 字段表来自后端文档 |
| 9 | 不过度保守 | ✓ | escape hatch 已加 |
| 10 | 风险可见 | ✓ | P1: 影响列表 mutate |
```

任一 ⚠️ / ✗ → **修 Prompt 或反问用户**，不要直接交付。

## 反模式（自动失败）

下列任一出现 → Prompt 整体判 ✗：

- "全部重构" / "顺手 cleanup" / "看着办" / "优化一下"
- 留 `<贴 xxx>` / `【你的需求】` 这种占位符
- 没引用 forbidden-paths（除非明确说 "本次允许动 X"）
- 验收条件全是形容词（"流畅"、"美观"、"正确"）
- 让 Agent 一次性改 ≥ 10 文件且没 phase 拆分
- A2A 任务但没说当前阶段 / 没读 file-change-plan
