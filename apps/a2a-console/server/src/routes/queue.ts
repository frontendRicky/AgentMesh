import { Router } from 'express';
import { z } from 'zod';

import { fail, ok } from './_helpers.js';
import { runPool } from '../store/run-pool.js';
import { taskQueue } from '../store/task-queue.js';

export const queueRouter = Router();

const TASK_ID_RE = /^T-\d{4}-\d{3}$/;
const prioritySchema = z.enum(['urgent', 'high', 'normal', 'background']);

const enqueueRequestSchema = z.object({
  task_id: z.string().regex(TASK_ID_RE),
  priority: prioritySchema.default('normal'),
}).strict();

queueRouter.get('/', (_req, res) => {
  return ok(res, taskQueue.list());
});

queueRouter.post('/', (req, res) => {
  const parsed = enqueueRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return fail(res, 400, 'QUEUE_REQUEST_INVALID', 'Invalid queue request', {
      issues: parsed.error.issues,
    });
  }

  const queued = taskQueue.enqueue(parsed.data.task_id, parsed.data.priority);
  if (!queued) {
    return fail(res, 409, 'TASK_ALREADY_QUEUED', `Task already queued: ${parsed.data.task_id}`);
  }

  runPool.add({
    task_id: parsed.data.task_id,
    status: 'queued',
    priority: parsed.data.priority,
    agent: 'scheduler',
    model: 'default',
  });

  res.status(201);
  return ok(res, { position: queued.position });
});

queueRouter.delete('/:task_id', (req, res) => {
  const taskId = req.params['task_id'];
  if (typeof taskId !== 'string' || !TASK_ID_RE.test(taskId)) {
    return fail(res, 400, 'TASK_ID_INVALID', 'task_id must match ^T-\\d{4}-\\d{3}$');
  }

  taskQueue.remove(taskId);
  const queuedRun = runPool.list(taskId).find((run) => run.status === 'queued');
  if (queuedRun) {
    runPool.update(queuedRun.run_id, { status: 'cancelled' });
  }
  return res.status(204).send();
});
