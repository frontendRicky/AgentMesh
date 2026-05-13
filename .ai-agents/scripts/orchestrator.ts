#!/usr/bin/env tsx
/**
 * A2A Orchestrator — 主编排循环
 *
 * 流程：
 *   loop:
 *     1. 读 state.md
 *     2. 检测 clarification-questions.md（需用户在 Cursor 聊天窗回答）→ 暂停
 *     3. 终止态 → 退出
 *     4. 暂停态（human_review_required / final_review_required / blocked）→ 进入对应交互
 *     5. 否则按 next-agent-picker 决定下一步：跑专业 Agent 或 Controller 推进
 *     6. 跑完后回到 loop
 */

import { confirm } from "@inquirer/prompts";
import chalk from "chalk";
import * as fs from "node:fs";
import * as path from "node:path";

import { runAgent } from "./run-agent.js";

import { detectPendingClarifications } from "./lib/clarification-detector.js";
import {
  invokeControllerAdvance,
  invokeControllerReviewAdvance,
} from "./lib/controller-invoker.js";
import {
  artifactsDir,
  humanReviewsDir,
  messagesDir,
  taskDir,
} from "./lib/paths.js";
import {
  promptClarifications,
  promptReview,
} from "./lib/review-prompter.js";
import { writeReviewRecord } from "./lib/review-writer.js";
import {
  isPauseStatus,
  isTerminalStatus,
  readState,
  readTask,
  type CurrentStatus,
  type TaskState,
} from "./lib/state-reader.js";
import { pickNextAction } from "./lib/next-agent-picker.js";
import {
  banner,
  error,
  info,
  pause,
  printState,
  step,
  success,
  warn,
} from "./lib/terminal-ui.js";

export interface OrchestratorOptions {
  apiKey: string;
  maxLoops?: number;
  defaultReviewer?: string;
}

const DEFAULT_MAX_LOOPS = 60;

export async function orchestrate(taskId: string, options: OrchestratorOptions): Promise<void> {
  const maxLoops = options.maxLoops ?? DEFAULT_MAX_LOOPS;
  let loopCount = 0;
  let lastStatus: CurrentStatus | null = null;
  let consecutiveSameStatus = 0;

  banner(`A2A Orchestrator: ${taskId}`);

  while (loopCount < maxLoops) {
    loopCount += 1;

    let state: TaskState;
    try {
      state = readState(taskId);
    } catch (err) {
      error(`读 state.md 失败：${(err as Error).message}`);
      return;
    }

    info(`Loop ${loopCount}/${maxLoops}`);
    printState(state);

    if (lastStatus === state.current_status) {
      consecutiveSameStatus += 1;
      if (consecutiveSameStatus >= 3) {
        warn(`检测到 state.current_status 连续 ${consecutiveSameStatus} 轮无变化（${state.current_status}），可能 Agent 未推进或卡住，停止循环`);
        const cont = await confirm({ message: "是否继续？（再跑一轮）", default: false });
        if (!cont) return;
        consecutiveSameStatus = 0;
      }
    } else {
      consecutiveSameStatus = 0;
      lastStatus = state.current_status;
    }

    if (isTerminalStatus(state.current_status)) {
      if (state.current_status === "completed") {
        success(`任务 ${taskId} 已完成 ✨`);
      } else {
        warn(`任务 ${taskId} 已取消`);
      }
      return;
    }

    const pendingClarifications = detectPendingClarifications(taskId);
    if (pendingClarifications.length > 0) {
      pause("检测到待澄清问题");

      for (const doc of pendingClarifications) {
        console.log("\n" + chalk.yellow.bold(`📋 ${doc.role.toUpperCase()} 有未回答的澄清问题`));
        console.log(chalk.gray(`  文件：${path.relative(process.cwd(), doc.filePath)}`));
      }

      console.log("\n" + chalk.cyan.bold("请按以下步骤回答："));
      console.log(chalk.gray("  方式 A（推荐）：在 Cursor 聊天窗发送 ↓"));
      console.log(chalk.white.bold(`    回答 ${pendingClarifications.map((d) => d.role).join("/")} 的澄清问题（任务 ${taskId}），逐条问我并把答案写回对应 clarification-questions.md（answer 字段 + status: answered）`));
      console.log(chalk.gray("  方式 B（备选）：直接在本终端逐条回答"));
      console.log();

      const useTerminal = await confirm({
        message: "是否在终端直接回答？（选 N 则去 Cursor 聊天窗回答完后回来按回车）",
        default: false,
      });

      if (useTerminal) {
        for (const doc of pendingClarifications) {
          console.log(chalk.cyan(`\n=== ${doc.role.toUpperCase()} ===`));
          const answers = await promptClarifications(doc);
          if (answers.length > 0) {
            const { writeAnswers } = await import("./lib/clarification-detector.js");
            writeAnswers(doc, answers);
            success(`已写入 ${answers.length} 个答案 → ${path.basename(doc.filePath)}`);
          }
        }
      } else {
        await confirm({ message: "已在 Cursor 中回答完毕？按回车继续", default: true });

        const stillPending = detectPendingClarifications(taskId);
        if (stillPending.length > 0) {
          warn(`仍有 ${stillPending.length} 个角色存在未回答问题，重新进入澄清流程`);
          continue;
        }
      }

      step("重新召唤上一个 Agent 让它读取已答澄清继续工作");
      const lastAgent = inferAgentFromStatus(state.current_status);
      if (lastAgent) {
        await runAgent(lastAgent, `clarification-questions.md 中的问题已被用户回答，请按 answer 字段继续之前未完成的工作；不要重复已经写过的 artifact 内容。当前 Task: ${taskId}`, { apiKey: options.apiKey });
      } else {
        await invokeControllerAdvance(taskId, state, { apiKey: options.apiKey });
      }
      continue;
    }

    const next = pickNextAction(state);
    step(next.reason);

    switch (next.type) {
      case "run_agent":
        try {
          await runAgent(next.agent, `请按你的 agent.md 工作流执行当前阶段任务。当前 Task: ${taskId}`, {
            apiKey: options.apiKey,
          });
          success(`${next.agent} 执行完毕`);
        } catch (err) {
          error(`${next.agent} 执行失败：${(err as Error).message}`);
          const cont = await confirm({ message: "是否继续编排（false=退出）？", default: false });
          if (!cont) return;
        }
        break;

      case "run_controller_advance":
        try {
          await invokeControllerAdvance(taskId, state, { apiKey: options.apiKey });
          success("Controller 推进完毕");
        } catch (err) {
          error(`Controller 执行失败：${(err as Error).message}`);
          const cont = await confirm({ message: "是否继续编排（false=退出）？", default: false });
          if (!cont) return;
        }
        break;

      case "pause_human_review": {
        const reviewedArtifacts = collectReviewableArtifacts(taskId, next.reviewType);
        const result = await handleHumanReview(taskId, next.reviewType, reviewedArtifacts, options);
        if (result === "abort") {
          info("用户选择暂时退出，下次用 ./resume-task 继续");
          return;
        }
        break;
      }

      case "pause_blocked":
        await handleBlocked(taskId, state, options);
        break;

      default:
        warn(`未知 action type，跳过`);
    }
  }

  warn(`已达到 maxLoops=${maxLoops}，编排器停止。下次可用 ./resume-task ${taskId} 继续`);
}

