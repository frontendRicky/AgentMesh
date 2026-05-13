# Test Rules — 测试规则

> 规范 QA Agent 的测试设计、执行与报告。**核心**：5 状态 + 7 维 + 越界守门。

## 1. 7 维测试覆盖（每维都必须有用例）

每个 Task 的 test-report.md 必须覆盖以下 7 维（即使某维"无适用"，也要明示该维不适用并给出原因）：

1. **主流程**：核心路径走通
2. **异常流程**：接口失败 / 字段缺失 / 字段异常 / 网络超时
3. **权限**：菜单 / 路由 / 按钮 / 接口 / 数据 5 层 × 涉及角色
4. **空状态**：列表无数据、对象字段缺失、首次进入
5. **加载状态**（loading）：网络慢 / 接口未返回 / 长时间等待
6. **接口失败**：4xx / 5xx / 超时 / 网络断
7. **边界**：极大 / 极小 / 极端输入 / 并发 / 临界值

外加：**回归** — 受影响模块的旧功能不破坏（与 file-change-plan 关联）。

## 2. 5 状态枚举（status 字段）

每条用例必须显式标注 status，5 个枚举之一：

| status | 含义 | 何时使用 |
|---|---|---|
| `pass` | 实际执行通过 | **必须**真正执行了用例并验证通过 |
| `fail` | 实际执行失败 | 实际执行后预期与实际不一致 |
| `blocked` | 依赖未就绪，无法执行 | 上游缺失（接口未上、依赖组件未实现） |
| `not_executed` | 未执行 | 故意跳过（如非本期范围、低优先） |
| `manual_required` | 需要人工执行 | 自动化无法覆盖（如视觉对比、设备适配、并发） |

**严禁**：在未实际执行的情况下写 `pass`。这是 QA 行为最严重的违规之一。

### 试运行特例（dry-run）— F-07

当 `task.md` 的 `task_type == dry_run`（或 constraints 含 `dry-run: true` / 用户在 Prompt 中明示"试运行"）时：

- 大量用例落 `not_executed` / `manual_required` 是**预期**，不视为覆盖率不足
- test-report.md 顶部必须**明示**"本 Task 为试运行模式，QA 状态分布偏向 not_executed/manual_required 是合规的"
- 仍**严禁**：未执行就写 `pass`（红线不变）
- 试运行 acceptance-checklist 中的"PRD 验收项"可整体落"试运行不验证（真实施时验证）"
- 真实施前必须重新启动 QA，把 not_executed 全部转为 pass / fail / blocked / manual_required

## 3. 用例字段（每条用例必含）

```markdown
### TC-<seq> <用例标题>

- **step**: <可执行步骤,逐步>
- **expected**: <预期结果>
- **actual**: <实际结果,pass 时也要写"已验证一致">
- **status**: pass | fail | blocked | not_executed | manual_required
- **notes**: <补充,如关联接口 / 关联文件 / 限制条件>
```

如 status == `manual_required`，必须额外提供：
- **manual_steps**: <人工执行步骤,详细到一个不熟悉项目的人也能执行>

如 status == `fail`，必须额外提供：
- **root_cause_hint**: <根因初判>
- **suggested_owner**: <建议谁修>

## 4. 验收清单（acceptance-checklist.md）

每项必含：

```markdown
- [ ] <验收项,从 PRD / tech-plan / 用户原始需求衍生>
  - 来源: PRD §2.3 / tech-plan §4 / 用户需求
  - 验证方式: 手动操作 / 看截图 / 看接口返回 / 看日志
  - status: pass | fail | blocked | not_executed | manual_required
  - 备注: <可选>
```

## 5. 测试通过率门禁

- pass 数 + manual_required 数 ≥ 用例总数 × 90% → 可交付 Final Review
- < 90% → 必须发 blocker-request 让 Dev / Architect 修复
- 任何 fail 用例都必须在 final-review 前明确归属（已修复 / 已知遗留 / 已转新 Task）

## 6. 回归测试规则

- 必须覆盖 file-change-plan 中所有 operation: modify 与 operation: delete 涉及的模块
- bugfix-flow 必须额外覆盖 regression-scope 中的所有受影响模块
- refactor-flow 必须额外覆盖"不允许破坏的行为"列表

## 7. 测试文件改动权限

- QA 默认主业务代码只读
- 如需新增测试文件 / 测试夹具：
  - 先写 `artifacts/qa/qa-file-change-plan.md`
  - owner 字段为 `qa` 或 `developer+qa-approved`
  - 用户批准后再创建测试文件

## 8. 手动验收清单

QA 必须在 acceptance-checklist.md 中提供"手动验收清单"小节，列出用户可逐项勾选验证的清单：

```markdown
## 手动验收清单

- [ ] 打开 /settings 页面无报错
- [ ] 切换主题立即生效
- [ ] 刷新页面后主题保持
- [ ] 无权限用户无法看到 Settings 菜单
...
```

## 9. 禁止行为

- **严禁**用"看起来没问题"作结论
- **严禁**未执行写 pass
- **严禁**漏 7 维任一维度
- **严禁**漏 5 层权限测试任一层（如涉及）
- **严禁**修改主业务代码
- **严禁**未经 qa-file-change-plan 授权新建任何源码文件
