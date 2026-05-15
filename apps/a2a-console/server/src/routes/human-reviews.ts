import { Router } from 'express';
import type { Request, Response } from 'express';
import { reviewsResponseSchema } from '@a2a-console/contract';

import { okWithSchema, resolveProjectRoot, validateTaskIdParam, handleReaderError } from './_helpers.js';

export const humanReviewsRouter = Router();

function getReviews(req: Request, res: Response) {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  const taskId = validateTaskIdParam(req, res);
  if (!taskId) return;
  try {
    okWithSchema(res, reviewsResponseSchema, { items: ctx.reader.listHumanReviews(taskId) });
  } catch (e) {
    handleReaderError(res, e);
  }
}

humanReviewsRouter.get('/:taskId/reviews', getReviews);
humanReviewsRouter.get('/:taskId/human-reviews', getReviews);
