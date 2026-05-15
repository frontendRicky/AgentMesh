import { Router } from 'express';

import { ok, resolveProjectRoot, validateTaskIdParam, handleReaderError } from './_helpers.js';

export const humanReviewsRouter = Router();

humanReviewsRouter.get('/:taskId/human-reviews', (req, res) => {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  const taskId = validateTaskIdParam(req, res);
  if (!taskId) return;
  try {
    ok(res, { items: ctx.reader.listHumanReviews(taskId) });
  } catch (e) {
    handleReaderError(res, e);
  }
});
