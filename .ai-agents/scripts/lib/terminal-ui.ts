import chalk from "chalk";

import type { TaskState } from "./state-reader.js";

export function banner(text: string): void {
  const line = "─".repeat(Math.max(40, text.length + 4));
  console.log("\n" + chalk.cyan(line));
  console.log(chalk.cyan.bold("  " + text));
  console.log(chalk.cyan(line) + "\n");
}

export function info(text: string): void {
  console.log(chalk.gray("[orchestrator] ") + text);
}

export function step(text: string): void {
  console.log(chalk.blue("→ ") + text);
}

export function success(text: string): void {
  console.log(chalk.green("✓ ") + text);
}

export function warn(text: string): void {
  console.log(chalk.yellow("⚠ ") + text);
}

export function error(text: string): void {
  console.log(chalk.red("✗ ") + text);
}

export function pause(text: string): void {
  console.log(chalk.magenta.bold("⏸ ") + chalk.magenta(text));
}

export function printState(state: TaskState): void {
  const items = [
    ["task_id", state.task_id],
    ["current_status", colorStatus(state.current_status)],
    ["current_agent", state.current_agent],
    ["next_agent", state.next_agent ?? "-"],
    ["human_review_status", colorReview(state.human_review_status)],
    ["final_review_status", colorReview(state.final_review_status)],
    ["active_blocker", state.active_blocker ?? "-"],
    ["updated_at", state.updated_at],
  ];

  console.log(chalk.gray("┌─── State " + "─".repeat(50)));
  for (const [k, v] of items) {
    console.log(chalk.gray("│ ") + chalk.dim(k.padEnd(22)) + " " + v);
  }
  console.log(chalk.gray("└" + "─".repeat(60)));
}

function colorStatus(status: string): string {
  if (status === "completed") return chalk.green.bold(status);
  if (status === "blocked" || status === "cancelled") return chalk.red.bold(status);
  if (status.endsWith("_review_required")) return chalk.magenta.bold(status);
  if (status.endsWith("_processing")) return chalk.yellow(status);
  if (status.endsWith("_completed")) return chalk.cyan(status);
  return status;
}

function colorReview(s: string): string {
  if (s === "approved") return chalk.green(s);
  if (s === "rejected" || s === "needs_changes") return chalk.red(s);
  if (s === "pending") return chalk.yellow(s);
  return chalk.dim(s);
}
