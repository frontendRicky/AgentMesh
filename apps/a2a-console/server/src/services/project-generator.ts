import fs from 'node:fs';
import path from 'node:path';

import type {
  ProjectGeneratorDraftId,
  ProjectGeneratorDraftRequest,
  ProjectGeneratorDraftResponse,
  ProjectGeneratorTaskCreateRequest,
  ProjectGeneratorTaskCreateResponse,
} from '@a2a-console/contract';

import { resolveSafePath } from '../lib/path-guard.js';
import { PROJECT_GENERATOR_TEMPLATES } from './project-generator-templates.js';

const TASK_ID_RE = /^T-\d{4}-\d{3}$/;
const SLUG_RE = /^[a-z0-9-]{1,40}$/;

export class ProjectGeneratorError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details?: unknown,
  ) {
    super(message);
  }
}

interface StoredDraft extends ProjectGeneratorDraftResponse {
  input: ProjectGeneratorDraftRequest;
  created_at: string;
}

let draftCounter = 0;
const drafts = new Map<ProjectGeneratorDraftId, StoredDraft>();

export function createProjectDraft(input: ProjectGeneratorDraftRequest): ProjectGeneratorDraftResponse {
  draftCounter += 1;
  const year = new Date().getFullYear();
  const draftId = `D-${year}-004-${String(draftCounter).padStart(3, '0')}` as ProjectGeneratorDraftId;
  const summary = buildSummary(input);
  const prdPreview = buildPrdPreview(input, summary);
  const openspecPreview = buildOpenSpecPreview(input);
  const modelSnapshotPreview = buildModelSnapshot(input);
  const draft: StoredDraft = {
    draft_id: draftId,
    summary,
    prd_preview: prdPreview,
    openspec_preview: openspecPreview,
    model_snapshot_preview: modelSnapshotPreview,
    input,
    created_at: nowWithOffset(),
  };
  drafts.set(draftId, draft);
  return {
    draft_id: draft.draft_id,
    summary: draft.summary,
    prd_preview: draft.prd_preview,
    openspec_preview: draft.openspec_preview,
    model_snapshot_preview: draft.model_snapshot_preview,
  };
}

export function createTaskFromDraft(
  projectRoot: string,
  draftId: ProjectGeneratorDraftId,
  request: ProjectGeneratorTaskCreateRequest,
): ProjectGeneratorTaskCreateResponse {
  const draft = drafts.get(draftId);
  if (!draft) {
    throw new ProjectGeneratorError(404, 'DRAFT_NOT_FOUND', 'draft_id not found or expired');
  }
  if (!SLUG_RE.test(request.slug)) {
    throw new ProjectGeneratorError(400, 'TASK_SLUG_INVALID', 'slug must match ^[a-z0-9-]{1,40}$');
  }

  const workspaceRoot = path.join(projectRoot, '.ai-agents', 'workspace');
  const taskId = allocateNextTaskId(workspaceRoot);
  const taskRoot = resolveSafePath(workspaceRoot, taskId);
  if (!TASK_ID_RE.test(taskId)) {
    throw new ProjectGeneratorError(500, 'TASK_ID_INVALID', 'generated task_id failed validation');
  }
  if (fs.existsSync(taskRoot)) {
    throw new ProjectGeneratorError(409, 'TASK_ID_CONFLICT', `${taskId} already exists`);
  }

  const now = nowWithOffset();
  const createdFiles = writeTaskPackage(taskRoot, taskId, request.slug, draft, now);
  drafts.delete(draftId);

  return {
    task_id: taskId,
    task_path: `.ai-agents/workspace/${taskId}`,
    created_files: createdFiles,
    model_snapshot_path: 'artifacts/pm/model-selection-snapshot.md',
    next_step: 'handoff_to_technical_owner',
  };
}

function allocateNextTaskId(workspaceRoot: string): string {
  const year = new Date().getFullYear();
  const prefix = `T-${year}-`;
  const pattern = new RegExp(`^${prefix}\\d{3}$`);
  const existing = fs
    .readdirSync(workspaceRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory() && pattern.test(entry.name))
    .map((entry) => Number(entry.name.slice(prefix.length)))
    .filter((value) => Number.isInteger(value));
  const next = existing.length > 0 ? Math.max(...existing) + 1 : 1;
  if (next > 999) {
    throw new ProjectGeneratorError(409, 'TASK_ID_CONFLICT', `No available task_id in ${year}`);
  }
  return `${prefix}${String(next).padStart(3, '0')}`;
}

