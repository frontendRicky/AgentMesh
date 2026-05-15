import { z } from 'zod';
export declare const messageItemSchema: z.ZodObject<{
    message_id: z.ZodNullable<z.ZodString>;
    from_agent: z.ZodNullable<z.ZodString>;
    to_agent: z.ZodNullable<z.ZodString>;
    message_type: z.ZodNullable<z.ZodString>;
    intent: z.ZodNullable<z.ZodString>;
    summary: z.ZodNullable<z.ZodString>;
    referenced_artifacts: z.ZodArray<z.ZodString, "many">;
    created_at: z.ZodNullable<z.ZodString>;
    file_path: z.ZodEffects<z.ZodString, string, string>;
}, "strip", z.ZodTypeAny, {
    created_at: string | null;
    summary: string | null;
    message_id: string | null;
    from_agent: string | null;
    to_agent: string | null;
    message_type: string | null;
    intent: string | null;
    referenced_artifacts: string[];
    file_path: string;
}, {
    created_at: string | null;
    summary: string | null;
    message_id: string | null;
    from_agent: string | null;
    to_agent: string | null;
    message_type: string | null;
    intent: string | null;
    referenced_artifacts: string[];
    file_path: string;
}>;
export declare const messagesResponseSchema: z.ZodObject<{
    items: z.ZodArray<z.ZodObject<{
        message_id: z.ZodNullable<z.ZodString>;
        from_agent: z.ZodNullable<z.ZodString>;
        to_agent: z.ZodNullable<z.ZodString>;
        message_type: z.ZodNullable<z.ZodString>;
        intent: z.ZodNullable<z.ZodString>;
        summary: z.ZodNullable<z.ZodString>;
        referenced_artifacts: z.ZodArray<z.ZodString, "many">;
        created_at: z.ZodNullable<z.ZodString>;
        file_path: z.ZodEffects<z.ZodString, string, string>;
    }, "strip", z.ZodTypeAny, {
        created_at: string | null;
        summary: string | null;
        message_id: string | null;
        from_agent: string | null;
        to_agent: string | null;
        message_type: string | null;
        intent: string | null;
        referenced_artifacts: string[];
        file_path: string;
    }, {
        created_at: string | null;
        summary: string | null;
        message_id: string | null;
        from_agent: string | null;
        to_agent: string | null;
        message_type: string | null;
        intent: string | null;
        referenced_artifacts: string[];
        file_path: string;
    }>, "many">;
}, "strip", z.ZodTypeAny, {
    items: {
        created_at: string | null;
        summary: string | null;
        message_id: string | null;
        from_agent: string | null;
        to_agent: string | null;
        message_type: string | null;
        intent: string | null;
        referenced_artifacts: string[];
        file_path: string;
    }[];
}, {
    items: {
        created_at: string | null;
        summary: string | null;
        message_id: string | null;
        from_agent: string | null;
        to_agent: string | null;
        message_type: string | null;
        intent: string | null;
        referenced_artifacts: string[];
        file_path: string;
    }[];
}>;
export type MessageItem = z.infer<typeof messageItemSchema>;
export type MessagesResponse = z.infer<typeof messagesResponseSchema>;
