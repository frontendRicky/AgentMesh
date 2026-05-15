import { Router } from 'express';

import { ok, resolveProjectRoot, validateTaskIdParam, handleReaderError } from './_helpers.js';

export const artifactsRouter = Router();

artifactsRouter.get('/:taskId/artifacts', (req, res) => {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  const taskId = validateTaskIdParam(req, res);
  if (!taskId) return;
  try {
    const requestedPath = req.query['path'];
    if (typeof requestedPath === 'string' && requestedPath.length > 0) {
      ok(res, ctx.reader.readArtifactFile(taskId, requestedPath));
      return;
    }
    ok(res, { tree: ctx.reader.buildArtifactsTree(taskId) });
  } catch (e) {
    handleReaderError(res, e);
  }
});
