import * as fs from "node:fs";
import * as path from "node:path";

import { humanReviewsDir } from "./paths.js";
import type { ReviewInput, Verdict } from "./review-prompter.js";

export interface WriteReviewParams {
  taskId: string;
  reviewType: "architect_review" | "final_review";
  reviewedArtifacts: string[];
  input: ReviewInput;
}

export function writeReviewRecord(params: WriteReviewParams): string {
  const { taskId, reviewType, reviewedArtifacts, input } = params;

  const fileName = reviewType === "architect_review" ? "architect-review.md" : "final-review.md";
  const dir = humanReviewsDir(taskId);
  fs.mkdirSync(dir, { recursive: true });
  const filePath = path.join(dir, fileName);

  const reviewId = `R-${taskId}-${reviewType === "architect_review" ? "architect" : "final"}`;
  const reviewedAt = new Date().toISOString().replace(/\.\d{3}Z$/, "+00:00");
  const followupRequired = input.verdict !== "approved";

  const issuesYaml =
    input.issues.length === 0
      ? "issues: []"
      : "issues:\n" +
        input.issues
          .map(
            (i) =>
              `  - severity: ${i.severity}\n` +
              `    description: ${escapeYaml(i.description)}` +
              (i.affected_artifact ? `\n    affected_artifact: ${i.affected_artifact}` : ""),
          )
          .join("\n");

  const frontmatter = [
    "---",
    `review_id: ${reviewId}`,
    `task_id: ${taskId}`,
    `review_type: ${reviewType}`,
    "reviewed_artifacts:",
    ...reviewedArtifacts.map((a) => `  - ${a}`),
    `reviewer: ${input.reviewer}`,
    `reviewed_at: ${reviewedAt}`,
    `verdict: ${input.verdict}`,
    issuesYaml,
    `followup_required: ${followupRequired}`,
    `notes: ${escapeYaml(input.notes || "(无)")}`,
    "schema_version: a2a/v1",
    "---",
    "",
    `# ${reviewType === "architect_review" ? "Architect Review" : "Final Review"}`,
    "",
    "## 我审阅了什么",
    ...reviewedArtifacts.map((a) => `- ${a}`),
    "",
    "## 我的判断",
    `verdict: ${input.verdict}`,
    "",
    "## 我对下游 Agent 的额外要求",
    input.issues.length > 0
      ? input.issues.map((i, idx) => `- [${i.severity}] ${i.description}`).join("\n")
      : "- (无)",
    "",
    "## 备注",
    input.notes || "(无)",
    "",
  ].join("\n");

  fs.writeFileSync(filePath, frontmatter, "utf-8");
  return filePath;
}

function escapeYaml(s: string): string {
  if (/[:#\n"']/.test(s)) {
    return `"${s.replace(/"/g, '\\"').replace(/\n/g, "\\n")}"`;
  }
  return s;
}

export function verdictToHumanReviewStatus(v: Verdict): "approved" | "rejected" | "needs_changes" {
  return v;
}
