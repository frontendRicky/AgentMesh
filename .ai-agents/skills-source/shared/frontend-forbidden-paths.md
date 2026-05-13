# Frontend Forbidden Paths（默认禁改集 + 例外）

> 单一事实源。所有 Prompt 模板里只引用本文件，不要再各自维护一份。

## 默认禁改

下列文件/目录默认不允许通过 Prompt 让 Agent 修改：

- `package.json`
- `package-lock.json` / `pnpm-lock.yaml` / `yarn.lock`
- `.github/**` / `.gitlab-ci.yml` / `.gitlab/**`
- `Dockerfile` / `docker-compose*.yml`
- `next.config.{js,ts,mjs}`
- `tsconfig.json` / `tsconfig.*.json`
- `axiosConfig.*` / `http/client.*` / 全局请求拦截器
- `middleware.ts` / `middleware.*`
- 全局权限体系 / RBAC / 路由守卫
- 全局主题 / ConfigProvider
- 与本次任务**无关**的页面 / hook / service / component

## 例外条件（escape hatch）

允许触碰禁改文件，**当且仅当**满足以下之一：

1. **用户原话显式批准**："可以改 axiosConfig" / "同意升级依赖" / "允许改 middleware"。Prompt 必须在「目标」段引用该原话。
2. **A2A file-change-plan 中显式声明**：路径 `allowed: yes` 且 `owner: user-approved`。
3. **Human Review verdict = approved** 且 `architect-review.md` 显式列出该路径。

例外生效时，Prompt 仍必须：
- 保留**其他禁改项**不变
- 「修改范围」段单列被解禁文件 + 引用批准来源
- 「验收」段加入"本次解禁的文件未越界"

## blocker-request 触发条件

任一满足时，Prompt 必须要求 Agent **停止修改，输出 blocker-request**：

- 任务实际需要修改禁改集中的文件，但**没有任何例外条件成立**
- 实施中发现 file-change-plan 白名单不覆盖必要文件
- 后端 / 上游契约和现有 file-change-plan 冲突
- 实施中发现需要新增依赖

blocker-request 输出格式（Prompt 末尾要求 Agent 输出这段）：

```md
## blocker-request

- 类型：path-out-of-whitelist | new-dependency | upstream-conflict | other
- 阻塞点：<具体文件 / 依赖 / 冲突>
- 根因：<一句话>
- 建议解决路径：<架构调整 / 用户批准 / 等后端 / 走 A2A>
- 不影响的部分：<已完成的工作>
```

## 不在禁改集内但需要警惕

下列虽不在硬禁改集，但 Prompt 应**默认要求二次确认**：

- 公共 hooks / utils / mappers（被多个页面引用）
- 业务 axios 实例 / API base
- 设计 token / Tailwind config
- 业务状态机 / 流程枚举

要求方式：Prompt 「执行要求」段加一行 "修改前列出影响范围 + 调用方清单"。
