import {
  projectGeneratorDraftRequestSchema,
  projectGeneratorDraftResponseSchema,
  projectGeneratorTaskCreateRequestSchema,
  projectGeneratorTaskCreateResponseSchema,
  projectGeneratorTemplatesResponseSchema,
  type ProjectGeneratorDraftId,
  type ProjectGeneratorDraftRequest,
} from '@a2a-console/contract';

import { apiGet, apiPost } from './useApi';

export function getProjectGeneratorTemplates() {
  return apiGet('/api/a2a/project-generator/templates', projectGeneratorTemplatesResponseSchema);
}

export function createProjectGeneratorDraft(payload: ProjectGeneratorDraftRequest) {
  const parsed = projectGeneratorDraftRequestSchema.safeParse(payload);
  if (!parsed.success) {
    return Promise.reject({
      code: 'REQUEST_VALIDATION_FAILED',
      message: '请检查项目名称、业务说明和模型选择。',
    });
  }
  return apiPost(
    '/api/a2a/project-generator/drafts',
    parsed.data,
    projectGeneratorDraftResponseSchema,
  );
}

export function createProjectGeneratorTask(draftId: ProjectGeneratorDraftId, slug: string) {
  const parsed = projectGeneratorTaskCreateRequestSchema.safeParse({ slug });
  if (!parsed.success) {
    return Promise.reject({
      code: 'TASK_SLUG_INVALID',
      message: '任务短名只能用小写字母、数字和中横线，最多 40 个字符。',
    });
  }
  return apiPost(
    `/api/a2a/project-generator/drafts/${draftId}/tasks`,
    parsed.data,
    projectGeneratorTaskCreateResponseSchema,
  );
}
