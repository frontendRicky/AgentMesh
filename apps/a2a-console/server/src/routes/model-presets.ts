import { Router } from 'express';
import { modelPresetsResponseSchema } from '@a2a-console/contract';

import { okWithSchema, resolveProjectRoot, handleReaderError } from './_helpers.js';
import { readModelPresets } from '../services/model-presets-reader.js';

export const modelPresetsRouter = Router();

modelPresetsRouter.get('/', (req, res) => {
  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;
  try {
    okWithSchema(res, modelPresetsResponseSchema, readModelPresets(ctx.projectRoot));
  } catch (e) {
    handleReaderError(res, e);
  }
});
