import { runAgent } from "../run-agent.js";
import type { TaskState } from "./state-reader.js";

/**
 * 调用 Flow Controller Agent 执行一次"推进"。
 *
 * Controller 自己读 state.md + 上游产物 + handoff contract，决定下一步：
 * - 推进到下一阶段（写 state.md + 下发 handoff message）
 * - 校验失败 → 创建 Blocker
 * - 中间态 → 启动自检场景 0 自动补做
 */
export async function invokeControllerAdvance(
  taskId: string,
  state: TaskState,
  options: { apiKey?: string } = {},
): Promise<void> {
  const prompt = [
    `当前 Task: ${taskId}`,
    `当前 state.current_status: ${state.current_status}`,
    `请按 .ai-agents/agents/flow-controller.agent.md 的工作流执行：`,
    ``,
    `1. 先跑场景 0（启动自检）：检测是否存在双步流转中间态（human_review_required + approved 或 final_review_required + approved），如有立即补做第 2 步`,
    `2. 校验当前阶段的上游产物（artifacts / messages / review records）是否 ready`,
    `3. 校验通过 → 推进 state.current_status 到合法下一阶段，并写对应 from-controller-<seq>-*.md`,
    `4. 校验失败 → 进入场景 D 创建正式 Blocker，或场景 D' 留痕`,
    ``,
    `严禁写 artifacts/{pm,architect,developer,qa}/、严禁写 human-reviews/、严禁写任何项目源码。`,
    `完成后在对话中明确报告：state.current_status 推进到了什么、写了哪些文件。`,
  ].join("\n");

  await runAgent("controller", prompt, options);
}

/**
 * 调用 Controller 完成"双步审核翻转"的第 2 步。
 * 第 1 步由编排器直接写 state（review record 写完后立即翻 *_status），
 * 第 2 步交给 Controller 推 current_status。
 */
export async function invokeControllerReviewAdvance(
  taskId: string,
  reviewType: "architect_review" | "final_review",
  options: { apiKey?: string } = {},
): Promise<void> {
  const reviewFile =
    reviewType === "architect_review" ? "human-reviews/architect-review.md" : "human-reviews/final-review.md";

  const statusField = reviewType === "architect_review" ? "human_review_status" : "final_review_status";

  const prompt = [
    `当前 Task: ${taskId}`,
    `Human Review Actor 已写入 ${reviewFile}（按 review.schema.md 校验）。`,
    `当前 state.${statusField} 仍是 pending；尚未触发双步翻转。`,
    ``,
    `请按 .ai-agents/agents/flow-controller.agent.md 场景 C 执行**完整的双步翻转**：`,
    ``,
    `第 1 步（独立写入）：`,
    `- 校验 ${reviewFile} 字段完整性：review_id / review_type / verdict / reviewer / reviewed_at / reviewed_artifacts`,
    `- 校验通过 → 翻 state.${statusField} = <verdict>`,
    `- 校验失败 → 进入场景 D 创建 Blocker`,
    ``,
    `第 2 步（独立写入，禁止与第 1 步合并）：`,
    `- 若 verdict == approved：`,
    `  - architect_review → state.current_status = developer_processing, current_agent = developer, next_agent = qa`,
    `  - final_review → state.current_status = completed, current_agent = controller, next_agent = none`,
    `- 若 verdict != approved：`,
    `  - architect_review rejected/needs_changes → state.current_status = architect_processing`,
    `  - final_review rejected/needs_changes → state.current_status = developer_processing`,
    ``,
    `同时写一条 from-controller-<seq>-handoff.md 通知下游。`,
    `若 verdict == approved AND review_type == final_review，进入场景 F 写 artifacts/final/final-delivery.md（需满足 §9 门禁）。`,
  ].join("\n");

  await runAgent("controller", prompt, options);
}

/**
 * 让 Controller 创建一个全新 Task。
 */
export async function invokeControllerCreateTask(params: {
  taskType: string;
  taskTitle: string;
  priority: string;
  humanOwner: string;
  rawRequirement: string;
  apiKey?: string;
}): Promise<void> {
  const { taskType, taskTitle, priority, humanOwner, rawRequirement, apiKey } = params;

  const prompt = [
    `请按 .ai-agents/agents/flow-controller.agent.md 场景 A 执行：创建新 Task`,
    ``,
    `Task 元信息：`,
    `- task_type: ${taskType}`,
    `- task_title: ${taskTitle}`,
    `- priority: ${priority}`,
    `- human_owner: ${humanOwner}`,
    ``,
    `原始需求（写入 messages/from-controller-001-handoff.md 的 payload.raw_requirement，供 PM Agent 读取）：`,
    `"""`,
    rawRequirement,
    `"""`,
    ``,
    `执行步骤：`,
    `1. 生成 task_id（^T-\\d{4}-\\d{3}$），目录名严格 == task_id`,
    `2. 创建目录 workspace/<task-id>/{messages,artifacts/{pm,architect,developer,qa,final},human-reviews,blockers,archive}/`,
    `3. 写 task.md（仅静态元信息）`,
    `4. 写 state.md（current_status = pm_processing，current_agent = pm，next_agent = architect）`,
    `5. 更新 workspace/active-task.md（active_task_id = <new task_id>）`,
    `6. 写 messages/from-controller-001-handoff.md（含原始需求 payload）`,
    `7. 在对话中明确报告：新建的 task_id`,
  ].join("\n");

  await runAgent("controller", prompt, { apiKey });
}
