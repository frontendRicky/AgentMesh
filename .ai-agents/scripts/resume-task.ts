#!/usr/bin/env tsx
/**
 * A2A — 从当前 state 继续编排
 *
 * Usage:
 *   ./resume-task                  # 自动读 active-task.md
 *   ./resume-task T-2026-001       # 显式指定 task_id
 *   ./resume-task --owner zhangxia # 指定默认 reviewer
 */

import * as fs from "node:fs";

import { stateFile } from "./lib/paths.js";
import { readActiveTaskId, readState } from "./lib/state-reader.js";
import { banner, error, info, printState } from "./lib/terminal-ui.js";
import { orchestrate } from "./orchestrator.js";

async function main() {
  const apiKey = process.env.CURSOR_API_KEY;
  if (!apiKey) {
    console.error("Error: CURSOR_API_KEY 未设置");
    process.exit(1);
  }

  const args = process.argv.slice(2);
  const owner = pickArg(args, "--owner") ?? "zhangxia";
  const explicit = args.find((a) => /^T-\d{4}-\d{3}$/.test(a));

  let taskId: string | null = explicit ?? readActiveTaskId();

  if (!taskId) {
    error("未指定 task_id，且 active-task.md 中 active_task_id == null");
    error("用法：./resume-task T-2026-001");
    process.exit(1);
  }

  if (!/^T-\d{4}-\d{3}$/.test(taskId)) {
    error(`task_id "${taskId}" 不符合 ^T-\\d{4}-\\d{3}$，拒绝继续`);
    process.exit(1);
  }

  if (!fs.existsSync(stateFile(taskId))) {
    error(`state.md 不存在：${stateFile(taskId)}`);
    process.exit(1);
  }

  banner(`A2A — Resume Task: ${taskId}`);

  const state = readState(taskId);
  info(`从当前 state 继续编排：`);
  printState(state);

  await orchestrate(taskId, { apiKey, defaultReviewer: owner });
}

function pickArg(args: string[], flag: string): string | undefined {
  const idx = args.indexOf(flag);
  if (idx === -1 || idx === args.length - 1) return undefined;
  return args[idx + 1];
}

main().catch((err) => {
  console.error("resume-task failed:", err);
  process.exit(1);
});
