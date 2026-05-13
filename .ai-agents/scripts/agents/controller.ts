#!/usr/bin/env tsx
// Flow Controller Agent — 快捷入口
// Usage: tsx agents/controller.ts "<调度指令>"
import { execFileSync } from "node:child_process";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const runner = path.join(__dirname, "../run-agent.ts");
const prompt = process.argv.slice(2).join(" ");

if (!prompt) {
  console.error('Usage: tsx agents/controller.ts "<调度指令>"');
  process.exit(1);
}

execFileSync("npx", ["tsx", runner, "controller", prompt], { stdio: "inherit" });
