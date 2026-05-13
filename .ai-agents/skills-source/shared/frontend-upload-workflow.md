# Frontend Upload Workflow（上传链路）

> 单一事实源。Prompt 涉及上传 / presign / COS / 大文件 / AI 分析时引用。

## 正确链路

```text
1. presign（业务后端）
   → 返回 { uploadItemId, cosKey, uploadUrl, expiresIn, ... }

2. PUT uploadUrl（直传 COS / S3，绝对 URL）
   → 不走业务 axios baseURL
   → headers 按 presign 返回的 contentType 设置
   → 成功后拿到 ETag（可选）

3. confirm（业务后端）
   → 上报 uploadItemId / etag / size
   → 后端将 uploadStatus 置 1（已上传）
   → analysisStatus 默认 0（未分析）

4. 用户主动点击 analyze（或自动触发，看产品定义）
   → analysisStatus 置 1（分析中）

5. AI 回调（后端推 / 前端轮询）
   → 成功：analysisStatus = 2，写 result
   → 失败：analysisStatus = 3，写 failureReason
```

## 常见 Bug 速查

| 现象 | 根因 | 排查点 |
|---|---|---|
| `PUT /buser/undefined` 或 `uploadUrl undefined` | presign 没 unwrap 或字段名错 | service unwrap、type 字段对齐、mapper 是否吞字段 |
| PUT 走了业务 axios baseURL | 用了业务 axios 实例 PUT 绝对 URL | 上传必须用独立 `axios.create()` 或 `fetch`，不带 baseURL |
| confirm 后**自动**进入"分析中" | 后端在 confirm 后自动调起 analyze，或前端在 confirm 成功回调里调了 analyze | 看后端 confirm 实现 + 前端 confirm 成功 handler，按产品定义裁剪 |
| analysisStatus 显示错 | mapper 把数字状态映射到错误的 Tab key / 文案 | mapper unit 测、Tab key 与 status 枚举对齐 |
| failureReason 是上次失败的残留 | 前端用本地 state 缓存 failureReason，没在重试时清掉 | 重试入口 reset 本地态，统一从后端读 |
| ETag 缺失导致 confirm 失败 | PUT 响应 header 没暴露（CORS `Access-Control-Expose-Headers`） | 后端配置 / 改用 size + cosKey 校验 |
| 重复上传 | upload button disable 时机晚 / 状态机没锁 | `canUpload` 派生字段，按 uploadStatus + analysisStatus 收口 |
| 进度条不动 | 用 axios 但没 onUploadProgress / 用 fetch 不支持 progress | 上传用 XHR 或 axios + onUploadProgress |

## 状态枚举建议（生成 Prompt 时要求确认）

```text
uploadStatus:    0=未上传   1=已上传   2=已失败
analysisStatus:  0=未开始   1=分析中   2=成功     3=失败
```

**Prompt 必须要求**：
- 与后端核对枚举值（生产历史可能有 4=已取消 / 5=已撤回 等）
- 数字状态在 mapper 映射为业务 enum，组件不直接消费数字

## Prompt 引用片段

涉及上传任务时，Prompt 「执行要求」段贴：

```text
上传链路 + 常见 bug：<see: shared/frontend-upload-workflow.md>
关键约束：
- presign 必须 unwrap 后拿到 uploadUrl
- PUT 必须用独立 axios / fetch，不走业务 baseURL
- confirm 后是否自动 analyze 必须显式定义（不能默认行为）
- analysisStatus 必须经 mapper 映射为业务 enum
- 重试时清本地 failureReason
```
