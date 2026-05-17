import { z } from 'zod';

import { nullableStringSchema } from './envelope.js';

export const parsedMarkdownSchema = z.object({
  frontmatter: z.record(z.unknown()).nullable(),
  body: z.string(),
  parse_error: nullableStringSchema,
});

export const taskSummarySchema = z.object({
  task_id: z.string(),
  task_title: nullableStringSchema,
  task_type: nullableStringSchema,
  priority: nullableStringSchema,
  current_status: nullableStringSchema,
  current_agent: nullableStringSchema,
  human_review_status: nullableStringSchema,
  final_review_status: nullableStringSchema,
  blocker_count: z.number().int().nonnegative(),
  produced_artifacts_count: z.number().int().nonnegative(),
  token_total_estimate: z.number().int().nonnegative(),
  created_at: nullableStringSchema,
  updated_at: nullableStringSchema,
});

export const taskDetailResponseSchema = z.object({
  task: parsedMarkdownSchema,
  state: parsedMarkdownSchema,
  summary: taskSummarySchema.nullable(),
});

export type ParsedMarkdownPayload = z.infer<typeof parsedMarkdownSchema>;
export type TaskSummary = z.infer<typeof taskSummarySchema>;
export type TaskDetailResponse = z.infer<typeof taskDetailResponseSchema>;

export const taskDownloadErrorCodeSchema = z.enum([
  'TASK_NOT_FOUND',
  'TASK_PACKAGE_TOO_LARGE',
  'PATH_TRAVERSAL',
  'PROJECT_ROOT_MISSING',
]);
export type TaskDownloadErrorCode = z.infer<typeof taskDownloadErrorCodeSchema>;
