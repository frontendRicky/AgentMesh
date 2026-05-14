#!/usr/bin/env tsx
// Senior Frontend Developer Agent — 快捷入口
// Usage: tsx agents/developer.ts [--model <id>] "<实现任务描述>"
import { execFileSync } from "node:child_process";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const runner = path.join(__dirname, "../run-agent.ts");
const args = process.argv.slice(2);

if (args.length === 0) {
  console.error('Usage: tsx agents/developer.ts [--model <id>] "<实现任务描述>"');
  process.exit(1);
}

execFileSync("npx", ["tsx", runner, "developer", ...args], { stdio: "inherit" });
