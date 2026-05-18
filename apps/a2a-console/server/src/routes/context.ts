import { Router } from 'express';
import { contextAgentSchema, contextBuildRequestSchema } from '@a2a-console/contract';

import { fail, ok, resolveProjectRoot } from './_helpers.js';
import { buildContextPack } from '../store/context-pack-builder.js';
import { contextPackStore } from '../store/context-pack-store.js';

export const contextRouter = Router();

contextRouter.post('/build', (req, res) => {
  const parsed = contextBuildRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return fail(res, 400, 'CONTEXT_BUILD_REQUEST_INVALID', 'Invalid context build request', {
      issues: parsed.error.issues,
    });
  }
  if (parsed.data.full_context === true && !parsed.data.reason?.trim()) {
    return fail(res, 400, 'FULL_CONTEXT_REASON_REQUIRED', 'full_context=true requires a reason');
  }

  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return undefined;

  try {
    return ok(res, buildContextPack(ctx.projectRoot, parsed.data));
  } catch (e) {
    return failContextError(res, e);
  }
});

contextRouter.get('/', (req, res) => {
  const taskId = typeof req.query['task_id'] === 'string' ? req.query['task_id'] : undefined;
  const agentRaw = typeof req.query['agent'] === 'string' ? req.query['agent'] : undefined;
  const agent = agentRaw === undefined ? undefined : contextAgentSchema.safeParse(agentRaw);
  if (agentRaw !== undefined && agent?.success !== true) {
    return fail(res, 400, 'CONTEXT_AGENT_INVALID', 'agent must be pm, architect, developer, qa, fix, or security');
  }
  return ok(res, contextPackStore.list({
    taskId,
    agent: agent?.success === true ? agent.data : undefined,
  }));
});

contextRouter.get('/:packId', (req, res) => {
  const packId = req.params['packId'];
  if (typeof packId !== 'string' || packId.length === 0) {
    return fail(res, 400, 'CONTEXT_PACK_ID_INVALID', 'packId is required');
  }
  const pack = contextPackStore.get(packId);
  if (!pack) return fail(res, 404, 'CONTEXT_PACK_NOT_FOUND', `Context pack not found: ${packId}`);
  return ok(res, pack);
});

function failContextError(res: Parameters<typeof fail>[0], error: unknown): ReturnType<typeof fail> {
  const code = (error as { code?: string })?.code ?? 'CONTEXT_BUILD_FAILED';
  const message = error instanceof Error ? error.message : String(error);
  const status = code === 'TASK_NOT_FOUND' ? 404 : 400;
  return fail(res, status, code, message);
}
