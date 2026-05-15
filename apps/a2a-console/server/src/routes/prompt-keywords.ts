import { Router } from 'express';

import { ok, resolveProjectRoot, validateTaskIdParam, handleReaderError } from './_helpers.js';
import { readModelPresets } from '../services/model-presets-reader.js';

interface Keyword {
  keyword: string;
  ui_action: 'copy' | 'show_only' | 'link';
  cli_role: string | null;
  hint?: string;
}

const STATUS_TO_KEYWORD: Record<string, Keyword> = {
  created: { keyword: 'prompt controller', ui_action: 'copy', cli_role: 'controller' },
  pm_processing: { keyword: 'prompt pm', ui_action: 'copy', cli_role: 'pm' },
  pm_completed: { keyword: 'prompt controller', ui_action: 'copy', cli_role: 'controller' },
  architect_processing: {
    keyword: 'prompt architect',
    ui_action: 'copy',
    cli_role: 'architect',
  },
  architect_completed: {
    keyword: 'prompt controller',
    ui_action: 'copy',
    cli_role: 'controller',
  },
  human_review_required: {
    keyword: '',
    ui_action: 'show_only',
    cli_role: null,
    hint: '请在 Cursor 中代写 architect-review.md 后让 Controller 推进',
  },
  developer_processing: {
    keyword: 'prompt developer',
    ui_action: 'copy',
    cli_role: 'developer',
  },
  developer_completed: {
    keyword: 'prompt controller',
    ui_action: 'copy',
    cli_role: 'controller',
  },
  qa_processing: { keyword: 'prompt qa', ui_action: 'copy', cli_role: 'qa' },
  qa_completed: { keyword: 'prompt controller', ui_action: 'copy', cli_role: 'controller' },
  final_review_required: {
    keyword: '',
    ui_action: 'show_only',
    cli_role: null,
    hint: '请在 Cursor 中代写 final-review.md 后让 Controller 推进',
  },
  completed: {
    keyword: '',
    ui_action: 'link',
    cli_role: null,
    hint: '查看 artifacts/final/final-delivery.md',
  },
  blocked: { keyword: 'prompt controller', ui_action: 'copy', cli_role: 'controller' },
  cancelled: { keyword: '', ui_action: 'show_only', cli_role: null, hint: 'Task 已取消' },
};

export const promptKeywordsRouter = Router();

promptKeywordsRouter.get('/:taskId/prompt-keywords', (req, res) => {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  const taskId = validateTaskIdParam(req, res);
  if (!taskId) return;
  try {
    const stateFm = ctx.reader.readState(taskId).frontmatter ?? {};
    const status = (stateFm['current_status'] as string | undefined) ?? 'created';
    const cfg = STATUS_TO_KEYWORD[status] ?? STATUS_TO_KEYWORD['created']!;
    const presets = readModelPresets(ctx.projectRoot);
    type Role = keyof typeof presets.overrides;
    const role = cfg.cli_role as Role | null;
    const recommended = role
      ? presets.overrides[role] ?? presets.defaults[role] ?? null
      : null;
    const cli =
      cfg.cli_role && cfg.keyword
        ? `a2a-agent --project-root "${ctx.projectRoot}" ${cfg.keyword}` +
          (recommended ? ` --model ${recommended}` : '')
        : '';
    ok(res, {
      current_status: status,
      keyword: cfg.keyword,
      cli_command: cli,
      ui_action: cfg.ui_action,
      hint: cfg.hint ?? null,
      cli_role: cfg.cli_role,
      model_recommended: recommended,
    });
  } catch (e) {
    handleReaderError(res, e);
  }
});
