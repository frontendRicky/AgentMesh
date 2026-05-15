import { Router } from 'express';

import { ok, resolveProjectRoot, handleReaderError } from './_helpers.js';
import { readModelPresets } from '../services/model-presets-reader.js';

export const modelPresetsRouter = Router();

modelPresetsRouter.get('/', (req, res) => {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  try {
    ok(res, readModelPresets(ctx.projectRoot));
  } catch (e) {
    handleReaderError(res, e);
  }
});
