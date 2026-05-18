import { Router } from 'express';
import { testRunRequestSchema } from '@a2a-console/contract';

import { fail, ok } from './_helpers.js';
import { projectRegistry } from '../store/project-registry.js';
import { readTestResults, runTestSuites } from '../store/test-runner.js';

export const testRouter = Router();

testRouter.post('/run', async (req, res) => {
  const parsed = testRunRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    const hasSuiteIssue = parsed.error.issues.some((issue) => issue.path.includes('suites'));
    return fail(
      res,
      400,
      hasSuiteIssue ? 'INVALID_SUITE' : 'TEST_RUN_REQUEST_INVALID',
      hasSuiteIssue ? 'Invalid test suite' : 'Invalid test run request',
      { issues: parsed.error.issues },
    );
  }

  const project = projectRegistry.get(parsed.data.project_id);
  if (!project) {
    return fail(res, 404, 'PROJECT_NOT_FOUND', `Project not found: ${parsed.data.project_id}`);
  }

  try {
    const results = await runTestSuites(parsed.data.run_id, project, parsed.data.suites);
    return ok(res, {
      run_id: parsed.data.run_id,
      project_id: parsed.data.project_id,
      results,
    });
  } catch (e) {
    return failTestError(res, e);
  }
});

testRouter.get('/:runId', (req, res) => {
  const runId = req.params['runId'];
  const projectId = typeof req.query['project_id'] === 'string' ? req.query['project_id'] : null;
  if (typeof runId !== 'string' || runId.length === 0) {
    return fail(res, 400, 'RUN_ID_INVALID', 'runId is required');
  }
  if (!projectId) {
    return fail(res, 400, 'PROJECT_ID_REQUIRED', 'project_id query is required');
  }
  const project = projectRegistry.get(projectId);
  if (!project) return fail(res, 404, 'PROJECT_NOT_FOUND', `Project not found: ${projectId}`);
  return ok(res, {
    run_id: runId,
    project_id: projectId,
    results: readTestResults(project, runId),
  });
});

function failTestError(res: Parameters<typeof fail>[0], error: unknown): ReturnType<typeof fail> {
  const code = (error as { code?: string })?.code ?? 'TEST_RUN_FAILED';
  const message = error instanceof Error ? error.message : String(error);
  const status = code === 'TEST_SCRIPT_NOT_FOUND' || code === 'PACKAGE_JSON_NOT_FOUND' ? 400 : 500;
  return fail(res, status, code, message);
}
