import { Router } from 'express';
import { z } from 'zod';

import { fail, ok } from './_helpers.js';
import { runPool, type RunPriority, type RunStatus } from '../store/run-pool.js';

export const runsRouter = Router();

const TASK_ID_RE = /^T-\d{4}-\d{3}$/;

const runPrioritySchema = z.enum(['urgent', 'high', 'normal', 'background']);

const createRunRequestSchema = z.object({
  task_id: z.string().regex(TASK_ID_RE),
  agent: z.string().min(1),
  model: z.string().min(1).optional(),
  priority: runPrioritySchema.optional(),
}).strict();

const runActionSchema = z.enum(['pause', 'resume', 'cancel']);

type RunAction = z.infer<typeof runActionSchema>;

runsRouter.get('/', (req, res) => {
  const taskId = typeof req.query['task_id'] === 'string' ? req.query['task_id'] : null;
  if (taskId !== null && !TASK_ID_RE.test(taskId)) {
    return fail(res, 400, 'TASK_ID_INVALID', 'task_id must match ^T-\\d{4}-\\d{3}$');
  }

  return ok(res, runPool.list(taskId ?? undefined));
});

runsRouter.post('/', (req, res) => {
  const parsed = createRunRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return fail(res, 400, 'RUN_REQUEST_INVALID', 'Invalid run request', {
      issues: parsed.error.issues,
    });
  }

  const run = runPool.add({
    task_id: parsed.data.task_id,
    status: 'queued',
    priority: parsed.data.priority ?? 'normal',
    agent: parsed.data.agent,
    model: parsed.data.model ?? 'default',
  });

  res.status(201);
  return ok(res, run);
});

runsRouter.patch('/:runId', (req, res) => {
  const runId = req.params['runId'];
  if (typeof runId !== 'string' || runId.length === 0) {
    return fail(res, 400, 'RUN_ID_INVALID', 'runId is required');
  }

  const actionResult = parseRunAction(req.query['action'], req.body);
  if (!actionResult.success) {
    return fail(res, 400, 'RUN_ACTION_INVALID', actionResult.message);
  }

  const run = runPool.get(runId);
  if (!run) {
    return fail(res, 404, 'RUN_NOT_FOUND', `Run not found: ${runId}`);
  }

  const next = runPool.update(runId, { status: statusForAction(actionResult.action) });
  return ok(res, next ?? run);
});

function parseRunAction(
  queryAction: unknown,
  body: unknown,
): { success: true; action: RunAction } | { success: false; message: string } {
  const candidate = typeof queryAction === 'string'
    ? queryAction
    : readBodyAction(body);
  const parsed = runActionSchema.safeParse(candidate);
  if (!parsed.success) {
    return { success: false, message: 'action must be pause, resume, or cancel' };
  }
  return { success: true, action: parsed.data };
}

function readBodyAction(body: unknown): unknown {
  if (body === null || typeof body !== 'object') return undefined;
  if (!('action' in body)) return undefined;
  return body.action;
}

function statusForAction(action: RunAction): RunStatus {
  if (action === 'pause') return 'paused';
  if (action === 'resume') return 'running';
  return 'cancelled';
}

export function parseRunPriority(value: unknown): RunPriority | null {
  const parsed = runPrioritySchema.safeParse(value);
  return parsed.success ? parsed.data : null;
}
