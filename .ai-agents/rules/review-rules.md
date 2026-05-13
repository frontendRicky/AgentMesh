# Review Rules — 审核规则

> 规范每个审核点应检查的内容。Cursor 在协助用户做审核时按本规则给出 checklist。

## 1. PRD 审核点（PM Agent 内部自检 + Architect 接收时校验）

- [ ] 用户角色清晰（多角色情况下角色矩阵明确）
- [ ] 核心流程描述完整（建议含 mermaid）
- [ ] 页面/交互描述完整
- [ ] 权限规则覆盖 5 层（菜单 / 路由 / 按钮 / 接口 / 数据）
- [ ] 异常状态显式（接口失败 / 字段缺失 / 字段异常 / 网络超时）
- [ ] 边界场景显式（空数据 / 大数据 / 极端输入 / 并发）
- [ ] loading / empty / error / success 四态显式定义
- [ ] 验收标准可被 QA 直接转测试用例
- [ ] 所有"待确认"问题已列出（不臆断、不假设）

## 2. 技术方案审核点（Architect Review 主审）

- [ ] tech-plan 含全部 11 节
- [ ] **"最小可行方案"非空**（避免过度设计）
- [ ] 影响范围说明清晰
- [ ] 模块边界说明清晰
- [ ] 数据流 / 状态流 / 接口契约 / 权限点 显式
- [ ] 第三方依赖列表（含必要性论证）
- [ ] 风险点至少 1 个
- [ ] 回滚方案可执行
- [ ] 回答了 PM handoff 中的 architect_must_answer
- [ ] 待确认问题已列出

## 3. 文件修改计划审核点（Architect Review 主审）

- [ ] file-change-plan 每条目 7 字段完整
- [ ] **新增文件**已预先列出（operation: create）
- [ ] 默认禁改集（package.json / lock / .github/** / .gitlab-ci.yml / Dockerfile / CI 配置）operation: forbidden（除非用户批准）
- [ ] 修改条目都有清晰 reason
- [ ] 高风险条目（risk: 高）有详细 notes 与回滚思路
- [ ] owner 字段合理（developer / qa / developer+qa-approved / user-approved）

## 4. 代码实现审核点（QA + 用户在 Final Review 抽查）

- [ ] 所有改动都在 file-change-plan 白名单中
- [ ] changed-files 越界审计 == 0
- [ ] implementation-log 每步记录清晰
- [ ] 没有触碰默认禁改集
- [ ] 没有写死 mock 进入正式逻辑
- [ ] 没有大范围重构无关代码
- [ ] 没有删旧逻辑（除非 operation: delete）
- [ ] 复用了已有 component / hook / util / type / service

## 5. 测试报告审核点（Final Review 主审）

- [ ] 7 维测试每维都有用例（即使"无适用"也明示）
- [ ] 每条用例 status 为 5 枚举之一
- [ ] 没有伪造 pass
- [ ] manual_required 用例都给出可执行步骤
- [ ] fail 用例都有根因分析
- [ ] pass 数 + manual_required 数 ≥ 用例总数 × 90%
- [ ] 回归测试覆盖
- [ ] 测试报告末尾有"是否可交付"明确结论

## 6. 最终验收审核点（Final Review 主审）

- [ ] PRD 验收标准全部满足
- [ ] tech-plan 关键决策都已实现
- [ ] file-change-plan 与 changed-files 一致
- [ ] test-report 中无未处理 fail
- [ ] acceptance-checklist 每项都已勾选（pass 或 manual_required+步骤）
- [ ] human-reviews/architect-review.md 存在且 verdict == approved
- [ ] human-reviews/final-review.md 即将由本次审核创建
- [ ] 已知遗留问题已显式列出（如有）

## 7. Review Record 审核点（Controller 校验）

Controller 在读取 review record 后必须检查：

- [ ] frontmatter 字段完整（review_id / review_type / reviewed_artifacts / reviewer / reviewed_at / verdict / followup_required / schema_version）
- [ ] verdict ∈ { approved, rejected, needs_changes }
- [ ] reviewer 字段不是角色名（必须是真实用户 handle）
- [ ] reviewed_artifacts 中的 artifact_id 都真实存在
- [ ] verdict ∈ { rejected, needs_changes } 时 issues 非空且每条 issue 含 severity / description / affected_artifact

任一不通过 → 进入 Blocker 创建流程。
