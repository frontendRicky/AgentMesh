import { z } from 'zod';

export const nullableStringSchema = z.string().nullable();
export const unknownDataSchema = z.unknown();

export const taskRelativePathSchema = z.string().min(1).refine(
  (value) => {
    if (value.includes('\0')) return false;
    if (value.startsWith('/') || /^[A-Za-z]:[\\/]/.test(value)) return false;
    return !value.split(/[\\/]+/).includes('..');
  },
  { message: 'path must be relative to the task root' },
);

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

export function apiSuccessEnvelopeSchema<T extends z.ZodTypeAny>(dataSchema: T) {
  return z.object({
    ok: z.literal(true),
    data: dataSchema,
  });
}

export function apiEnvelopeSchema<T extends z.ZodTypeAny>(dataSchema: T) {
  return z.discriminatedUnion('ok', [
    apiSuccessEnvelopeSchema(dataSchema),
    apiFailureEnvelopeSchema,
  ]);
}

export type ApiErrorPayload = z.infer<typeof apiErrorSchema>;
export type ApiFailureEnvelope = z.infer<typeof apiFailureEnvelopeSchema>;
export type ApiSuccessEnvelope<T> = { ok: true; data: T };
export type ApiEnvelope<T> = ApiSuccessEnvelope<T> | ApiFailureEnvelope;
