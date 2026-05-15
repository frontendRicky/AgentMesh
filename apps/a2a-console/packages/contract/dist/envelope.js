import { z } from 'zod';
export const nullableStringSchema = z.string().nullable();
export const unknownDataSchema = z.unknown();
export const taskRelativePathSchema = z.string().min(1).refine((value) => {
    if (value.includes('\0'))
        return false;
    if (value.startsWith('/') || /^[A-Za-z]:[\\/]/.test(value))
        return false;
    return !value.split(/[\\/]+/).includes('..');
}, { message: 'path must be relative to the task root' });
export const apiErrorSchema = z.object({
    code: z.string(),
    message: z.string(),
    details: z.unknown().optional(),
    field: z.string().optional(),
});
export const apiFailureEnvelopeSchema = z.object({
    ok: z.literal(false),
    error: apiErrorSchema,
});
export function apiSuccessEnvelopeSchema(dataSchema) {
    return z.object({
        ok: z.literal(true),
        data: dataSchema,
    });
}
export function apiEnvelopeSchema(dataSchema) {
    return z.discriminatedUnion('ok', [
        apiSuccessEnvelopeSchema(dataSchema),
        apiFailureEnvelopeSchema,
    ]);
}
//# sourceMappingURL=envelope.js.map