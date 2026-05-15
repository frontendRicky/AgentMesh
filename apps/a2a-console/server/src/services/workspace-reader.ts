import fs from 'node:fs';
import path from 'node:path';

import { resolveSafePath } from '../lib/path-guard.js';
import { readMarkdownWithLimit, type ReadResult } from '../lib/file-size-guard.js';
import { parseMarkdown, type ParsedMarkdown } from './frontmatter.js';
import { emptyAgentBucket, estimateTokens, type AgentTokenBucket } from './token-estimate.js';

const TASK_ID_RE = /^T-\d{4}-\d{3}$/;

/**
 * gray-matter 经 js-yaml 会把 YAML 时间戳自动转 Date 对象，导致下游
 * 字符串操作（localeCompare、includes）失败。此处统一转 ISO 字符串。
 */
function toIsoString(value: unknown): string | null {
  if (value === undefined || value === null) return null;
  if (value instanceof Date) return value.toISOString();
  if (typeof value === 'string') return value;
  return String(value);
}

interface ActiveTaskFm {
  active_task_id?: string | null;
  last_switched_at?: string;
  schema_version?: string;
}

export interface ActiveTaskInfo {
  active_task_id: string | null;
  last_switched_at: string | null;
  directory_exists: boolean;
}

export interface TaskListItem {
  task_id: string;
  task_title: string | null;
  task_type: string | null;
  priority: string | null;
  current_status: string | null;
  current_agent: string | null;
  human_review_status: string | null;
  final_review_status: string | null;
  blocker_count: number;
  produced_artifacts_count: number;
  token_total_estimate: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface TaskFilter {
  status?: string;
  agent?: string;
  priority?: string;
  q?: string;
}

export interface TreeFileNode {
  type: 'file';
  name: string;
  size: number;
  path: string;
}

export interface TreeDirNode {
  type: 'dir';
  name: string;
  path: string;
  children: TreeNode[];
}

export type TreeNode = TreeFileNode | TreeDirNode;

export interface ArtifactFile extends ReadResult {
  path: string;
  parsed: ParsedMarkdown;
}

export interface MessageItem {
  message_id: string | null;
  from_agent: string | null;
  to_agent: string | null;
  message_type: string | null;
  intent: string | null;
  summary: string | null;
  referenced_artifacts: string[];
  created_at: string | null;
  file_path: string;
}

export interface BlockerItem {
  blocker_id: string | null;
  blocking_reason: string | null;
  missing_artifacts: string[];
  required_fix: string | null;
  resume_to_agent: string | null;
  resume_to_status: string | null;
  created_at: string | null;
  file_path: string;
}

export interface BlockersResponse {
  active_blocker: string | null;
  blocked_context: Record<string, unknown> | null;
  blockers_history: string[];
  items: BlockerItem[];
}

export interface ReviewItem {
  review_id: string | null;
  review_type: string | null;
  reviewer: string | null;
  reviewed_at: string | null;
  verdict: string | null;
  followup_required: boolean | null;
  notes: string | null;
  file_path: string;
}

export interface MetricsResponse {
  tokens: {
    total_estimate: number;
    by_agent: AgentTokenBucket;
    by_stage: Record<string, number>;
  };
  context: {
    active_chars: number;
    active_tokens_estimate: number;
    model: string | null;
    model_max_context: number;
    usage_pct: number;
    level: 'safe' | 'warning' | 'high' | 'danger';
  };
}

export class WorkspaceReader {
  constructor(private readonly projectRoot: string) {}

  private workspaceDir(): string {
    return path.join(this.projectRoot, '.ai-agents', 'workspace');
  }

  private taskDir(taskId: string): string {
    if (!TASK_ID_RE.test(taskId)) {
      throw new Error('TASK_ID_INVALID');
    }
    return path.join(this.workspaceDir(), taskId);
  }

  private safeRead(absPath: string): string {
    return fs.readFileSync(absPath, 'utf8');
  }

  // ---------- active-task ----------

