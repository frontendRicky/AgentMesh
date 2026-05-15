import { Router } from 'express';

import { ok, resolveProjectRoot, handleReaderError } from './_helpers.js';

export const tasksRouter = Router();

tasksRouter.get('/', (req, res) => {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  try {
    const status = typeof req.query['status'] === 'string' ? req.query['status'] : undefined;
    const agent = typeof req.query['agent'] === 'string' ? req.query['agent'] : undefined;
    const priority = typeof req.query['priority'] === 'string' ? req.query['priority'] : undefined;
    const q = typeof req.query['q'] === 'string' ? req.query['q'] : undefined;
    const items = ctx.reader.listTasks({ status, agent, priority, q });
    ok(res, { total: items.length, items });
  } catch (e) {
    handleReaderError(res, e);
  }
});