function inferAgentFromStatus(status: CurrentStatus): "pm" | "architect" | "developer" | "qa" | null {
  if (status === "pm_processing") return "pm";
  if (status === "architect_processing") return "architect";
  if (status === "developer_processing") return "developer";
  if (status === "qa_processing") return "qa";
  return null;
}

function collectReviewableArtifacts(
  taskId: string,
  reviewType: "architect_review" | "final_review",
): string[] {
  const role = reviewType === "architect_review" ? "architect" : "qa";
  const dir = artifactsDir(taskId, role);
  if (!fs.existsSync(dir)) return [];

  const artifacts: string[] = [];
  const files = fs.readdirSync(dir).filter((f) => f.endsWith(".md") && f !== "clarification-questions.md");

  for (const file of files) {
    const content = fs.readFileSync(path.join(dir, file), "utf-8");
    const idMatch = content.match(/^artifact_id:\s*(\S+)/m);
    if (idMatch) artifacts.push(idMatch[1]);
  }
  return artifacts;
}

async function handleHumanReview(
  taskId: string,
  reviewType: "architect_review" | "final_review",
  reviewedArtifacts: string[],
  options: OrchestratorOptions,
): Promise<"continue" | "abort"> {
  pause(`等待 Human Review（${reviewType}）`);
  console.log(chalk.gray("\n  待审产物 artifact_ids：" + (reviewedArtifacts.length > 0 ? reviewedArtifacts.join(", ") : "(空 - 请检查 artifacts 目录)")));
  console.log();

  const reviewFile =
    reviewType === "architect_review" ? "architect-review.md" : "final-review.md";
  const existingReviewPath = path.join(humanReviewsDir(taskId), reviewFile);

  if (fs.existsSync(existingReviewPath)) {
    info(`${reviewFile} 已存在`);
    const reuse = await confirm({
      message: `检测到 ${reviewFile} 已存在，是否复用并交给 Controller 推进？（N=重写）`,
      default: true,
    });
    if (reuse) {
      await invokeControllerReviewAdvance(taskId, reviewType, { apiKey: options.apiKey });
      success("Controller 已处理已有 review record");
      return "continue";
    }
  }

  const input = await promptReview({
    reviewType,
    reviewedArtifacts,
    defaultReviewer: options.defaultReviewer ?? "zhangxia",
  });

  if (!input) {
    return "abort";
  }

  const filePath = writeReviewRecord({ taskId, reviewType, reviewedArtifacts, input });
  success(`已写 ${path.relative(process.cwd(), filePath)}`);

  await invokeControllerReviewAdvance(taskId, reviewType, { apiKey: options.apiKey });
  success("Controller 双步推进完毕");
  return "continue";
}

async function handleBlocked(
  taskId: string,
  state: TaskState,
  options: OrchestratorOptions,
): Promise<void> {
  pause(`任务进入 blocked 状态`);
  console.log(chalk.gray(`  active_blocker: ${state.active_blocker ?? "(null)"}`));
  console.log(chalk.gray(`  请前往 .ai-agents/workspace/${taskId}/blockers/ 查看详情`));

  const choice = await confirm({
    message: "已人工处理 Blocker？召唤 Controller 校验恢复",
    default: false,
  });

  if (!choice) {
    info("退出编排器，处理完 Blocker 后用 ./resume-task 继续");
    throw new BlockedAbortError();
  }

  await invokeControllerAdvance(taskId, state, { apiKey: options.apiKey });
  success("Controller 已尝试恢复");
}

class BlockedAbortError extends Error {
  constructor() {
    super("blocked_abort");
    this.name = "BlockedAbortError";
  }
}