  readActiveTask(): ActiveTaskInfo {
    const file = path.join(this.workspaceDir(), 'active-task.md');
    if (!fs.existsSync(file)) {
      return { active_task_id: null, last_switched_at: null, directory_exists: false };
    }
    const parsed = parseMarkdown<ActiveTaskFm>(this.safeRead(file));
    const id = parsed.frontmatter?.active_task_id ?? null;
    const directory_exists =
      typeof id === 'string' && TASK_ID_RE.test(id) && fs.existsSync(this.taskDir(id));
    return {
      active_task_id: typeof id === 'string' ? id : null,
      last_switched_at: toIsoString(parsed.frontmatter?.last_switched_at),
      directory_exists,
    };
  }

  // ---------- tasks ----------

  listTaskIds(): string[] {
    const dir = this.workspaceDir();
    if (!fs.existsSync(dir)) return [];
    return fs
      .readdirSync(dir, { withFileTypes: true })
      .filter((d) => d.isDirectory() && TASK_ID_RE.test(d.name))
      .map((d) => d.name)
      .sort();
  }

  listTasks(filter: TaskFilter = {}): TaskListItem[] {
    const ids = this.listTaskIds();
    const items = ids.map((id) => this.summarizeTask(id)).filter((t): t is TaskListItem => !!t);
    return items.filter((t) => {
      if (filter.status && t.current_status !== filter.status) return false;
      if (filter.agent && t.current_agent !== filter.agent) return false;
      if (filter.priority && t.priority !== filter.priority) return false;
      if (filter.q) {
        const q = filter.q.toLowerCase();
        const haystack = `${t.task_id} ${t.task_title ?? ''}`.toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
  }

  private summarizeTask(taskId: string): TaskListItem | null {
    const taskFile = path.join(this.taskDir(taskId), 'task.md');
    const stateFile = path.join(this.taskDir(taskId), 'state.md');
    if (!fs.existsSync(taskFile) || !fs.existsSync(stateFile)) return null;
    const task = parseMarkdown<Record<string, unknown>>(this.safeRead(taskFile)).frontmatter ?? {};
    const state = parseMarkdown<Record<string, unknown>>(this.safeRead(stateFile)).frontmatter ?? {};
    const tokenTotal = this.estimateTaskTokens(taskId);
    const blockersDir = path.join(this.taskDir(taskId), 'blockers');
    const blockerCount = fs.existsSync(blockersDir)
      ? fs.readdirSync(blockersDir).filter((f) => f.endsWith('.md')).length
      : 0;
    const produced = Array.isArray(state['produced_artifacts']) ? state['produced_artifacts'].length : 0;
    return {
      task_id: taskId,
      task_title: (task['task_title'] as string | undefined) ?? null,
      task_type: (task['task_type'] as string | undefined) ?? null,
      priority: (task['priority'] as string | undefined) ?? null,
      current_status: (state['current_status'] as string | undefined) ?? null,
      current_agent: (state['current_agent'] as string | undefined) ?? null,
      human_review_status: (state['human_review_status'] as string | undefined) ?? null,
      final_review_status: (state['final_review_status'] as string | undefined) ?? null,
      blocker_count: blockerCount,
      produced_artifacts_count: produced,
      token_total_estimate: tokenTotal,
      created_at: toIsoString(task['created_at']),
      updated_at: toIsoString(state['updated_at']),
    };
  }

  // ---------- single task ----------

  readTaskFull(taskId: string): {
    task: ParsedMarkdown;
    state: ParsedMarkdown;
    summary: TaskListItem | null;
  } {
    const taskFile = path.join(this.taskDir(taskId), 'task.md');
    const stateFile = path.join(this.taskDir(taskId), 'state.md');
    if (!fs.existsSync(taskFile) || !fs.existsSync(stateFile)) {
      throw new Error('TASK_NOT_FOUND');
    }
    return {
      task: parseMarkdown(this.safeRead(taskFile)),
      state: parseMarkdown(this.safeRead(stateFile)),
      summary: this.summarizeTask(taskId),
    };
  }

  readState(taskId: string): ParsedMarkdown {
    const file = path.join(this.taskDir(taskId), 'state.md');
    if (!fs.existsSync(file)) throw new Error('TASK_NOT_FOUND');
    return parseMarkdown(this.safeRead(file));
  }

  // ---------- artifacts tree / single file ----------

  buildArtifactsTree(taskId: string): TreeNode[] {
    const root = this.taskDir(taskId);
    if (!fs.existsSync(root)) throw new Error('TASK_NOT_FOUND');
    const subdirs = ['artifacts', 'messages', 'human-reviews', 'blockers'];
    const nodes: TreeNode[] = [];
    for (const sub of subdirs) {
      const abs = path.join(root, sub);
      if (fs.existsSync(abs) && fs.statSync(abs).isDirectory()) {
        nodes.push(this.walkDir(abs, sub));
      }
    }
    return nodes;
  }

  private walkDir(absDir: string, relPath: string): TreeDirNode {
    const entries = fs.readdirSync(absDir, { withFileTypes: true });
    const children: TreeNode[] = [];
    for (const e of entries) {
      const childAbs = path.join(absDir, e.name);
      const childRel = path.posix.join(relPath, e.name);
      if (e.isDirectory()) {
        children.push(this.walkDir(childAbs, childRel));
      } else if (e.isFile()) {
        const stat = fs.statSync(childAbs);
        children.push({ type: 'file', name: e.name, size: stat.size, path: childRel });
      }
    }
    children.sort((a, b) => a.name.localeCompare(b.name));
    return { type: 'dir', name: path.basename(absDir), path: relPath, children };
  }

  readArtifactFile(taskId: string, requestedPath: string): ArtifactFile {
    const taskRoot = this.taskDir(taskId);
    const abs = resolveSafePath(taskRoot, requestedPath);
    if (!fs.existsSync(abs)) throw new Error('ARTIFACT_NOT_FOUND');
    const result = readMarkdownWithLimit(abs);
    const parsed = parseMarkdown(result.body);
    return { path: requestedPath, ...result, parsed };
  }

  // ---------- messages ----------

  listMessages(taskId: string): MessageItem[] {
    const dir = path.join(this.taskDir(taskId), 'messages');
    if (!fs.existsSync(dir)) return [];
    const files = fs.readdirSync(dir).filter((f) => f.endsWith('.md'));
    const items: MessageItem[] = files.map((name) => {
      const abs = path.join(dir, name);
      const fm = parseMarkdown<Record<string, unknown>>(this.safeRead(abs)).frontmatter ?? {};
      const referenced = Array.isArray(fm['referenced_artifacts'])
        ? (fm['referenced_artifacts'] as string[])
        : [];
      return {
        message_id: (fm['message_id'] as string | undefined) ?? null,
        from_agent: (fm['from_agent'] as string | undefined) ?? null,
        to_agent: (fm['to_agent'] as string | undefined) ?? null,
        message_type: (fm['message_type'] as string | undefined) ?? null,
        intent: (fm['intent'] as string | undefined) ?? null,
        summary: (fm['summary'] as string | undefined) ?? null,
        referenced_artifacts: referenced,
        created_at: toIsoString(fm['created_at']),
        file_path: path.posix.join('messages', name),
      };
    });
    items.sort((a, b) => (a.created_at ?? '').localeCompare(b.created_at ?? ''));
    return items;
  }

  // ---------- blockers ----------

  readBlockers(taskId: string): BlockersResponse {
    const dir = path.join(this.taskDir(taskId), 'blockers');
    const items: BlockerItem[] = fs.existsSync(dir)
      ? fs
          .readdirSync(dir)
          .filter((f) => f.endsWith('.md'))
          .map((name) => {
            const abs = path.join(dir, name);
            const fm = parseMarkdown<Record<string, unknown>>(this.safeRead(abs)).frontmatter ?? {};
            const missing = Array.isArray(fm['missing_artifacts'])
              ? (fm['missing_artifacts'] as string[])
              : [];
            return {
              blocker_id: (fm['blocker_id'] as string | undefined) ?? null,
              blocking_reason: (fm['blocking_reason'] as string | undefined) ?? null,
              missing_artifacts: missing,
              required_fix: (fm['required_fix'] as string | undefined) ?? null,
              resume_to_agent: (fm['resume_to_agent'] as string | undefined) ?? null,
              resume_to_status: (fm['resume_to_status'] as string | undefined) ?? null,
              created_at: toIsoString(fm['created_at']),
              file_path: path.posix.join('blockers', name),
            };
          })
      : [];
    const stateFm = this.readState(taskId).frontmatter ?? {};
    return {
      active_blocker: (stateFm['active_blocker'] as string | null | undefined) ?? null,
      blocked_context:
        (stateFm['blocked_context'] as Record<string, unknown> | null | undefined) ?? null,
      blockers_history: Array.isArray(stateFm['blockers_history'])
        ? (stateFm['blockers_history'] as string[])
        : [],
      items,
    };
  }

  // ---------- human reviews ----------

  listHumanReviews(taskId: string): ReviewItem[] {
    const dir = path.join(this.taskDir(taskId), 'human-reviews');
    if (!fs.existsSync(dir)) return [];
    return fs
      .readdirSync(dir)
      .filter((f) => f.endsWith('.md'))
      .map((name) => {
        const abs = path.join(dir, name);
        const fm = parseMarkdown<Record<string, unknown>>(this.safeRead(abs)).frontmatter ?? {};
        return {
          review_id: (fm['review_id'] as string | undefined) ?? null,
          review_type: (fm['review_type'] as string | undefined) ?? null,
          reviewer: (fm['reviewer'] as string | undefined) ?? null,
          reviewed_at: toIsoString(fm['reviewed_at']),
          verdict: (fm['verdict'] as string | undefined) ?? null,
          followup_required:
            typeof fm['followup_required'] === 'boolean'
              ? (fm['followup_required'] as boolean)
              : null,
          notes: (fm['notes'] as string | undefined) ?? null,
          file_path: path.posix.join('human-reviews', name),
        };
      });
  }

  // ---------- metrics ----------

  estimateTaskTokens(taskId: string): number {
    const root = this.taskDir(taskId);
    if (!fs.existsSync(root)) return 0;
    let chars = 0;
    const subdirs = ['artifacts', 'messages', 'human-reviews', 'blockers'];
    for (const sub of subdirs) {
      const abs = path.join(root, sub);
      if (fs.existsSync(abs)) chars += this.dirCharCount(abs);
    }
    return estimateTokens(chars);
  }

  private dirCharCount(absDir: string): number {
    let chars = 0;
    for (const e of fs.readdirSync(absDir, { withFileTypes: true })) {
      const child = path.join(absDir, e.name);
      if (e.isDirectory()) chars += this.dirCharCount(child);
      else if (e.isFile()) chars += fs.statSync(child).size;
    }
    return chars;
  }

  computeMetrics(taskId: string, model: string | null, modelMaxContext: number): MetricsResponse {
    const root = this.taskDir(taskId);
    if (!fs.existsSync(root)) throw new Error('TASK_NOT_FOUND');
    const byAgent = emptyAgentBucket();
    const byStage: Record<string, number> = {};

    // by_agent: messages 按 from_agent 归口；artifacts 按 produced_by 归口
    const messages = this.listMessages(taskId);
    for (const m of messages) {
      const file = path.join(root, m.file_path);
      if (fs.existsSync(file)) {
        const size = fs.statSync(file).size;
        const role = (m.from_agent ?? 'controller') as keyof AgentTokenBucket;
        if (role in byAgent) byAgent[role] += estimateTokens(size);
      }
    }

    const artifactsRoot = path.join(root, 'artifacts');
    if (fs.existsSync(artifactsRoot)) {
      for (const sub of fs.readdirSync(artifactsRoot, { withFileTypes: true })) {
        if (!sub.isDirectory()) continue;
        const subAbs = path.join(artifactsRoot, sub.name);
        const stageChars = this.dirCharCount(subAbs);
        const stageTokens = estimateTokens(stageChars);
        byStage[sub.name] = (byStage[sub.name] ?? 0) + stageTokens;
        const role = (sub.name === 'final' ? 'controller' : sub.name) as keyof AgentTokenBucket;
        if (role in byAgent) byAgent[role] += stageTokens;
      }
    }

    const totalChars = this.dirCharCount(root);
    const totalTokens = estimateTokens(totalChars);

    const usagePct = modelMaxContext > 0 ? totalTokens / modelMaxContext : 0;
    let level: MetricsResponse['context']['level'] = 'safe';
    if (usagePct > 0.9) level = 'danger';
    else if (usagePct > 0.75) level = 'high';
    else if (usagePct > 0.5) level = 'warning';

    return {
      tokens: { total_estimate: totalTokens, by_agent: byAgent, by_stage: byStage },
      context: {
        active_chars: totalChars,
        active_tokens_estimate: totalTokens,
        model,
        model_max_context: modelMaxContext,
        usage_pct: Number(usagePct.toFixed(4)),
        level,
      },
    };
  }
}
