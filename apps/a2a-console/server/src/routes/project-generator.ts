import { Router } from 'express';
import {
  projectGeneratorDraftIdSchema,
  projectGeneratorDraftRequestSchema,
  projectGeneratorDraftResponseSchema,
  projectGeneratorTaskCreateRequestSchema,
  projectGeneratorTaskCreateResponseSchema,
  projectGeneratorTemplatesResponseSchema,
} from '@a2a-console/contract';

import { fail, okWithSchema, resolveProjectRoot } from './_helpers.js';
import { createProjectDraft, createTaskFromDraft, ProjectGeneratorError } from '../services/project-generator.js';
import { PROJECT_GENERATOR_TEMPLATES } from '../services/project-generator-templates.js';

export const projectGeneratorRouter = Router();

projectGeneratorRouter.get('/templates', (_req, res) => {
  return okWithSchema(res, projectGeneratorTemplatesResponseSchema, {
    items: PROJECT_GENERATOR_TEMPLATES,
  });
});

projectGeneratorRouter.post('/drafts', (req, res) => {
  const parsed = projectGeneratorDraftRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return fail(res, 400, 'REQUEST_VALIDATION_FAILED', 'project generator draft request failed validation', {
      issues: parsed.error.issues,
    });
  }

  const draft = createProjectDraft(parsed.data);
  return okWithSchema(res, projectGeneratorDraftResponseSchema, draft);
});

projectGeneratorRouter.post('/drafts/:draftId/tasks', (req, res) => {
  const draftIdResult = projectGeneratorDraftIdSchema.safeParse(req.params['draftId']);
  if (!draftIdResult.success) {
    return fail(res, 400, 'DRAFT_ID_INVALID', 'draftId must match ^D-\\d{4}-004-\\d{3}$');
  }

  const parsed = projectGeneratorTaskCreateRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return fail(res, 400, 'REQUEST_VALIDATION_FAILED', 'task create request failed validation', {
      issues: parsed.error.issues,
    });
  }

  const ctx = resolveProjectRoot(req, res);
  if (!ctx) return;

  try {
    const result = createTaskFromDraft(ctx.projectRoot, draftIdResult.data, parsed.data);
    return okWithSchema(res, projectGeneratorTaskCreateResponseSchema, result);
  } catch (e) {
    if (e instanceof ProjectGeneratorError) {
      return fail(res, e.status, e.code, e.message, e.details);
    }
    const code = (e as { code?: string })?.code;
    if (code === 'PATH_TRAVERSAL') {
      return fail(res, 400, 'PATH_TRAVERSAL', e instanceof Error ? e.message : String(e));
    }
    return fail(res, 500, 'PROJECT_GENERATOR_WRITE_FAILED', e instanceof Error ? e.message : String(e));
  }
});
