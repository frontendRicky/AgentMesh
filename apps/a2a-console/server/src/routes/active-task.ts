import { Router } from 'express';

import { ok, resolveProjectRoot, handleReaderError } from './_helpers.js';

export const activeTaskRouter = Router();

activeTaskRouter.get('/', (req, res) => {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  try {
    ok(res, ctx.reader.readActiveTask());
  } catch (e) {
    handleReaderError(res, e);
  }
});
