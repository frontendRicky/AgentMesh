#!/usr/bin/env tsx
/**
 * A2A Agent Runner
 *
 * Usage:
 *   CURSOR_API_KEY=cursor_xxx tsx run-agent.ts <agent> "<prompt>"
 *
 * Agents: pm | architect | developer | qa | controller
 */

import { Agent, CursorAgentError } from "@cursor/sdk";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

import { resolveModelId } from "./lib/model-config.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const AGENT_MAP: Record<string, string> = {
  pm: "product-manager",
  architect: "architect",
  developer: "senior-frontend-developer",
  qa: "qa-tester",
  controller: "flow-controller",
};

const AGENT_DISPLAY: Record<string, string> = {
  pm: "Product Manager Agent",
  architect: "Architect Agent",
  developer: "Senior Frontend Developer Agent",
  qa: "QA Tester Agent",
  controller: "Flow Controller Agent",
};

const AGENT_ROLE_DIR: Record<string, string> = {
  pm: "pm",
  architect: "architect",
  developer: "developer",
  qa: "qa",
  controller: "controller",
};

const CLARIFICATION_INSTRUCTION = `
**🛑 严禁猜测、模糊决策处理规则（必读）**

如果在执行过程中遇到任何不确定、模糊或需要用户拍板的点：

1. **严禁**自行猜测、推测、假设、按"常识"决策
2. 立即在 \`artifacts/<your-role>/clarification-questions.md\` 中追加问题（如不存在则创建，遵循以下 frontmatter 模板）：

\`\`\`yaml
---
status: pending
created_at: <ISO8601>
schema_version: a2a/v1
---

## 待澄清问题

- id: Q-001
  question: <问题原文，越具体越好>
  options:
    - <选项 A>
    - <选项 B>
  default: <你倾向的默认值，可空>
  why_asking: <为什么必须问，不问会怎样>
  blocks_progress: true
  answer: null
\`\`\`

3. 写完 clarification-questions.md 后，**立即停止工作并退出**（不要继续写其他 artifact、不要尝试自己回答）
4. 在对话中明确报告："已写入 clarification-questions.md，等待用户回答"
5. 编排器会暂停流程、引导用户回答，回答后会重新召唤你
6. 你重新启动时优先读 clarification-questions.md 已 answered 的条目，按答案继续

**何时必须用 clarification 而不是猜测：**

- 接口字段语义不清
- 业务流程有多种合理实现
- 设计稿与现有规范冲突
- 性能/UX 权衡需取舍
- 任何"我倾向用 X 但不确定"的判断
`;

function loadAgentDef(agentAlias: string): string {
  const fileName = AGENT_MAP[agentAlias];
  if (!fileName) {
    const valid = Object.keys(AGENT_MAP).join(" | ");
    throw new Error(`Unknown agent "${agentAlias}". Valid: ${valid}`);
  }
  const filePath = path.join(__dirname, "../agents", `${fileName}.agent.md`);
  if (!fs.existsSync(filePath)) {
    throw new Error(`Agent definition not found: ${filePath}`);
  }
  return fs.readFileSync(filePath, "utf-8");
}

function buildPrompt(agentAlias: string, agentDef: string, userPrompt: string): string {
  const displayName = AGENT_DISPLAY[agentAlias];
  const roleDir = AGENT_ROLE_DIR[agentAlias];
  return [
    `你现在以 **${displayName}** 身份运行，处于 A2A 多 Agent 协作系统中。`,
    `严格遵守 .cursor/rules/ai-agents.mdc 与你的 agent.md 中所有的触发条件、禁止行为和产物要求。`,
    ``,
    `以下是你的完整行为定义：`,
    ``,
    `---`,
    agentDef,
    `---`,
    ``,
    CLARIFICATION_INSTRUCTION.replace("<your-role>", roleDir),
    ``,
    `**当前用户/编排器指令：**`,
    userPrompt,
  ].join("\n");
}

export async function runAgent(
  agentAlias: string,
  userPrompt: string,
  options: { projectRoot?: string; apiKey?: string; verbose?: boolean } = {},
): Promise<{ status: string; result?: string }> {
  const apiKey = options.apiKey ?? process.env.CURSOR_API_KEY;
  if (!apiKey) {
    throw new Error("CURSOR_API_KEY 未设置");
  }

  const projectRoot = options.projectRoot ?? path.resolve(__dirname, "../..");
  const agentDef = loadAgentDef(agentAlias);
  const fullPrompt = buildPrompt(agentAlias, agentDef, userPrompt);
  const modelId = await resolveModelId(apiKey);

  if (options.verbose !== false) {
    console.log(`[run-agent] ${AGENT_DISPLAY[agentAlias]} | model=${modelId} | prompt=${fullPrompt.length} chars`);
  }

  const result = await Agent.prompt(fullPrompt, {
    apiKey,
    model: { id: modelId },
    local: { cwd: projectRoot },
  });

  return { status: result.status, result: result.result };
}

async function main() {
  const [, , agentAlias, ...rest] = process.argv;

  if (!agentAlias || agentAlias === "--help" || agentAlias === "-h") {
    console.log(`
A2A Agent Runner

Usage:
  CURSOR_API_KEY=cursor_xxx tsx run-agent.ts <agent> "<prompt>"

Agents:
  pm          产品经理 — 需求分析 / PRD / 任务分解
  architect   架构师   — 技术方案 / file-change-plan / 风险方案
  developer   开发     — 代码实现（双门禁：developer_processing + approved）
  qa          测试     — 测试报告 / 验收清单
  controller  调度器   — Task 创建 / 状态推进 / Blocker 管理
    `);
    process.exit(0);
  }

  const userPrompt = rest.join(" ");
  if (!userPrompt) {
    console.error('Error: prompt is required. Example: tsx run-agent.ts pm "你的需求"');
    process.exit(1);
  }

  try {
    const result = await runAgent(agentAlias, userPrompt);
    console.log(`\n[run-agent] status=${result.status}`);
    if (result.result) {
      console.log("\n--- Agent Output ---\n" + result.result + "\n--- End ---");
    }
    process.exit(result.status === "finished" ? 0 : 2);
  } catch (err) {
    if (err instanceof CursorAgentError) {
      console.error(`[run-agent] Startup failed: ${err.message}, retryable=${err.isRetryable}`);
      process.exit(1);
    }
    console.error(`[run-agent] Error: ${(err as Error).message}`);
    process.exit(1);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
