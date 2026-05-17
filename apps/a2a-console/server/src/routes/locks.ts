import { Router } from 'express';
import { z } from 'zod';

import { fail, ok } from './_helpers.js';
import { lockManager } from '../store/lock-manager.js';

export const locksRouter = Router();

const acquireRequestSchema = z.object({
  run_id: z.string().min(1),
  paths: z.array(z.string().min(1)).default([]),
}).strict();

const releaseRequestSchema = z.object({
  run_id: z.string().min(1),
}).strict();

locksRouter.get('/', (_req, res) => {
  return ok(res, lockManager.listLocks());
});

locksRouter.post('/acquire', (req, res) => {
  const parsed = acquireRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return fail(res, 400, 'LOCK_REQUEST_INVALID', 'Invalid lock acquire request', {
      issues: parsed.error.issues,
    });
  }

  const waitingOn = lockManager.waitingOn(parsed.data.run_id, parsed.data.paths);
  const result = lockManager.acquire(parsed.data.run_id, parsed.data.paths);
  return ok(res, {
    result,
    waiting_on: result === 'waiting' ? waitingOn : [],
  });
});

locksRouter.post('/release', (req, res) => {
  const parsed = releaseRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return fail(res, 400, 'LOCK_REQUEST_INVALID', 'Invalid lock release request', {
      issues: parsed.error.issues,
    });
  }

  lockManager.release(parsed.data.run_id);
  return res.status(204).send();
});
