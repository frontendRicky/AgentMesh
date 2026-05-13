import * as fs from "node:fs";
import matter from "gray-matter";

import { clarificationFile } from "./paths.js";

export type ClarificationRole = "pm" | "architect" | "developer" | "qa";

export interface ClarificationQuestion {
  id: string;
  question: string;
  options?: string[];
  default?: string | null;
  why_asking?: string;
  blocks_progress?: boolean;
  answer?: string | null;
}

export interface ClarificationDoc {
  role: ClarificationRole;
  filePath: string;
  status: "pending" | "answered" | "resolved";
  questions: ClarificationQuestion[];
  raw: string;
}

const ROLES: ClarificationRole[] = ["pm", "architect", "developer", "qa"];

/**
 * 扫描所有角色目录下的 clarification-questions.md，
 * 返回存在且包含未回答（answer == null）且 blocks_progress != false 的文件。
 */
export function detectPendingClarifications(taskId: string): ClarificationDoc[] {
  const docs: ClarificationDoc[] = [];

  for (const role of ROLES) {
    const filePath = clarificationFile(taskId, role);
    if (!fs.existsSync(filePath)) continue;

    const raw = fs.readFileSync(filePath, "utf-8");
    const parsed = matter(raw);
    const frontmatter = parsed.data as { status?: string };
    const questions = parseQuestions(parsed.content);

    if (frontmatter.status === "resolved") continue;

    const pending = questions.filter(
      (q) => (q.answer === null || q.answer === undefined || q.answer === "") && q.blocks_progress !== false,
    );

    if (pending.length > 0) {
      docs.push({
        role,
        filePath,
        status: (frontmatter.status as "pending" | "answered") ?? "pending",
        questions,
        raw,
      });
    }
  }

  return docs;
}

/**
 * 将答案写回 clarification-questions.md。
 * 对每个 question.id：先尝试替换 answer: null，否则替换 answer: <旧值>。
 * 同时把 frontmatter status 改成 answered（保留文件，便于审计）。
 */
export function writeAnswers(
  doc: ClarificationDoc,
  answers: Array<{ id: string; answer: string }>,
): void {
  let next = doc.raw;

  for (const { id, answer } of answers) {
    const safeAnswer = answer.replace(/"/g, '\\"');
    const idPattern = new RegExp(
      `(- id:\\s*${escapeRegex(id)}[\\s\\S]*?answer:\\s*)(null|".*?"|.+?)(\\n)`,
    );
    if (idPattern.test(next)) {
      next = next.replace(idPattern, `$1"${safeAnswer}"$3`);
    }
  }

  next = next.replace(/^(status:\s*)pending(\s*)$/m, `$1answered$2`);

  fs.writeFileSync(doc.filePath, next, "utf-8");
}

function parseQuestions(body: string): ClarificationQuestion[] {
  const questions: ClarificationQuestion[] = [];
  const blocks = body.split(/^- id:\s*/m).slice(1);

  for (const block of blocks) {
    const idMatch = block.match(/^([A-Za-z0-9_-]+)/);
    const questionMatch = block.match(/^\s*question:\s*(.+?)(?:\n|$)/m);
    const defaultMatch = block.match(/^\s*default:\s*(.+?)(?:\n|$)/m);
    const whyMatch = block.match(/^\s*why_asking:\s*(.+?)(?:\n|$)/m);
    const blocksMatch = block.match(/^\s*blocks_progress:\s*(true|false)/m);
    const answerMatch = block.match(/^\s*answer:\s*(null|".*?"|.+?)(?:\n|$)/m);

    const optionsBlock = block.match(/options:\s*\n([\s\S]*?)(?:\n\s*\w|\n\s*$|$)/);
    const options: string[] = [];
    if (optionsBlock) {
      const lines = optionsBlock[1].split("\n");
      for (const line of lines) {
        const m = line.match(/^\s*-\s*(.+?)\s*$/);
        if (m) options.push(m[1].replace(/^"|"$/g, ""));
      }
    }

    if (idMatch && questionMatch) {
      questions.push({
        id: idMatch[1],
        question: questionMatch[1].replace(/^"|"$/g, "").trim(),
        options: options.length > 0 ? options : undefined,
        default: defaultMatch ? defaultMatch[1].replace(/^"|"$/g, "").trim() : null,
        why_asking: whyMatch ? whyMatch[1].replace(/^"|"$/g, "").trim() : undefined,
        blocks_progress: blocksMatch ? blocksMatch[1] === "true" : true,
        answer: answerMatch && answerMatch[1] !== "null"
          ? answerMatch[1].replace(/^"|"$/g, "").trim()
          : null,
      });
    }
  }

  return questions;
}

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