function writeTaskPackage(
  taskRoot: string,
  taskId: string,
  slug: string,
  draft: StoredDraft,
  now: string,
): string[] {
  const files: Array<{ relativePath: string; content: string }> = [
    {
      relativePath: 'task.md',
      content: frontmatter(
        {
          task_id: taskId,
          task_title: draft.input.project_name,
          task_type: 'frontend_project_generation',
          task_slug: slug,
          priority: 'medium',
          created_by: 'a2a-console-generator',
          created_at: now,
          schema_version: 'a2a/v1',
        },
        buildTaskBody(draft),
      ),
    },
    {
      relativePath: 'state.md',
      content: frontmatter(
        {
          task_id: taskId,
          current_status: 'pm_completed',
          previous_status: 'pm_processing',
          current_agent: 'pm',
          next_agent: 'architect',
          allowed_next_statuses: ['architect_processing', 'blocked'],
          human_review_status: 'not_required',
          final_review_status: 'not_required',
          produced_artifacts: [
            'artifacts/pm/requirement.md',
            'artifacts/pm/prd.md',
            'artifacts/pm/task-breakdown.md',
            'artifacts/pm/model-selection-snapshot.md',
            'artifacts/pm/user-input-snapshot.md',
          ],
          active_blocker: null,
          blockers_history: [],
          blocked_context: null,
          updated_at: now,
          schema_version: 'a2a/v1',
        },
        [
          '# State',
          '',
          '## 写入历史',
          '',
          '| 时间 | from | to | 触发原因 |',
          '|---|---|---|---|',
          `| ${now} | null | pm_processing | A2A Console 普通模式根据用户输入创建任务包 |`,
          `| ${now} | pm_processing | pm_completed | 已生成 requirement / prd / task-breakdown / model-selection-snapshot，等待技术同事进入 Architect 阶段 |`,
        ].join('\n'),
      ),
    },
    {
      relativePath: 'artifacts/pm/requirement.md',
      content: frontmatter(
        artifactFrontmatter(taskId, 'A-requirement', 'requirement', now),
        buildRequirementBody(draft),
      ),
    },
    {
      relativePath: 'artifacts/pm/prd.md',
      content: frontmatter(
        artifactFrontmatter(taskId, 'A-prd', 'prd', now),
        draft.prd_preview,
      ),
    },
    {
      relativePath: 'artifacts/pm/task-breakdown.md',
      content: frontmatter(
        artifactFrontmatter(taskId, 'A-task-breakdown', 'task_breakdown', now),
        buildTaskBreakdownBody(draft),
      ),
    },
    {
      relativePath: 'artifacts/pm/model-selection-snapshot.md',
      content: frontmatter(
        artifactFrontmatter(taskId, 'A-model-selection-snapshot', 'model_selection_snapshot', now),
        draft.model_snapshot_preview,
      ),
    },
    {
      relativePath: 'artifacts/pm/user-input-snapshot.md',
      content: frontmatter(
        artifactFrontmatter(taskId, 'A-user-input-snapshot', 'user_input_snapshot', now),
        buildUserInputSnapshot(draft.input),
      ),
    },
    {
      relativePath: 'messages/from-pm-001-handoff.md',
      content: frontmatter(
        {
          message_id: `M-${taskId}-001`,
          task_id: taskId,
          from_agent: 'pm',
          to_agent: 'architect',
          message_type: 'handoff',
          intent: 'pm_to_architect',
          summary: '普通模式已生成前端项目任务包，请技术同事在 Cursor / Codex 中继续 A2A 流程。',
          required_response: true,
          referenced_artifacts: [
            'artifacts/pm/requirement.md',
            'artifacts/pm/prd.md',
            'artifacts/pm/task-breakdown.md',
            'artifacts/pm/model-selection-snapshot.md',
          ],
          created_at: now,
          schema_version: 'a2a/v1',
        },
        [
          '# PM Handoff',
          '',
          '请从 Architect 阶段继续：阅读 PM artifacts，制定 tech-plan / file-change-plan / risk-plan，并按 A2A Human Review 门禁推进。',
        ].join('\n'),
      ),
    },
  ];

  fs.mkdirSync(taskRoot, { recursive: false });
  for (const file of files) {
    const absPath = resolveWithinTaskRoot(taskRoot, file.relativePath);
    fs.mkdirSync(path.dirname(absPath), { recursive: true });
    fs.writeFileSync(absPath, file.content, 'utf8');
  }

  return files.map((file) => file.relativePath);
}

