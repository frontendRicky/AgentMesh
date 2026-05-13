---
artifact_id: A-T-2026-001-risk-and-open-questions
task_id: T-2026-001
artifact_type: risk_and_open_questions
produced_by: pm
consumed_by:
  - architect
  - developer
  - qa
  - human
file_path: artifacts/pm/risk-and-open-questions.md
version: 1
status: ready
summary: 综合"后端 PRD + 测试报告"识别的风险点与待确认项，标注影响层（前端 / 后端 / 跨域）与建议处置。
dependencies:
  - A-T-2026-001-api-contract-checklist
  - A-T-2026-001-state-and-action-matrix
validation_result: pass
validation_notes: 所有风险条目均与后端文档或测试报告记录可追溯。
created_at: 2026-05-13T16:00:00+08:00
schema_version: a2a/v1
---

# 风险与待确认问题（Risks & Open Questions）

> 优先级：P0=阻塞前端联调；P1=需 Architect 在 file-change-plan 中明确策略；P2=人工验证 / 长期治理。

## 风险

### R-01【P1 / 跨域】AI 成功回调后端 JSONB 写入失败

- 现象（测试报告 §"失败项日志证据"）：`AI外部回调integration` 200 成功 + MQ 消费触发，但 hire 写 `talent_resume.highlights/risk_points/interview_suggestions/raw_ai_json` 报 `column "highlights" is of type jsonb but expression is of type character varying`。
- 影响：成功回调路径无法落主表 → `analysis_status` 卡在 1（分析中）→ 平台管理列表无新增；`/ai-insight` 详情即便能调通也是模拟数据。
- 前端能做：
  - 列表轮询超时（如 `analysisStatus=1` 持续 > 5 分钟）时，前端给出可见提示（"分析中"右侧加 Tooltip "AI 处理较慢，可稍后刷新"）；不主动重发分析。
  - 不在前端隐藏问题（即使后端没写入，前端展示状态仍按接口返回为准）。
- 后端处置：配置 MyBatis JSONB TypeHandler 或 SQL cast；不属于前端范围。
- 等待事项：后端修复后重测；前端 hook 层只对接固定契约，无需变更代码。

### R-02【P0 / 后端】AI 提交接口当前 SKIP

- 现象（测试报告 §14）：AI 服务接收任务接口未提供，`/talent/resume/analyze` 触发链路无法端到端验证。
- 影响：前端按契约对接 `/analyze` 后无法验证"分析中 → 成功 / 失败"全链路。
- 前端处置：按 PRD §3.4 契约对接；联调时由 Architect 在 file-change-plan 中指定一种"开发期占位"方式，例如：
  1. 不实现任何 mock，AI 服务就绪前接受"分析中无更新"作为已知现象；
  2. 或前端约定一个 `?mockAi=1` URL 参数走 fixture（仅 dev）—— 但**任何 mock 代码必须可由开发开关移除**，不影响 prod 行为。
- 推荐：选 1（最小改动），由后端推进 AI 服务对接进度。

### R-03【P1 / 前端】COS 上传 confirm 失败重试

- 现象：PRD §2.7 要求 confirm 幂等；测试报告中 confirm 100% 成功，但需考虑生产环境网络抖动。
- 影响：用户上传"已 PUT 成功但 confirm 失败"时，重新申请 presign 会产生孤儿 COS 对象 + 多余明细。
- 前端处置：
  - confirm 失败时**优先重试 confirm**（同一 `uploadItemId + cosKey + fileSize + contentType`），最多 3 次，间隔退避 1s / 2s / 4s；
  - 仍失败 → toast"上传完成但确认失败，请重试"，保留前端瞬时态，可手动重试；
  - **不**回退到 presign，**不**重新 PUT。

### R-04【P1 / 前端】presign 过期（10 分钟）

- 现象：PRD §2.4，临时上传地址有效期 10 分钟。
- 影响：长时间停顿后 PUT COS 失败（403/SignatureDoesNotMatch）。
- 前端处置：
  - 不主动倒计时 UI；
  - 在 PUT 失败且响应表明签名过期时，自动**对同一文件重新 presign + PUT**（最多 1 次），仍失败 toast 提示用户重试上传；
  - 失败的旧 `uploadItemId` 由后端清理任务处理，前端不调清理接口。

