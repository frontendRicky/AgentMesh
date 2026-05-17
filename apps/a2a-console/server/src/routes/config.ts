import { Router } from 'express';
import { z } from 'zod';

import { fail, ok } from './_helpers.js';
import { loadConfig, saveConfig } from '../config/config-store.js';
import { validateProjectRoot } from '../lib/path-guard.js';
import { logger } from '../lib/logger.js';

export const configRouter = Router();

configRouter.get('/', (_req, res) => {
  ok(res, loadConfig());
});

const projectRootBody = z.object({
  project_root: z.string().min(1),
});

configRouter.post('/project-root', (req, res) => {
  const parsed = projectRootBody.safeParse(req.body);
  if (!parsed.success) {
    return fail(res, 400, 'PROJECT_ROOT_INVALID', 'project_root must be a non-empty string');
  }
  try {
    const real = validateProjectRoot(parsed.data.project_root);
    const config = loadConfig();
    config.project_root = real;
    saveConfig(config);
    logger.info(`project_root updated to ${real}`);
    return ok(res, { project_root: real, valid: true });
  } catch (e) {
    const code = (e as { code?: string })?.code ?? 'PROJECT_ROOT_INVALID';
    return fail(res, 400, code, e instanceof Error ? e.message : String(e));
  }
});

configRouter.get('/project-root', (_req, res) => {
  const config = loadConfig();
  ok(res, { project_root: config.project_root });
});
