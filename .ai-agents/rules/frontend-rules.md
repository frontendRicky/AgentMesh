# Frontend Rules — 前端通用规范

> 不绑定具体技术栈（React / Vue / Svelte 都适用），通用前端工程规范。项目接入时可在 `rules/stack-<框架>.md` 扩展具体栈规范。

## 1. 组件规范

- 单一职责：一个组件只解决一类问题；超过 3 个明显职责应拆分
- 命名：PascalCase（如 `UserSettingsPanel`）；测试文件 `<Name>.test.<ext>`
- 文件位置：按 feature/domain 组织（如 `components/settings/`），避免按 type 平铺
- props：保持窄接口，**禁止**传整个 Object 进去；可拆为多个具名 props
- 默认导出 vs 命名导出：组件文件默认导出主组件，子组件命名导出
- 组件层不直接发起请求（应通过 hook / service）
- 组件层不直接读 / 写全局状态（应通过 hook）

## 2. Hooks 规范

- 命名：`useXxx`
- 单一职责：一个 hook 只封装一类逻辑（数据请求 / 状态机 / 副作用 / 表单 / ...）
- 返回值：建议返回稳定的对象或元组，避免每次返回新引用导致下游重渲染
- 副作用收敛在 hook 内；组件层不直接 useEffect 做业务请求
- 命名空间：业务 hook 放 `hooks/` 或 `features/<feature>/hooks/`

## 3. Utils 规范

- 纯函数优先：utils 不依赖 framework 上下文（如 React Context）
- 命名：camelCase（如 `formatCurrency`）
- 单测覆盖：utils 优先级最高，应有单测
- 不在 utils 里做请求 / 副作用 / DOM 操作

## 4. Types 规范

- 严格 TypeScript：禁止 `any` 进入正式逻辑（必要时用 `unknown` + 收窄）
- 公共类型放 `types/`；私有类型放使用方文件
- 接口契约类型与后端 API 一一对应（`types/api/*.ts`）
- 枚举优先用字面量联合类型（`type Theme = 'light' | 'dark'`），减少运行时开销

## 5. API Service 规范

- 所有请求收敛到 `services/`，不在组件 / hook 中直接 fetch
- 每个接口一个具名导出函数，含完整请求 / 响应类型
- 错误码统一处理（建议 axios interceptor / fetch wrapper）
- 4xx 与 5xx 区分处理：4xx 多为业务可预期；5xx 应给降级
- 重试策略显式声明（不在 service 内偷偷重试）
- mock 数据**不允许**出现在正式逻辑中（仅 dev 环境 / 测试夹具中）

## 6. 状态管理规范

- 优先**就近放**：先尝试组件内 useState；不行再放 hook 共享；最后才上全局
- 全局状态需经评审（在 tech-plan 中说明为什么必须全局）
- 状态命名清晰：`isLoading` / `error` / `data` 是常见三件套
- 派生状态用 useMemo / computed，不应在 useEffect 中同步
- 服务端状态与本地状态分离（建议 React Query / SWR 类工具）

## 7. 路由规范

- 路由声明集中（如 `routes.ts`），不在多处零散定义
- 路由守卫统一（认证 / 权限 / 重定向）
- 路由参数有类型定义
- 不在 layout 中做业务请求；通过 loader / preload 抽离

## 8. 权限规范

- 5 层覆盖：菜单 / 路由 / 按钮 / 接口 / 数据
- 前端权限**仅是 UX**，不是安全；接口层必须兜底
- 角色 → 权限映射不写死前端代码；通过配置 / 后端返回
- 权限组件统一（如 `<Authorized>` 或 `usePermission`）

## 9. 错误处理规范

- 全局错误边界（如 React `<ErrorBoundary>`）
- 接口错误统一展示位（toast / banner / inline）
- 不要把 `try/catch` 吞掉错误（必须打 log 或上报）
- 业务错误与技术错误区分文案
- error 状态必须有"重试"或"返回"动作

## 10. loading / empty / error 状态规范

四态显式：

- **loading**：骨架屏 / spinner，避免长时间空白
- **empty**：友好文案 + 引导动作（如"创建第一个 X"）
- **error**：错误信息 + 重试动作
- **success**：正常渲染数据

每个数据展示组件必须显式处理上述四态，不能"看起来不会失败就不写"。

## 11. 性能规范

- 列表渲染稳定 key（不要用 index 作 key）
- 图片懒加载 + 适当尺寸（避免加载原图）
- 避免不必要的 re-render（用 React.memo / useMemo / useCallback 等）
- 大量数据分页 / 虚拟滚动
- 避免在 render 中做计算密集（应用 useMemo）

## 12. 可访问性（a11y）

- 语义化 HTML（不要全 div）
- 交互元素键盘可用
- 图片有 alt
- 表单字段有 label
- 错误提示对屏幕阅读器友好

## 13. 项目接入扩展

如需绑定具体栈规范，新建：
- `rules/stack-react-nextjs.md`
- `rules/stack-vue3.md`
- `rules/stack-svelte.md`
- ...

不要修改本文件去绑定具体栈。