### R-05【P1 / 前端】大文件上传进度

- 现象：本期后端**移除了 multipart 字段**（测试报告"断点续传残留"项 `upload_columns_no_multipart=0`），即只走单 PUT。
- 影响：大文件无分片，上传进度依赖 XHR `progress` 事件；网络中断无法续传。
- 前端处置：
  - 上传组件用 axios `onUploadProgress` 或原生 XHR `progress` 事件展示进度；
  - 用户主动取消 / 离开页面时 abort 当前 PUT，提示"已取消"；
  - 单文件大小硬上限沿用现有 `MAX_FILE_SIZE_BYTES`（默认 10MB，按 Figma 文案；Architect 与设计核对最终上限）；
  - 文件数硬上限沿用现有 `MAX_FILE_COUNT`（默认 50）；
  - **不实现分片续传**（已与后端口径一致）。

### R-06【P1 / 跨域】邮箱为空失败

- 现象（测试报告 §16 通过）：AI 回调 `email=""` → `analysisStatus=2`、`failureReason="邮箱为空"`。
- 影响：候选人无法进入平台管理 → HR 看不到该简历。
- 前端处置：
  - 上传明细列表"分析失败"子 Tab 直接展示 `failureReason`，无需特判文案；
  - 不提供"补填邮箱后重试"功能（PRD 未要求，本期不做）；
  - 仅在 UI 上引导 HR"删除并重新上传含邮箱版本"。

### R-07【P1 / 业务】邀请次数 3 次限制

- 现象（PRD §6.6）：`inviteCount` 累计跨撤回，上限 3。
- 影响：HR 撤回后再发邀请 → `inviteCount` 不重置；用户体验上易误以为"还能再发"。
- 前端处置：
  - 邀请按钮始终展示 `inviteCount/maxInviteCount`（如 `1/3`）；
  - `inviteCount >= 3` 时按钮 disabled + tooltip："邀请次数已达上限"；
  - 撤回 toast 提示"已撤回，剩余 X 次"，引导 HR 谨慎重发。

### R-08【P1 / 业务】已注册不可撤回 / 重发

- 现象（PRD §3.10 / §3.9）：`inviteStatus=2 已注册` 时撤回 / 重发被后端拒绝。
- 影响：UI 必须按状态隐藏按钮，否则用户点击后看到的是统一业务错误 toast，不友好。
- 前端处置：
  - 按"操作矩阵"显隐；
  - 仍以后端为权威（兜底）。

### R-09【P0 / 前端】数字字段 string 兼容

- 现象（测试报告大量返回）：
  - 分页 `current / size / pages / total` 为 string；
  - 上传字段 `fileSize / inviteCount`（在 invite 接口响应中是 number）；
  - 列表 `matchScore`（number）；
  - 但 `upload/stat` 返回三字段全部 string；
  - Long ID（`uploadItemId / talentResumeId / jobId / aiTaskId`）全为 string。
- 影响：直接 `Number()` 会丢精度 / NaN；分页计算与列表渲染会出错。
- 前端处置：
  - DTO 类型用 `number | string | null` 联合类型；
  - mapper 内 normalize：分页字段统一转 number（只用于 Pagination 组件，绝不参与 ID 拼接）；ID 字段统一 `String(id)`；`matchScore` / `fileSize` 在展示时转 number 但保留 string 字段以便回显原值；
  - 严禁组件直接消费 raw response。

### R-10【P2 / 跨域】邮件到达需人工确认

- 现象（测试报告 §"最终汇总"）：mail_logs 仅证明 SMTP 回写，不证明收件箱真实到达。
- 影响：邀请成功 toast 不代表候选人能收到邮件；HR 误以为"已发出 = 已送达"。
- 前端处置：
  - 邀请 / 重发成功 toast 文案明确："邀请邮件已提交发送，候选人可能需要几分钟才能收到"；
  - 不实现邮件投递追踪（本期不做，PRD §3 不做范围）。

### R-11【P1 / 业务】职位绑定与分析的强依赖

