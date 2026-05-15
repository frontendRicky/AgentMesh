import { Router } from 'express';

import { ok, resolveProjectRoot, validateTaskIdParam, handleReaderError } from './_helpers.js';

export const messagesRouter = Router();

messagesRouter.get('/:taskId/messages', (req, res) => {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  const taskId = validateTaskIdParam(req, res);
  if (!taskId) return;
  try {
    ok(res, { items: ctx.reader.listMessages(taskId) });
  } catch (e) {
    handleReaderError(res, e);
  }
});
