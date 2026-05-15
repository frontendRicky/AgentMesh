import { z } from 'zod';
import { nullableStringSchema, taskRelativePathSchema } from './envelope.js';
export const messageItemSchema = z.object({
    message_id: nullableStringSchema,
    from_agent: nullableStringSchema,
    to_agent: nullableStringSchema,
    message_type: nullableStringSchema,
    intent: nullableStringSchema,
    summary: nullableStringSchema,
    referenced_artifacts: z.array(z.string()),
    created_at: nullableStringSchema,
    file_path: taskRelativePathSchema,
});
export const messagesResponseSchema = z.object({
    items: z.array(messageItemSchema),
});
//# sourceMappingURL=messages.js.map