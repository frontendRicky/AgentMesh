import { Router } from 'express';
import { taskDetailResponseSchema } from '@a2a-console/contract';

import { ok, okWithSchema, resolveProjectRoot, validateTaskIdParam, handleReaderError } from './_helpers.js';

export const taskDetailRouter = Router();

taskDetailRouter.get('/:taskId', (req, res) => {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  const taskId = validateTaskIdParam(req, res);
  if (!taskId) return;
  try {
    okWithSchema(res, taskDetailResponseSchema, ctx.reader.readTaskFull(taskId));
  } catch (e) {
    handleReaderError(res, e);
  }
});

taskDetailRouter.get('/:taskId/state', (req, res) => {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  const taskId = validateTaskIdParam(req, res);
  if (!taskId) return;
  try {
    ok(res, ctx.reader.readState(taskId));
  } catch (e) {
    handleReaderError(res, e);
  }
});
