import { input, select, confirm } from "@inquirer/prompts";

import type { ClarificationDoc, ClarificationQuestion } from "./clarification-detector.js";

export type Verdict = "approved" | "rejected" | "needs_changes";

export interface ReviewInput {
  verdict: Verdict;
  notes: string;
  issues: Array<{ severity: "blocker" | "major" | "minor"; description: string; affected_artifact?: string }>;
  reviewer: string;
}

export async function promptReview(opts: {
  reviewType: "architect_review" | "final_review";
  reviewedArtifacts: string[];
  defaultReviewer: string;
}): Promise<ReviewInput | null> {
  const verdict = (await select({
    message: `请选择 verdict（${opts.reviewType}）：`,
    choices: [
      { name: "approved — 通过", value: "approved" },
      { name: "rejected — 拒绝", value: "rejected" },
      { name: "needs_changes — 需修改", value: "needs_changes" },
      { name: "暂不审核，退出（之后用 resume-task 继续）", value: "abort" },
    ],
  })) as string;

  if (verdict === "abort") return null;

  const notes = await input({
    message: "评论 / notes（可空）：",
    default: "",
  });

  const issues: ReviewInput["issues"] = [];
  if (verdict !== "approved") {
    let addMore = true;
    while (addMore) {
      const severity = (await select({
        message: "issue severity：",
        choices: [
          { name: "blocker — 阻塞性", value: "blocker" },
          { name: "major — 主要问题", value: "major" },
          { name: "minor — 次要问题", value: "minor" },
        ],
      })) as "blocker" | "major" | "minor";

      const description = await input({
        message: "issue description：",
      });

      const affected = await input({
        message: "affected_artifact（artifact_id，可空）：",
        default: opts.reviewedArtifacts[0] ?? "",
      });

      issues.push({
        severity,
        description,
        affected_artifact: affected || undefined,
      });

      addMore = await confirm({
        message: "继续添加 issue？",
        default: false,
      });
    }
  }

  const reviewer = await input({
    message: "reviewer（用户 handle）：",
    default: opts.defaultReviewer,
  });

  return { verdict: verdict as Verdict, notes, issues, reviewer };
}

export async function promptClarification(question: ClarificationQuestion): Promise<string> {
  const message = [
    question.question,
    question.why_asking ? `\n  原因：${question.why_asking}` : "",
    question.default ? `\n  默认：${question.default}` : "",
  ].join("");

  if (question.options && question.options.length > 0) {
    const answer = (await select({
      message,
      choices: [
        ...question.options.map((o) => ({ name: o, value: o })),
        { name: "✏️ 自由输入...", value: "__free__" },
      ],
      default: question.default ?? undefined,
    })) as string;

    if (answer === "__free__") {
      return input({ message: "自由输入答案：" });
    }
    return answer;
  }

  return input({ message, default: question.default ?? undefined });
}

export async function promptClarifications(doc: ClarificationDoc): Promise<Array<{ id: string; answer: string }>> {
  const pending = doc.questions.filter((q) => (q.answer === null || q.answer === undefined || q.answer === "") && q.blocks_progress !== false);
  const answers: Array<{ id: string; answer: string }> = [];

  for (const q of pending) {
    const answer = await promptClarification(q);
    answers.push({ id: q.id, answer });
  }

  return answers;
}
