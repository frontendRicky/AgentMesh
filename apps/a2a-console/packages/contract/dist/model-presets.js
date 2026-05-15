import { z } from 'zod';
import { nullableStringSchema } from './envelope.js';
const modelRoleValueSchema = z.object({
    pm: z.string(),
    architect: z.string(),
    developer: z.string(),
    qa: z.string(),
    controller: z.string(),
    risk: z.string(),
});
export const modelPresetsResponseSchema = z.object({
    overrides: z.object({
        pm: nullableStringSchema,
        architect: nullableStringSchema,
        developer: nullableStringSchema,
        qa: nullableStringSchema,
        controller: nullableStringSchema,
        risk: nullableStringSchema,
    }),
    defaults: modelRoleValueSchema,
});
//# sourceMappingURL=model-presets.js.map