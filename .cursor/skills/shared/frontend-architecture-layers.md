# Frontend Architecture Layers（分层规范）

> 单一事实源。Prompt 模板用 `<see: shared/frontend-architecture-layers.md>` 引用，不重复写。

## 分层职责

| 层 | 路径 | 只做 | 不做 |
|---|---|---|---|
| **page** | `app/**/page.tsx` | 路由挂载、SEO meta、页面级 Provider | 业务状态、请求、submit |
| **container / page component** | `app/**/_components/**` 或 `components/pages/**` | 组装聚合 hook + 子组件 + 布局 | 直接请求接口、直接消费 raw response |
| **聚合 hook** | `hooks/use<Page>Page.ts` | 编排 base hook、SWR、handlers、UI state（modal/submitting） | HTTP 调用、normalize、组件渲染 |
| **base hook** | `hooks/<feature>/base/use*.ts` | 单一能力封装（一个接口 / 一个状态机分支） | 组合多个能力、UI 状态 |
| **service** | `services/**.ts` | HTTP 调用 + 类型化返回（DTO） | toast、normalize、UI 副作用 |
| **mapper** | `hooks/<feature>/mappers.ts` 或 `mappers/**.ts` | raw DTO → ViewModel；生成 `canXxx` 派生字段 | HTTP、UI、副作用 |
| **payload builder** | `hooks/<feature>/payloads.ts` 或 `payloads/**.ts` | UI 输入 → request body；统一 trim/默认值/字段补齐 | HTTP、normalize response |
| **types** | `types/**.ts` 或 `services/**/types.ts` | DTO（容忍 `string \| number \| null`）、ViewModel（稳定类型）、Payload | 实现逻辑 |
| **component** | `components/**` | 只消费 ViewModel + callbacks；纯渲染 | 请求、normalize、业务状态判断 |

## DTO vs ViewModel

| | DTO | ViewModel |
|---|---|---|
| 来源 | 后端 raw response | mapper 输出 |
| 类型严格度 | 容忍 `string \| number \| null` | 严格、稳定 |
| Long ID | 可能 `string \| number` | **必须 string** |
| 业务派生字段（canXxx） | 无 | 必须有 |
| 组件可直接消费 | ❌ | ✅ |

## 错误处理职责

| 层 | toast | console.error | throw |
|---|---|---|---|
| service | ❌ | ❌ | ✅（HTTP 错误） |
| mapper | ❌ | ⚠️（解析失败）  | ⚠️（仅 schema 严重不符） |
| base hook | ❌ | ❌ | ✅（向上抛） |
| 聚合 hook | ✅（业务 toast） | ⚠️（仅本地兜底） | ❌（必须捕获） |
| component | ❌（除非纯本地校验） | ❌ | ❌ |
| 全局 axios 拦截器 | ✅（resCode 业务错） | — | ✅ |

**铁律**：业务错误一次 toast；service / 拦截器 / hook / page **不要重复 toast**。

## 实施顺序（生成 Prompt 时建议的 Phase）

1. types（DTO / ViewModel / Payload）
2. service
3. mapper + payload builder
4. base hook
5. 聚合 hook
6. component（自下而上接入）
7. page 编排
8. 联调验证

## Prompt 引用片段

模板里贴这段就够：

```text
分层与职责：见 <see: shared/frontend-architecture-layers.md>
关键约束：
- service 只做 HTTP
- DTO 与 ViewModel 分离
- mapper 统一 normalize + 生成 canXxx
- payload builder 统一生成 request body
- component 只消费 ViewModel + callbacks
- 业务 toast 一次，不重复
- Long ID 全链路 string
```