function resolveWithinTaskRoot(taskRoot: string, relativePath: string): string {
  if (relativePath.includes('\0') || path.isAbsolute(relativePath)) {
    throw new ProjectGeneratorError(400, 'PATH_TRAVERSAL', 'relative file path is invalid');
  }
  const segments = relativePath.split(/[\\/]+/);
  if (segments.some((segment) => segment === '..')) {
    throw new ProjectGeneratorError(400, 'PATH_TRAVERSAL', 'relative file path escapes task root');
  }
  const resolved = path.resolve(taskRoot, relativePath);
  if (resolved !== taskRoot && !resolved.startsWith(taskRoot + path.sep)) {
    throw new ProjectGeneratorError(400, 'PATH_TRAVERSAL', 'relative file path escapes task root');
  }
  return resolved;
}

function artifactFrontmatter(
  taskId: string,
  shortId: string,
  artifactType: string,
  now: string,
): Record<string, unknown> {
  return {
    artifact_id: `${shortId}-${taskId}`,
    task_id: taskId,
    artifact_type: artifactType,
    produced_by: 'pm',
    consumed_by: ['architect', 'developer', 'qa'],
    version: 1,
    status: 'ready',
    created_at: now,
    schema_version: 'a2a/v1',
  };
}

function buildSummary(input: ProjectGeneratorDraftRequest): string {
  const template = PROJECT_GENERATOR_TEMPLATES.find((item) => item.id === input.project_type);
  return `${input.project_name}：${template?.name ?? '自定义项目'}，面向${input.target_users || '目标用户'}，以${strategyLabel(input.generation_strategy)}方式整理为前端项目任务包。`;
}

function buildPrdPreview(input: ProjectGeneratorDraftRequest, summary: string): string {
  return [
    '# 产品需求说明',
    '',
    '## 目标',
    '',
    summary,
    '',
    '## 用户和场景',
    '',
    input.target_users || '待技术同事继续澄清。',
    '',
    '## 需求说明',
    '',
    input.business_description,
    '',
    '## 页面范围',
    '',
    ...listOrFallback(input.pages, '普通用户暂未列出页面，请 Architect 在下一阶段拆分。'),
    '',
    '## 数据和接口',
    '',
    input.data_source || '默认先使用前端 mock 数据；如需真实接口，由技术同事在后续阶段补充契约。',
    '',
    '## 风格偏好',
    '',
    input.style_preference || '保持清晰、易懂、适合非技术同事验收。',
  ].join('\n');
}

function buildOpenSpecPreview(input: ProjectGeneratorDraftRequest): string {
  return [
    '# 技术同事继续说明',
    '',
    '## 目标',
    '',
    '- 生成可由技术同事继续执行的前端项目任务包。',
    '- 普通用户只需要填写中文业务信息，不需要理解 A2A 内部术语。',
    '',
    '## 范围',
    '',
    `- 项目类型：${input.project_type}`,
    `- 生成策略：${input.generation_strategy}`,
    `- 模型选择：${input.model_profile}`,
    `- 接口模式：${input.api_mode}`,
    '',
    '## 暂不做',
    '',
    '- 本期不在浏览器里一键执行代码生成。',
    '- 本期不写入 apps/generated-projects/。',
    '- 本期不保存 API Key，也不调用外部模型接口。',
  ].join('\n');
}

function buildModelSnapshot(input: ProjectGeneratorDraftRequest): string {
  return [
    '# Model Selection Snapshot',
    '',
    `- 选择档位：${modelProfileLabel(input.model_profile)}`,
    `- 生成策略：${strategyLabel(input.generation_strategy)}`,
    '- 快照说明：此文件是新任务的执行真相；浏览器本地记录只用于下次回填表单。',
    '- 执行提醒：请技术同事在 Cursor / Codex 中按组织批准的模型配置继续。',
  ].join('\n');
}

function buildTaskBody(draft: StoredDraft): string {
  return [
    '# Task',
    '',
    draft.summary,
    '',
    '## 如何继续',
    '',
    '把本任务包交给技术同事，在 Cursor / Codex 中从 Architect 阶段继续 A2A 流程。',
  ].join('\n');
}