- 现象（PRD §3.3）：发起 AI 分析前必须选择绑定岗位；岗位描述/JD 作为 AI 入参。
- 影响：未绑定岗位的明细点击"分析"会被后端拒绝。
- 前端处置：
  - 上传明细未绑定岗位时，"分析"按钮 disabled + tooltip："请先绑定职位"；
  - "重新分析"同规则；
  - 多选批量分析时，过滤未绑定职位的明细，并在 modal 中明示"X 条因未绑定职位将跳过"。

## Open Questions

### OQ-01 接口路径与 `services/axiosConfig.ts` baseURL 拼接

- 现象：测试报告 URL 含 `/api/v1`，但 PRD 文档写 `/talent/resume/...`。
- 待确认：项目现有 `services/axiosConfig.ts` 的 `baseURL` 是否已包含 `/api/v1`？
- 建议：Architect 在 file-change-plan 中确认前端 service 函数应写 `/hire/talent/resume/...` 还是 `/api/v1/hire/talent/resume/...`。

### OQ-02 上传明细列表轮询策略

- 现象：测试报告未涉及前端轮询；PRD §3.6 称"前端可轮询展示进度"。
- 待确认：分析中状态由"用户手动刷新"或"SWR refreshInterval"或"指数退避"驱动？
- 建议：Architect 决定具体策略；不引入 WebSocket / SSE（本期不做）。

### OQ-03 详情接口 `attachment.previewUrl` 与 `downloadUrl` 是否走同一 COS 直链

- 现象（测试报告 §19）：两者实测为同一 URL；PRD §3.3 期望支持预览失败 fallback 下载。
- 待确认：是否需要前端额外封装"预览失败检测"逻辑？或后端将来会拆分两个 URL？
- 建议：本期前端按"先 iframe / object 预览，失败提示用户下载"实现；Architect 在 file-change-plan 中确认 fallback 实现细节。

### OQ-04 上传请求 `jobId` 字段类型

- 现象（测试报告 §1）：`jobId` 入参传 number；§12 `bind-job` 入参 `jobId` 也是 number；其他接口（如 platform list）请求 `jobId` 可为 number 或 string。
- 待确认：前端发起请求时统一传 number 还是 string？
- 建议（与"Long ID 全程 string"规则可能冲突）：
  - 选项 A：所有请求字段统一 string（更符合现有 `07-type-id-field-convention.rule.mdc`）；
  - 选项 B：仅请求体保持 number（与测试报告一致）。
- **PM 倾向 A**，等 Architect 拍板并写入 file-change-plan。

### OQ-05 `task.md` 标题 "Pilot task" 与实际需求不一致

- 现象：当前 `task.md` 仍为占位"Pilot task"，但本次实际需求是"平台管理与批量简历上传前端需求"。
- 规则：PM 不能改 `task.md`；只有 Controller 可以；且 `task.md` 创建后原则上不再变更。
- 建议：Controller 在 Architect 接手前以 message 形式确认是否复用本 task slot；不影响 PM 阶段产出。

### OQ-06 分析触发后的乐观更新

- 现象：调 `/analyze` 成功后立即将 `analysisStatus=1`。
- 待确认：是按返回 `items[]` 单条更新 SWR 缓存，还是直接 mutate 拉新页？
- 建议：Architect 收敛为"单条乐观更新 + 同时 mutate 上传统计"，避免长列表重抓取。

### OQ-07 mock 数据是否在 dev 引入

- 现象：测试报告 AI 提交 SKIP，本地开发若无法触发分析中→成功状态，开发自测困难。
- 待确认：是否允许在 dev 环境注入 fixture（仅当 `process.env.NEXT_PUBLIC_ENABLE_AI_MOCK=1`）？
- 建议：Architect 决策；如允许，必须确保 prod build 不含 mock 路径。

## 严禁前端绕过

- 严禁前端篡改后端字段类型、修改后端接口契约。
- 严禁前端隐藏后端业务错误 toast；只能在 UI 上前置 disabled 减少错误率。
- 严禁前端为 R-01 后端 bug 写"假装写入成功"的补偿逻辑。
