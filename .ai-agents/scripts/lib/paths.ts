import * as path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const PROJECT_ROOT = path.resolve(__dirname, "../../..");
export const AI_AGENTS_ROOT = path.join(PROJECT_ROOT, ".ai-agents");
export const WORKSPACE_ROOT = path.join(AI_AGENTS_ROOT, "workspace");
export const ACTIVE_TASK_FILE = path.join(WORKSPACE_ROOT, "active-task.md");

export function taskDir(taskId: string): string {
  return path.join(WORKSPACE_ROOT, taskId);
}

export function stateFile(taskId: string): string {
  return path.join(taskDir(taskId), "state.md");
}

export function taskFile(taskId: string): string {
  return path.join(taskDir(taskId), "task.md");
}

export function messagesDir(taskId: string): string {
  return path.join(taskDir(taskId), "messages");
}

export function artifactsDir(taskId: string, role: string): string {
  return path.join(taskDir(taskId), "artifacts", role);
}

export function humanReviewsDir(taskId: string): string {
  return path.join(taskDir(taskId), "human-reviews");
}

export function clarificationFile(taskId: string, role: string): string {
  return path.join(artifactsDir(taskId, role), "clarification-questions.md");
}