function buildRequirementBody(draft: StoredDraft): string {
  return [
    '# Requirement',
    '',
    draft.summary,
    '',
    '## 原始业务说明',
    '',
    draft.input.business_description,
    '',
    '## 验收提醒',
    '',
    '- 页面文案需要让非技术同事能读懂。',
    '- 普通用户不应接触执行按钮、密钥或内部模型配置文件。',
  ].join('\n');
}

function buildTaskBreakdownBody(draft: StoredDraft): string {
  return [
    '# Task Breakdown',
    '',
    '1. Architect：将普通需求拆成技术方案、文件白名单和风险计划。',
    '2. Developer：按白名单实现页面、接口和契约校验。',
    '3. QA：按 PRD 和 OpenSpec 验收中文普通模式、专家模式回归与安全边界。',
    '',
    '## 建议页面',
    '',
    ...listOrFallback(draft.input.pages, '普通用户暂未列出页面，请 Architect 继续拆分。'),
  ].join('\n');
}

function buildUserInputSnapshot(input: ProjectGeneratorDraftRequest): string {
  return [
    '# User Input Snapshot',
    '',
    `- 项目名称：${input.project_name}`,
    `- 项目类型：${input.project_type}`,
    `- 目标用户：${input.target_users || '未填写'}`,
    `- 需要登录：${input.needs_auth ? '是' : '否'}`,
    `- 需要图表：${input.needs_charts ? '是' : '否'}`,
    `- 接口模式：${input.api_mode}`,
    '',
    '## 业务说明',
    '',
    input.business_description,
    '',
    '## 风格偏好',
    '',
    input.style_preference || '未填写',
  ].join('\n');
}

function listOrFallback(items: string[], fallback: string): string[] {
  if (items.length === 0) return [`- ${fallback}`];
  return items.map((item) => `- ${item}`);
}

function strategyLabel(value: ProjectGeneratorDraftRequest['generation_strategy']): string {
  const labels: Record<ProjectGeneratorDraftRequest['generation_strategy'], string> = {
    quick: '先快跑出可看版本',
    quality: '质量优先',
    budget: '节省成本',
    strict: '需求完整和风险优先',
  };
  return labels[value];
}

function modelProfileLabel(value: ProjectGeneratorDraftRequest['model_profile']): string {
  const labels: Record<ProjectGeneratorDraftRequest['model_profile'], string> = {
    recommended: '推荐',
    faster: '更快',
    stronger: '更强',
    cheaper: '更省',
    custom: '专家自定义',
  };
  return labels[value];
}

function frontmatter(data: Record<string, unknown>, body: string): string {
  return `---\n${toYaml(data)}---\n\n${body}\n`;
}

function toYaml(data: Record<string, unknown>): string {
  return Object.entries(data)
    .map(([key, value]) => yamlField(key, value))
    .join('');
}

function yamlField(key: string, value: unknown): string {
  if (Array.isArray(value)) {
    if (value.length === 0) return `${key}: []\n`;
    return `${key}:\n${value.map((item) => `  - ${yamlScalar(item)}\n`).join('')}`;
  }
  return `${key}: ${yamlScalar(value)}\n`;
}

function yamlScalar(value: unknown): string {
  if (value === null) return 'null';
  if (typeof value === 'boolean' || typeof value === 'number') return String(value);
  return JSON.stringify(String(value));
}

function nowWithOffset(): string {
  const date = new Date();
  const offsetMinutes = -date.getTimezoneOffset();
  const sign = offsetMinutes >= 0 ? '+' : '-';
  const absOffset = Math.abs(offsetMinutes);
  const offsetHours = String(Math.floor(absOffset / 60)).padStart(2, '0');
  const offsetMins = String(absOffset % 60).padStart(2, '0');
  return [
    date.getFullYear(),
    '-',
    String(date.getMonth() + 1).padStart(2, '0'),
    '-',
    String(date.getDate()).padStart(2, '0'),
    'T',
    String(date.getHours()).padStart(2, '0'),
    ':',
    String(date.getMinutes()).padStart(2, '0'),
    ':',
    String(date.getSeconds()).padStart(2, '0'),
    sign,
    offsetHours,
    ':',
    offsetMins,
  ].join('');
}
