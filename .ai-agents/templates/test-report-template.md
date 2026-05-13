---
artifact_id: A-T-YYYY-NNN-test-report
task_id: T-YYYY-NNN
artifact_type: test_report
produced_by: qa
consumed_by:
  - human-review-actor
file_path: artifacts/qa/test-report.md
version: 1
status: draft
summary: <N 用例 / X pass / Y fail / Z manual_required>
dependencies:
  - A-T-YYYY-NNN-prd
  - A-T-YYYY-NNN-tech-plan
  - A-T-YYYY-NNN-implementation-log
  - A-T-YYYY-NNN-changed-files
validation_result: pending
created_at: 2026-MM-DDTHH:MM:SS+08:00
schema_version: a2a/v1
---

# Test Report: <task_title>

> 7 维测试 + 5 状态枚举。**严禁**未执行写 pass。

## 维度 1：主流程

### TC-01 <主流程用例 1>

- **step**: 1) 进入页面 2) 点击 X 3) 输入 Y 4) 确认
- **expected**: 跳转到 Z,显示成功提示
- **actual**: 已验证一致
- **status**: pass
- **notes**: 关联接口 GET /api/xxx

### TC-02 ...

## 维度 2：异常流程

### TC-10 <接口失败异常>

- **step**: 1) 模拟接口 500 2) 触发请求
- **expected**: 显示错误提示 + 重试按钮
- **actual**: 已验证一致
- **status**: pass
- **notes**: 已通过 mock 验证

### TC-11 <字段缺失>

- **step**: 1) 后端返回空字段 2) 触发渲染
- **expected**: 显示"-"占位
- **actual**: -
- **status**: manual_required
- **manual_steps**: <详细到不熟悉项目的人也能执行>
- **notes**: 暂无 mock 工具支持自动化

## 维度 3：权限（角色 × 5 层）

### TC-20 <角色 A 菜单可见>
### TC-21 <角色 A 路由可访问>
### TC-22 <角色 A 按钮可点>
### TC-23 <角色 A 接口可调>
### TC-24 <角色 A 数据可见范围>
### TC-25 <角色 B 越权场景>
...

## 维度 4：空状态

### TC-30 <空列表显示>
### TC-31 <无数据初始进入>
...

## 维度 5：加载状态（loading）

### TC-40 <慢网络 loading>
### TC-41 <长时间等待>
...

## 维度 6：接口失败

### TC-50 <4xx 处理>
### TC-51 <5xx 处理>
### TC-52 <超时处理>
### TC-53 <网络断>
...

## 维度 7：边界

### TC-60 <极大输入>
### TC-61 <极小输入>
### TC-62 <并发>
### TC-63 <临界值>
...

## 维度 8（附加）：回归

### TC-70 <受影响模块旧功能 1>
### TC-71 <受影响模块旧功能 2>
...

## 汇总

| 状态 | 数量 |
|---|---|
| pass | N |
| fail | N |
| blocked | N |
| not_executed | N |
| manual_required | N |
| **总数** | **N** |

- **pass + manual_required 数**：N
- **占比**：N / 总数 = X%
- **门禁**：≥ 90% → 可交付 Final Review；< 90% → 必须发 blocker-request

## 失败用例归属

| TC | status | root_cause_hint | suggested_owner |
|---|---|---|---|
| TC-XX | fail | <根因> | developer / architect |

## 测试结论

- [ ] 7 维都覆盖（含"无适用"明示）
- [ ] 5 层权限覆盖（如适用）
- [ ] pass + manual_required ≥ 90%
- [ ] 越界审计已读，越界文件数 == 0
- [ ] **结论**：可交付 / 不可交付（如不可交付，附原因）
