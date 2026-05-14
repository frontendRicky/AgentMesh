#!/usr/bin/env tsx
/**
 * A2A — 新建并启动一个 Task
 *
 * Usage:
 *   ./start-task                          # 进入交互式输入
 *   ./start-task "需求描述"               # 用默认 feature / P2 / zhangxia 启动
 *   ./start-task --type bugfix "..."      # 指定 task_type
 *
 * 流程：
 *   1. 终端收集 task_type / title / priority / owner / 原始需求
 *   2. 召唤 Controller 创建 task.md / state.md / active-task.md / 001 handoff message
 *   3. 进入主编排循环
 */

import { input, select } from "@inquirer/prompts";

import { AGENT_ALIASES, type AgentAlias } from "./agents-model.config.js";
import { invokeControllerCreateTask } from "./lib/controller-invoker.js";
import { readActiveTaskId } from "./lib/state-reader.js";
import { banner, info, error, success } from "./lib/terminal-ui.js";
import { orchestrate } from "./orchestrator.js";

async function main() {
  const apiKey = process.env.CURSOR_API_KEY;
  if (!apiKey) {
    console.error("Error: CURSOR_API_KEY 未设置");
    console.error("  export CURSOR_API_KEY=cursor_your_api_key_here");
    process.exit(1);
  }

  const args = process.argv.slice(2);
  const inlineType = pickArg(args, "--type");
  const inlinePriority = pickArg(args, "--priority");
  const inlineOwner = pickArg(args, "--owner");
  const inlineTitle = pickArg(args, "--title");
  const modelOverrides = pickModelOverrides(args);
  const positional = stripFlagsAndValues(args).join(" ");

  banner("A2A — Start New Task");

  const taskType =
    inlineType ??
    ((await select({
      message: "task_type：",
      choices: [
        { name: "feature — 新功能", value: "feature" },
        { name: "bugfix — Bug 修复", value: "bugfix" },
        { name: "refactor — 重构", value: "refactor" },
        { name: "permission — 权限改造", value: "permission" },
        { name: "api-integration — 接口对接", value: "api-integration" },
        { name: "ui-redesign — UI 重做", value: "ui-redesign" },
      ],
    })) as string);

  const rawRequirement = positional || (await input({
    message: "原始需求（一句话或多句，详细越好）：",
  }));

  const taskTitle =
    inlineTitle ??
    (await input({
      message: "task_title（一句话标题）：",
      default: rawRequirement.slice(0, 60),
    }));

  const priority =
    inlinePriority ??
    ((await select({
      message: "priority：",
      choices: [
        { name: "P0 — 紧急", value: "P0" },
        { name: "P1 — 高", value: "P1" },
        { name: "P2 — 中（默认）", value: "P2" },
        { name: "P3 — 低", value: "P3" },
      ],
      default: "P2",
    })) as string);

  const humanOwner =
    inlineOwner ??
    (await input({
      message: "human_owner（你的 handle）：",
      default: "zhangxia",
    }));

  info(`即将创建 Task：${taskTitle} (${taskType}, ${priority}, owner=${humanOwner})`);

  await invokeControllerCreateTask({
    taskType,
    taskTitle,
    priority,
    humanOwner,
    rawRequirement,
    apiKey,
    modelOverride: modelOverrides.controller,
  });

  const newTaskId = readActiveTaskId();
  if (!newTaskId) {
    error("Controller 未成功更新 active-task.md，请检查 Controller 输出");
    process.exit(1);
  }

  success(`新 Task 已创建：${newTaskId}`);
  banner(`开始编排：${newTaskId}`);

  await orchestrate(newTaskId, {
    apiKey,
    defaultReviewer: humanOwner,
    modelOverrides,
  });
}

function pickArg(args: string[], flag: string): string | undefined {
  const idx = args.indexOf(flag);
  if (idx === -1 || idx === args.length - 1) return undefined;
  return args[idx + 1];
}

const KNOWN_VALUE_FLAGS = new Set<string>([
  "--type",
  "--priority",
  "--owner",
  "--title",
  ...AGENT_ALIASES.map((a) => `--model-${a}`),
]);

/**
 * 从 argv 中剥离所有"带值 flag + 它们的值"以及 boolean flag，
 * 剩下的纯位置参数即原始需求文本。
 */
function stripFlagsAndValues(args: string[]): string[] {
  const out: string[] = [];
  for (let i = 0; i < args.length; i += 1) {
    const a = args[i];
    if (a.includes("=") && a.startsWith("--")) continue;
    if (KNOWN_VALUE_FLAGS.has(a)) {
      i += 1;
      continue;
    }
    if (a.startsWith("--")) continue;
    out.push(a);
  }
  return out;
}

function pickModelOverrides(args: string[]): Partial<Record<AgentAlias, string>> {
  const out: Partial<Record<AgentAlias, string>> = {};
  for (const alias of AGENT_ALIASES) {
    const flag = `--model-${alias}`;
    const fromSpace = pickArg(args, flag);
    const eqMatch = args.find((a) => a.startsWith(`${flag}=`));
    const value = fromSpace ?? (eqMatch ? eqMatch.slice(flag.length + 1) : undefined);
    if (value && value.trim()) out[alias] = value.trim();
  }
  return out;
}

main().catch((err) => {
  console.error("start-task failed:", err);
  process.exit(1);
});
