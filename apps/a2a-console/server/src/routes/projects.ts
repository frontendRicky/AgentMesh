import { Router } from 'express';
import { z } from 'zod';

import { fail, ok } from './_helpers.js';
import { projectRegistry } from '../store/project-registry.js';

export const projectsRouter = Router();

const projectTypeSchema = z.enum([
  'self_upgrade',
  'client_project',
  'generated_project',
  'maintenance',
]);

const automationModeSchema = z.enum([
  'manual',
  'assisted',
  'selective_auto',
  'full_auto',
]);

const createProjectRequestSchema = z.object({
  project_id: z.string().min(1).optional(),
  project_name: z.string().min(1),
  project_root: z.string().min(1),
  project_type: projectTypeSchema,
  automation_mode: automationModeSchema.default('assisted'),
  max_parallel_runs: z.number().int().positive().default(2),
  allowed_paths: z.array(z.string()).default([]),
  blocked_paths: z.array(z.string()).default(['.env', '*.env', '.github/**', 'secrets/**']),
}).strict();

projectsRouter.get('/', (_req, res) => {
  return ok(res, projectRegistry.list());
});

projectsRouter.post('/', (req, res) => {
  const parsed = createProjectRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return fail(res, 400, 'PROJECT_REQUEST_INVALID', 'Invalid project request', {
      issues: parsed.error.issues,
    });
  }

  const result = projectRegistry.add(parsed.data);
  if (!result.ok) {
    return fail(res, result.code === 'SELF_UPGRADE_EXISTS' ? 409 : 400, result.code, result.message);
  }

  res.status(201);
  return ok(res, result.project);
});

projectsRouter.get('/:projectId', (req, res) => {
  const projectId = req.params['projectId'];
  if (typeof projectId !== 'string' || projectId.length === 0) {
    return fail(res, 400, 'PROJECT_ID_INVALID', 'projectId is required');
  }

  const project = projectRegistry.get(projectId);
  if (!project) {
    return fail(res, 404, 'PROJECT_NOT_FOUND', `Project not found: ${projectId}`);
  }
  return ok(res, project);
});

projectsRouter.delete('/:projectId', (req, res) => {
  const projectId = req.params['projectId'];
  if (typeof projectId !== 'string' || projectId.length === 0) {
    return fail(res, 400, 'PROJECT_ID_INVALID', 'projectId is required');
  }

  projectRegistry.remove(projectId);
  return res.status(204).send();
});
