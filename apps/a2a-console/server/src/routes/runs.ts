import { Router } from 'express';
import { z } from 'zod';

import { fail, ok } from './_helpers.js';

export const runsRouter = Router();

const TASK_ID_RE = /^T-\d{4}-\d{3}$/;

const runStatusSchema = z.enum([
  'queued',
  'running',
  'paused',
  'cancelled',
  'completed',
  'failed',
]);

const createRunRequestSchema = z.object({
  task_id: z.string().regex(TASK_ID_RE),
  agent: z.string().min(1),
  model: z.string().min(1).optional(),
}).strict();

const runActionSchema = z.enum(['pause', 'resume', 'cancel']);

type RunStatus = z.infer<typeof runStatusSchema>;
type RunAction = z.infer<typeof runActionSchema>;

interface RunSession {
  run_id: string;
  task_id: string;
  status: RunStatus;
  agent: string;
  model: string;
  created_at: string;
  updated_at: string;
  error_message?: string;
}

const runs = new Map<string, RunSession>();
let runSeq = 0;

runsRouter.get('/', (req, res) => {
  const taskId = typeof req.query['task_id'] === 'string' ? req.query['task_id'] : null;
  if (taskId !== null && !TASK_ID_RE.test(taskId)) {
    return fail(res, 400, 'TASK_ID_INVALID', 'task_id must match ^T-\\d{4}-\\d{3}$');
  }

  const items = Array.from(runs.values()).filter((run) => {
    return taskId === null || run.task_id === taskId;
  });
  return ok(res, items);
});

runsRouter.post('/', (req, res) => {
  const parsed = createRunRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return fail(res, 400, 'RUN_REQUEST_INVALID', 'Invalid run request', {
      issues: parsed.error.issues,
    });
  }

  const now = new Date().toISOString();
  const run: RunSession = {
    run_id: createRunId(),
    task_id: parsed.data.task_id,
    status: 'queued',
    agent: parsed.data.agent,
    model: parsed.data.model ?? 'default',
    created_at: now,
    updated_at: now,
  };

  runs.set(run.run_id, run);
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

  const run = runs.get(runId);
  if (!run) {
    return fail(res, 404, 'RUN_NOT_FOUND', `Run not found: ${runId}`);
  }

  run.status = statusForAction(actionResult.action);
  run.updated_at = new Date().toISOString();
  runs.set(runId, run);
  return ok(res, run);
});

function createRunId(): string {
  runSeq += 1;
  return `R-${Date.now()}-${String(runSeq).padStart(4, '0')}`;
}

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
