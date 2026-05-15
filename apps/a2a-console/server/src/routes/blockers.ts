import { Router } from 'express';

import { ok, resolveProjectRoot, validateTaskIdParam, handleReaderError } from './_helpers.js';

export const blockersRouter = Router();

blockersRouter.get('/:taskId/blockers', (req, res) => {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  const taskId = validateTaskIdParam(req, res);
  if (!taskId) return;
  try {
    ok(res, ctx.reader.readBlockers(taskId));
  } catch (e) {
    handleReaderError(res, e);
  }
});
