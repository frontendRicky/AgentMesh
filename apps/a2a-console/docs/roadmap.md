# Roadmap

## 已落地（ST-01 + ST-02 / 本轮）

- monorepo 骨架（apps/a2a-console workspaces）
- 11 GET + 1 POST API
- path-guard / file-size-guard / frontmatter 解析
- token / context 估算 service
- model-overrides.md 解析
- Client hello world + 健康检查

## 下一轮（ST-03 ~ ST-09）

- ST-03 Client 基础（路由 / AppLayout / Settings 页 / Zustand store）
- ST-04 Dashboard + Tasks 列表
- ST-05 Task Detail Overview + Agent Chat + Timeline
- ST-06 Artifacts MD 预览
- ST-07 Metrics + Blockers
- ST-08 Model & Prompt
- ST-09 文档完善 + 验收回归

## P2（不进 MVP）

- Artifact diff（PRD §11.6）
- Reroute / Patch round 切换器（PRD §11.4）
- 状态冲突检测（PRD §11.3）
- 风险雷达（PRD §11.2）
- 一键生成完整 Prompt（PRD §11.1）
- 成本预算提醒（PRD §11.9）
- Runbook / SOP 面板（PRD §11.10）

## P3

- 真正调用 LLM
- 自动推进 state
- 在线多人协作
- 远程部署
- 鉴权
- WebSocket 实时刷新
- chokidar 文件监听
