import fs from 'node:fs';
import path from 'node:path';
import {
  type ContextAgent,
  type ContextBuildRequest,
  type ContextPack,
  type ContextPackItem,
  type ContextPackItemType,
} from '@a2a-console/contract';

import { resolveSafePath } from '../lib/path-guard.js';
import { parseFileChangePlanPaths } from './file-change-plan-parser.js';
import { contextPackStore } from './context-pack-store.js';

const MAX_INPUT_TOKENS_PER_RUN = 80000;
const DEFAULT_ITEM_CHAR_LIMIT = 30000;
const FAIL_LOG_CHAR_LIMIT = 20000;
const PER_ITEM_TRUNCATE_THRESHOLD = 50000;
const PER_ITEM_TRUNCATE_TARGET = 30000;

export function buildContextPack(projectRoot: string, request: ContextBuildRequest): ContextPack {
  if (request.full_context === true && !request.reason?.trim()) {
    throw codedError('FULL_CONTEXT_REASON_REQUIRED', 'full_context=true requires a reason');
  }

  const taskRoot = resolveTaskRoot(projectRoot, request.task_id);
  const sources = readTaskSources(taskRoot, request.extra_context);
  const rawItems = itemsForAgent(request.agent, sources, request.full_context === true);
  const items = maybeCompressItems(rawItems, request.full_context === true);
  const pack: ContextPack = {
    pack_id: contextPackStore.createId(),
    task_id: request.task_id,
    agent: request.agent,
    items,
    total_estimated_input_tokens: sumTokens(items),
    full_context: request.full_context === true,
    created_at: new Date().toISOString(),
  };
  return contextPackStore.add(pack);
}

interface TaskSources {
  requirement: string;
  prd: string;
  fileChangePlan: string;
  techPlan: string;
  riskPlan: string;
  fileChangePaths: string[];
  extraContext: string;
}

function resolveTaskRoot(projectRoot: string, taskId: string): string {
  if (!/^T-\d{4}-\d{3}$/.test(taskId)) {
    throw codedError('TASK_ID_INVALID', 'task_id must match ^T-\\d{4}-\\d{3}$');
  }
  const taskRoot = resolveSafePath(projectRoot, `.ai-agents/workspace/${taskId}`);
  if (!fs.existsSync(taskRoot) || !fs.statSync(taskRoot).isDirectory()) {
    throw codedError('TASK_NOT_FOUND', `Task not found: ${taskId}`);
  }
  return taskRoot;
}

function readTaskSources(taskRoot: string, extraContext?: string): TaskSources {
  const fileChangePlan = readText(taskRoot, 'artifacts/architect/file-change-plan.md');
  return {
    requirement: readText(taskRoot, 'artifacts/pm/requirement.md'),
    prd: readText(taskRoot, 'artifacts/pm/prd.md'),
    fileChangePlan,
    techPlan: readText(taskRoot, 'artifacts/architect/tech-plan.md'),
    riskPlan: readText(taskRoot, 'artifacts/architect/risk-plan.md'),
    fileChangePaths: parseFileChangePlanPaths(fileChangePlan),
    extraContext: extraContext ?? '',
  };
}

function readText(taskRoot: string, relativePath: string): string {
  const absPath = path.join(taskRoot, relativePath);
  if (!fs.existsSync(absPath)) return '';
  return fs.readFileSync(absPath, 'utf8');
}

