import type { Request, Response } from 'express';

import { loadConfig } from '../config/config-store.js';
import { validateProjectRoot } from '../lib/path-guard.js';
import { WorkspaceReader } from '../services/workspace-reader.js';

const TASK_ID_RE = /^T-\d{4}-\d{3}$/;

export interface ResolvedContext {
  projectRoot: string;
  reader: WorkspaceReader;
}

export function ok<T>(res: Response, data: T): Response {
  return res.json({ ok: true, data });
}

export function fail(
  res: Response,
  status: number,
  code: string,
  message: string,
  details?: unknown,
): Response {
  return res.status(status).json({ ok: false, error: { code, message, details } });
}

export function resolveProjectRoot(_req: Request, res: Response): ResolvedContext | null {
  const config = loadConfig();
  if (!config.project_root) {
    fail(res, 400, 'PROJECT_ROOT_MISSING', 'project_root not configured');
    return null;
  }
  try {
    const real = validateProjectRoot(config.project_root);
    return { projectRoot: real, reader: new WorkspaceReader(real) };
  } catch (e) {
    const code = (e as { code?: string })?.code ?? 'PROJECT_ROOT_INVALID';
    fail(res, 400, code, e instanceof Error ? e.message : String(e));
    return null;
  }
}

export function validateTaskIdParam(req: Request, res: Response): string | null {
  const id = req.params['taskId'];
  if (typeof id !== 'string' || !TASK_ID_RE.test(id)) {
    fail(res, 400, 'TASK_ID_INVALID', 'taskId must match ^T-\\d{4}-\\d{3}$');
    return null;
  }
  return id;
}

export function handleReaderError(res: Response, e: unknown): void {
  const code = (e as { code?: string })?.code;
  const msg = e instanceof Error ? e.message : String(e);
  if (msg === 'TASK_NOT_FOUND') return void fail(res, 404, 'TASK_NOT_FOUND', msg);
  if (msg === 'ARTIFACT_NOT_FOUND') return void fail(res, 404, 'ARTIFACT_NOT_FOUND', msg);
  if (msg === 'TASK_ID_INVALID') return void fail(res, 400, 'TASK_ID_INVALID', msg);
  if (code === 'PATH_TRAVERSAL') return void fail(res, 400, 'PATH_TRAVERSAL', msg);
  fail(res, 500, 'INTERNAL_ERROR', msg);
}
