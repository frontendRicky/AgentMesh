import type { CurrentStatus, TaskState } from "./state-reader.js";

export type NextAction =
  | { type: "run_agent"; agent: "pm" | "architect" | "developer" | "qa"; reason: string }
  | { type: "run_controller_advance"; reason: string }
  | { type: "pause_human_review"; reviewType: "architect_review" | "final_review"; reason: string }
  | { type: "pause_blocked"; reason: string }
  | { type: "completed"; reason: string }
  | { type: "cancelled"; reason: string };

/**
 * 根据当前 state 决定下一步要做什么。
 *
 * 规则：
 * - *_processing：召唤对应专业 Agent
 * - *_completed：召唤 Controller 推进
 * - created：召唤 Controller 推进到 pm_processing
 * - human_review_required / final_review_required：暂停等用户
 * - blocked：暂停等人工裁决
 * - completed / cancelled：终止
 */
export function pickNextAction(state: TaskState): NextAction {
  const status: CurrentStatus = state.current_status;

  switch (status) {
    case "created":
      return { type: "run_controller_advance", reason: "Task 刚创建，推进到 pm_processing" };

    case "pm_processing":
      return { type: "run_agent", agent: "pm", reason: "PM 阶段，召唤 Product Manager Agent" };

    case "pm_completed":
      return { type: "run_controller_advance", reason: "PM 完成，推进到 architect_processing" };

    case "architect_processing":
      return { type: "run_agent", agent: "architect", reason: "Architect 阶段，召唤 Architect Agent" };

    case "architect_completed":
      return { type: "run_controller_advance", reason: "Architect 完成，推进到 human_review_required" };

    case "human_review_required":
      return {
        type: "pause_human_review",
        reviewType: "architect_review",
        reason: "等待 Human Review Actor 审核 Architect 产出",
      };

    case "developer_processing":
      return { type: "run_agent", agent: "developer", reason: "Developer 阶段，召唤 Developer Agent" };

    case "developer_completed":
      return { type: "run_controller_advance", reason: "Developer 完成，推进到 qa_processing" };

    case "qa_processing":
      return { type: "run_agent", agent: "qa", reason: "QA 阶段，召唤 QA Tester Agent" };

    case "qa_completed":
      return { type: "run_controller_advance", reason: "QA 完成，推进到 final_review_required" };

    case "final_review_required":
      return {
        type: "pause_human_review",
        reviewType: "final_review",
        reason: "等待 Human Review Actor 终审",
      };

    case "blocked":
      return { type: "pause_blocked", reason: "出现 Blocker，等待人工裁决" };

    case "completed":
      return { type: "completed", reason: "任务已完成" };

    case "cancelled":
      return { type: "cancelled", reason: "任务已取消" };

    default:
      throw new Error(`pickNextAction: 未知的 current_status: ${status}`);
  }
}