function itemsForAgent(
  agent: ContextAgent,
  sources: TaskSources,
  fullContext: boolean,
): ContextPackItem[] {
  const items: ContextPackItem[] = [];
  if (agent === 'pm') {
    items.push(createItem('requirement', 'PM requirement', sources.requirement, 'artifacts/pm/requirement.md', 'PM 阶段只需要用户需求与价值背景。'));
  } else if (agent === 'architect') {
    items.push(createItem('requirement', 'Requirement', sources.requirement, 'artifacts/pm/requirement.md', 'Architect 需要需求边界。'));
    items.push(createItem('prd_summary', 'PRD summary', sources.prd, 'artifacts/pm/prd.md', 'Architect 需要产品验收与用户路径。'));
    items.push(pathsItem(sources.fileChangePaths, 'file_change_plan_paths', '当前 file-change-plan 路径列表，仅路径不展开源码。'));
    items.push(createItem('constraints', 'Technical constraints', sources.techPlan, 'artifacts/architect/tech-plan.md', '用于延续既定技术约束。'));
  } else if (agent === 'developer') {
    items.push(createItem('file_change_plan', 'File change plan', sources.fileChangePlan, 'artifacts/architect/file-change-plan.md', 'Developer 必须按白名单写代码。'));
    items.push(pathsItem(sources.fileChangePaths, 'file_change_plan_paths', '列出被授权文件路径，不读取文件正文。'));
    items.push(pathsItem(sources.fileChangePaths, 'authorized_paths', 'Developer 写入前逐项核对 allowlist。'));
    items.push(createItem('technical_constraints', 'Tech plan', sources.techPlan, 'artifacts/architect/tech-plan.md', '实现必须遵循 revision 2 技术约束。'));
  } else if (agent === 'qa') {
    items.push(createItem('file_change_plan', 'File change plan', sources.fileChangePlan, 'artifacts/architect/file-change-plan.md', 'QA 用于检查 scoped diff。'));
    items.push(createItem('diff', 'Sandbox diff', sources.extraContext, undefined, 'QA 验收 diff，长文本会截断。'));
    items.push(createItem('fail_log', 'Failure log', sources.extraContext, undefined, '测试失败日志，UI 仅展示摘要。'));
    items.push(createItem('acceptance_scope', 'Risk plan', sources.riskPlan, 'artifacts/architect/risk-plan.md', 'QA 验收风险重点。'));
  } else if (agent === 'fix') {
    items.push(createItem('fail_log', 'Failure log', sources.extraContext, undefined, 'Fix 只围绕失败日志修复。'));
    items.push(createItem('diff', 'Current diff', sources.extraContext, undefined, 'Fix 需要当前差异。'));
    items.push(pathsItem(sources.fileChangePaths, 'changed_paths', 'Fix 只能在既有授权路径内行动。'));
    items.push(createItem('fix_scope', 'Fix scope', sources.riskPlan, 'artifacts/architect/risk-plan.md', '避免扩大修复范围。'));
  } else {
    items.push(createItem('diff', 'Security diff', sources.extraContext, undefined, 'Security 只看差异。'));
    items.push(pathsItem(sources.fileChangePaths, 'high_risk_paths', '复用 risk-scorer 识别高风险路径。'));
    items.push(createItem('forbidden_rules', 'Forbidden entries', sources.fileChangePlan, 'artifacts/architect/file-change-plan.md', 'Security 检查禁改集。'));
  }

  if (fullContext) {
    items.push(createItem('constraints', 'Full context reason', sources.extraContext, undefined, 'full_context 已由用户提供原因，额外上下文保留。'));
  }
  return items;
}

function createItem(
  type: ContextPackItemType,
  title: string,
  content: string,
  sourcePath: string | undefined,
  reason: string,
): ContextPackItem {
  return {
    type,
    title,
    content,
    source_path: sourcePath,
    estimated_tokens: estimateTokens(content),
    truncated: false,
    inclusion_reason: reason,
  };
}

function pathsItem(paths: string[], type: ContextPackItemType, reason: string): ContextPackItem {
  return createItem(type, 'Authorized paths', paths.map((item) => `- ${item}`).join('\n'), undefined, reason);
}

function maybeCompressItems(items: ContextPackItem[], fullContext: boolean): ContextPackItem[] {
  if (fullContext) {
    return items.map((item) => ({ ...item, estimated_tokens: estimateTokens(item.content) }));
  }

  const perFieldTruncated = items.map((item) => truncateOversizedItem(item));
  if (sumTokens(perFieldTruncated) <= MAX_INPUT_TOKENS_PER_RUN) {
    return perFieldTruncated;
  }
  return perFieldTruncated.map((item) => truncateItem(item));
}

function truncateOversizedItem(item: ContextPackItem): ContextPackItem {
  if (item.content.length <= PER_ITEM_TRUNCATE_THRESHOLD) {
    return { ...item, estimated_tokens: estimateTokens(item.content) };
  }
  const content = item.content.slice(0, PER_ITEM_TRUNCATE_TARGET);
  return {
    ...item,
    content,
    estimated_tokens: estimateTokens(content),
    truncated: true,
    inclusion_reason: `${item.inclusion_reason}（超过 ${PER_ITEM_TRUNCATE_THRESHOLD} 字符上限，已截断到 ${PER_ITEM_TRUNCATE_TARGET} 字符）`,
  };
}

function truncateItem(item: ContextPackItem): ContextPackItem {
  const limit = item.type === 'fail_log' ? FAIL_LOG_CHAR_LIMIT : DEFAULT_ITEM_CHAR_LIMIT;
  if (item.content.length <= limit) {
    return { ...item, estimated_tokens: estimateTokens(item.content) };
  }
  const content = item.content.slice(0, limit);
  return {
    ...item,
    content,
    estimated_tokens: estimateTokens(content),
    truncated: true,
    inclusion_reason: `${item.inclusion_reason} 因超过预算，内容已截断到 ${limit} 字符。`,
  };
}

function estimateTokens(content: string): number {
  return Math.ceil(content.length / 4);
}

function sumTokens(items: ContextPackItem[]): number {
  return items.reduce((sum, item) => sum + item.estimated_tokens, 0);
}

function codedError(code: string, message: string): Error & { code: string } {
  const error = new Error(message) as Error & { code: string };
  error.code = code;
  return error;
}
