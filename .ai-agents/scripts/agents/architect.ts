#!/usr/bin/env tsx
// Architect Agent — 快捷入口
// Usage: tsx agents/architect.ts [--model <id>] "<技术方案描述>"
import { execFileSync } from "node:child_process";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const runner = path.join(__dirname, "../run-agent.ts");
const args = process.argv.slice(2);

if (args.length === 0) {
  console.error('Usage: tsx agents/architect.ts [--model <id>] "<技术方案描述>"');
  process.exit(1);
}

execFileSync("npx", ["tsx", runner, "architect", ...args], { stdio: "inherit" });
