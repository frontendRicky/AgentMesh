import { Router } from 'express';

import { ok, resolveProjectRoot, validateTaskIdParam, handleReaderError } from './_helpers.js';
import { readModelPresets } from '../services/model-presets-reader.js';

const MODEL_CONTEXT: Record<string, number> = {
  'gpt-5.5': 200_000,
  'gpt-5.5-mini': 128_000,
  'claude-4.6-sonnet-medium-thinking': 200_000,
  'claude-opus-4-7-thinking-high': 200_000,
  'claude-opus-4-7-thinking-medium': 200_000,
};
const DEFAULT_CTX = 200_000;

export const metricsRouter = Router();

metricsRouter.get('/:taskId/metrics', (req, res) => {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  const taskId = validateTaskIdParam(req, res);
  if (!taskId) return;
  try {
    const stateFm = ctx.reader.readState(taskId).frontmatter ?? {};
    const currentAgent = (stateFm['current_agent'] as string | undefined) ?? null;
    const presets = readModelPresets(ctx.projectRoot);
    const requestedModel = typeof req.query['model'] === 'string' ? req.query['model'] : null;
    type Role = keyof typeof presets.overrides;
    const role = (currentAgent ?? '') as Role;
    const overrideForRole =
      role && role in presets.overrides ? presets.overrides[role] : null;
    const defaultForRole =
      role && role in presets.defaults ? presets.defaults[role] : null;
    const model = requestedModel ?? overrideForRole ?? defaultForRole ?? 'gpt-5.5';
    const maxCtx = MODEL_CONTEXT[model] ?? DEFAULT_CTX;
    ok(res, ctx.reader.computeMetrics(taskId, model, maxCtx));
  } catch (e) {
    handleReaderError(res, e);
  }
});
