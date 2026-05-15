import { Router } from 'express';
import { messagesResponseSchema } from '@a2a-console/contract';

import { okWithSchema, resolveProjectRoot, validateTaskIdParam, handleReaderError } from './_helpers.js';

export const messagesRouter = Router();

messagesRouter.get('/:taskId/messages', (req, res) => {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  const taskId = validateTaskIdParam(req, res);
  if (!taskId) return;
  try {
    okWithSchema(res, messagesResponseSchema, { items: ctx.reader.listMessages(taskId) });
  } catch (e) {
    handleReaderError(res, e);
  }
});
