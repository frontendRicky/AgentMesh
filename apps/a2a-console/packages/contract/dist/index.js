import { z } from 'zod';
import { nullableStringSchema, taskRelativePathSchema, } from './envelope.js';
export * from './envelope.js';
export * from './tasks.js';
export * from './messages.js';
export * from './metrics.js';
export * from './reviews.js';
export * from './model-presets.js';
export * from './runs.js';
export * from './projects.js';
export * from './usage.js';
export * from './policy.js';
export * from './context.js';
export * from './sandbox.js';
export * from './test.js';
export const projectGeneratorTaskIdSchema = z.string().regex(/^T-\d{4}-\d{3}$/);
export const projectGeneratorDraftIdSchema = z.string().regex(/^D-\d{4}-004-\d{3}$/);
export const projectGeneratorSlugSchema = z.string().regex(/^[a-z0-9-]{1,40}$/);
export const projectGeneratorProjectTypeSchema = z.enum([
    'business-dashboard',
    'admin-system',
    'marketing-site',
    'mobile-h5',
    'data-report',
    'custom',
]);
export const projectGeneratorStrategySchema = z.enum([
    'quick',
    'quality',
    'budget',
    'strict',
]);
export const projectGeneratorModelProfileSchema = z.enum([
    'recommended',
    'faster',
    'stronger',
    'cheaper',
    'custom',
]);
export const projectGeneratorApiModeSchema = z.enum(['mock', 'real', 'unknown']);
export const projectGeneratorTemplateSchema = z.object({
    id: projectGeneratorProjectTypeSchema,
    name: z.string(),
    description: z.string(),
    examples: z.array(z.string()),
    recommended_strategy: projectGeneratorStrategySchema,
});
export const projectGeneratorTemplatesResponseSchema = z.object({
    items: z.array(projectGeneratorTemplateSchema),
});
export const projectGeneratorDraftRequestSchema = z.object({
    project_name: z.string().min(1).max(80),
    project_type: projectGeneratorProjectTypeSchema,
    business_description: z.string().min(10).max(4000),
    target_users: z.string().max(1000).default(''),
    pages: z.array(z.string().min(1).max(60)).max(12).default([]),
    style_preference: z.string().max(1000).default(''),
    data_source: z.string().max(1000).default(''),
    generation_strategy: projectGeneratorStrategySchema,
    model_profile: projectGeneratorModelProfileSchema,
    api_mode: projectGeneratorApiModeSchema.default('mock'),
    needs_auth: z.boolean().default(false),
    needs_charts: z.boolean().default(false),
}).strict();
export const projectGeneratorDraftResponseSchema = z.object({
    draft_id: projectGeneratorDraftIdSchema,
    summary: z.string(),
    prd_preview: z.string(),
    openspec_preview: z.string(),
    model_snapshot_preview: z.string(),
});
export const projectGeneratorTaskCreateRequestSchema = z.object({
    slug: projectGeneratorSlugSchema,
}).strict();
export const projectGeneratorTaskCreateResponseSchema = z.object({
    task_id: projectGeneratorTaskIdSchema,
    task_path: z.string().regex(/^\.ai-agents\/workspace\/T-\d{4}-\d{3}$/),
    created_files: z.array(taskRelativePathSchema),
    model_snapshot_path: taskRelativePathSchema,
    next_step: z.literal('handoff_to_technical_owner'),
});
// Schema-only runner placeholder. No server route may be registered for this in T-2026-004.
export const projectGeneratorJobStatusSchema = z.object({
    task_id: projectGeneratorTaskIdSchema,
    status: z.enum(['not_started', 'queued', 'running', 'succeeded', 'failed']),
    message: nullableStringSchema,
    updated_at: nullableStringSchema,
});
//# sourceMappingURL=index.js.map