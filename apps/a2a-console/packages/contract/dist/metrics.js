import { z } from 'zod';
import { nullableStringSchema, taskRelativePathSchema } from './envelope.js';
const agentTokenBucketSchema = z.object({
    pm: z.number(),
    architect: z.number(),
    developer: z.number(),
    qa: z.number(),
    controller: z.number(),
    human: z.number(),
});
export const largestArtifactSchema = z.object({
    path: taskRelativePathSchema,
    size_bytes: z.number().int().nonnegative(),
    tokens_estimate: z.number().int().nonnegative(),
});
export const metricsResponseSchema = z.object({
    tokens: z.object({
        total_estimate: z.number().int().nonnegative(),
        by_agent: agentTokenBucketSchema,
        by_stage: z.record(z.number().int().nonnegative()),
    }),
    context: z.object({
        active_chars: z.number().int().nonnegative(),
        active_tokens_estimate: z.number().int().nonnegative(),
        model: nullableStringSchema,
        model_max_context: z.number().int().nonnegative(),
        usage_pct: z.number().nonnegative(),
        level: z.enum(['safe', 'warning', 'high', 'danger']),
    }),
    largest_artifacts: z.array(largestArtifactSchema).max(10),
});
//# sourceMappingURL=metrics.js.map