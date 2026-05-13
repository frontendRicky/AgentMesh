---
artifact_id: A-T-YYYY-NNN-acceptance-checklist
task_id: T-YYYY-NNN
artifact_type: acceptance_checklist
produced_by: qa
consumed_by:
  - human-review-actor
file_path: artifacts/qa/acceptance-checklist.md
version: 1
status: draft
summary: <N 项验收清单 / 全部可被人工勾选>
dependencies:
  - A-T-YYYY-NNN-prd
  - A-T-YYYY-NNN-test-report
validation_result: pending
created_at: 2026-MM-DDTHH:MM:SS+08:00
schema_version: a2a/v1
---

# Acceptance Checklist: <task_title>

> 每项必须人工可勾选,含来源 / 验证方式 / status / 备注。

## 1. 功能验收

- [ ] **<验收项 1>**
  - 来源: PRD §2.3
  - 验证方式: 手动操作
  - status: pass | fail | blocked | not_executed | manual_required
  - 备注: <可选>

- [ ] **<验收项 2>**
  - 来源: PRD §3.1
  - 验证方式: 看接口返回
  - status: pass
  - 备注: 关联 GET /api/xxx

## 2. 权限验收（按角色 × 5 层）

- [ ] **角色 A 菜单可见性**
  - 来源: PRD §4 角色矩阵
  - 验证方式: 切换角色登录
  - status: pass

- [ ] **角色 B 越权场景拦截**
  - 来源: PRD §4 越权场景
  - 验证方式: 模拟越权请求
  - status: manual_required
  - manual_steps: 1) 用 B 角色登录 2) 直接访问 /a-only 3) 应被路由守卫拦截到 /403

## 3. 异常状态验收

- [ ] **接口失败 4xx 显示**
  - 来源: PRD §5
  - 验证方式: mock 接口返回 400
  - status: pass

## 4. 四态显式验收

- [ ] **loading 骨架屏显示**
  - 来源: PRD §7
  - 验证方式: 慢网络观察
  - status: pass

- [ ] **empty 引导动作可点击**
  - 来源: PRD §7
  - 验证方式: 清空数据后进入
  - status: pass

## 5. 性能与兼容性

- [ ] **首屏加载 < 2s**
  - 来源: 用户原始需求
  - 验证方式: Chrome Lighthouse
  - status: manual_required
  - manual_steps: 1) 打开 Chrome 2) DevTools → Lighthouse → Generate report 3) FCP < 2s

## 6. 回归项

- [ ] **<受影响模块 1 旧功能不变>**
  - 来源: regression-scope（bugfix）/ tech-plan §1
  - 验证方式: 跑老用例
  - status: pass

## 7. 手动验收清单（用户最终勾选）

> 用户在 Final Review 阶段逐项勾选验证。

- [ ] 打开 X 页面无报错
- [ ] 操作 Y 流程顺畅
- [ ] 关闭浏览器再打开，状态保持
- [ ] 在小屏 / 大屏均正常
- [ ] 暗黑模式下视觉一致（如适用）
- [ ] 接口断网后有友好提示

## 总览

- 总项数：N
- 已勾选：N
- pass + manual_required（已提供步骤）：N
- 不可交付项（fail / blocked 未处理）：N
