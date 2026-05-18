import { Router } from 'express';
import fs from 'node:fs';
import path from 'node:path';
import { sandboxInitRequestSchema } from '@a2a-console/contract';

import { fail, ok } from './_helpers.js';
import { projectRegistry, type Project } from '../store/project-registry.js';
import {
  applySandbox,
  diffSandbox,
  initSandbox,
  rollbackSandbox,
} from '../store/sandbox-store.js';

export const sandboxRouter = Router();

sandboxRouter.post('/init', (req, res) => {
  const parsed = sandboxInitRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return fail(res, 400, 'SANDBOX_INIT_REQUEST_INVALID', 'Invalid sandbox init request', {
      issues: parsed.error.issues,
    });
  }

  const project = projectRegistry.get(parsed.data.project_id);
  if (!project) {
    return fail(res, 404, 'PROJECT_NOT_FOUND', `Project not found: ${parsed.data.project_id}`);
  }

  try {
    return ok(res, initSandbox(parsed.data.run_id, project, parsed.data.source_files));
  } catch (e) {
    return failSandboxError(res, e);
  }
});

sandboxRouter.get('/:runId/diff', (req, res) => {
  const context = findSandboxProject(req.params['runId']);
  if (!context) return fail(res, 404, 'SANDBOX_NOT_FOUND', 'Sandbox not found');
  try {
    return ok(res, diffSandbox(context.runId, context.project.project_root));
  } catch (e) {
    return failSandboxError(res, e);
  }
});

sandboxRouter.post('/:runId/apply', (req, res) => {
  const context = findSandboxProject(req.params['runId']);
  if (!context) return fail(res, 404, 'SANDBOX_NOT_FOUND', 'Sandbox not found');
  try {
    return ok(res, applySandbox(context.runId, context.project.project_root));
  } catch (e) {
    return failSandboxError(res, e);
  }
});

sandboxRouter.post('/:runId/rollback', (req, res) => {
  const context = findSandboxProject(req.params['runId']);
  if (!context) return fail(res, 404, 'SANDBOX_NOT_FOUND', 'Sandbox not found');
  try {
    return ok(res, rollbackSandbox(context.runId, context.project.project_root));
  } catch (e) {
    return failSandboxError(res, e);
  }
});

function findSandboxProject(runIdRaw: unknown): { runId: string; project: Project } | null {
  if (typeof runIdRaw !== 'string' || runIdRaw.length === 0) return null;
  for (const project of projectRegistry.list()) {
    const snapshot = path.join(project.project_root, '.agentmesh', 'runs', runIdRaw, 'snapshot.json');
    if (fs.existsSync(snapshot)) {
      return { runId: runIdRaw, project };
    }
  }
  return null;
}

function failSandboxError(res: Parameters<typeof fail>[0], error: unknown): ReturnType<typeof fail> {
  const code = (error as { code?: string })?.code ?? 'SANDBOX_FAILED';
  const message = error instanceof Error ? error.message : String(error);
  const status = code === 'LOCK_WAITING' || code === 'SANDBOX_DIRTY' ? 409 : 400;
  return fail(res, status, code, message);
}
