import * as fs from "node:fs";
import matter from "gray-matter";

import { stateFile, taskFile, ACTIVE_TASK_FILE } from "./paths.js";

export type CurrentStatus =
  | "created"
  | "pm_processing"
  | "pm_completed"
  | "architect_processing"
  | "architect_completed"
  | "human_review_required"
  | "developer_processing"
  | "developer_completed"
  | "qa_processing"
  | "qa_completed"
  | "final_review_required"
  | "completed"
  | "blocked"
  | "cancelled";

export type HumanReviewStatus = "pending" | "approved" | "rejected" | "needs_changes" | "not_required";

export type AgentRole = "pm" | "architect" | "developer" | "qa" | "controller" | "human";

export interface TaskState {
  task_id: string;
  current_status: CurrentStatus;
  previous_status?: CurrentStatus;
  current_agent: AgentRole;
  next_agent?: AgentRole;
  allowed_next_statuses: CurrentStatus[];
  human_review_status: HumanReviewStatus;
  final_review_status: HumanReviewStatus;
  produced_artifacts: string[];
  active_blocker: string | null;
  blockers_history: string[];
  blocked_context: unknown;
  updated_at: string;
  schema_version: string;
}

export interface TaskMeta {
  task_id: string;
  task_type: string;
  task_title: string;
  human_owner: string;
  priority: string;
  created_at: string;
}

export function readState(taskId: string): TaskState {
  const filePath = stateFile(taskId);
  if (!fs.existsSync(filePath)) {
    throw new Error(`state.md not found: ${filePath}`);
  }
  const raw = fs.readFileSync(filePath, "utf-8");
  const parsed = matter(raw);
  return parsed.data as TaskState;
}

export function readTask(taskId: string): TaskMeta {
  const filePath = taskFile(taskId);
  if (!fs.existsSync(filePath)) {
    throw new Error(`task.md not found: ${filePath}`);
  }
  const raw = fs.readFileSync(filePath, "utf-8");
  const parsed = matter(raw);
  return parsed.data as TaskMeta;
}

export function readActiveTaskId(): string | null {
  if (!fs.existsSync(ACTIVE_TASK_FILE)) return null;
  const raw = fs.readFileSync(ACTIVE_TASK_FILE, "utf-8");
  const parsed = matter(raw);
  const id = (parsed.data as { active_task_id?: string }).active_task_id;
  return id && id !== "null" ? id : null;
}

export function isTerminalStatus(status: CurrentStatus): boolean {
  return status === "completed" || status === "cancelled";
}

export function isPauseStatus(status: CurrentStatus): boolean {
  return (
    status === "human_review_required" ||
    status === "final_review_required" ||
    status === "blocked"
  );
}
