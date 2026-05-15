import { z } from 'zod';
export declare const nullableStringSchema: z.ZodNullable<z.ZodString>;
export declare const unknownDataSchema: z.ZodUnknown;
export declare const taskRelativePathSchema: z.ZodEffects<z.ZodString, string, string>;
export declare const apiErrorSchema: z.ZodObject<{
    code: z.ZodString;
    message: z.ZodString;
    details: z.ZodOptional<z.ZodUnknown>;
    field: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    code: string;
    message: string;
    details?: unknown;
    field?: string | undefined;
}, {
    code: string;
    message: string;
    details?: unknown;
    field?: string | undefined;
}>;
export declare const apiFailureEnvelopeSchema: z.ZodObject<{
    ok: z.ZodLiteral<false>;
    error: z.ZodObject<{
        code: z.ZodString;
        message: z.ZodString;
        details: z.ZodOptional<z.ZodUnknown>;
        field: z.ZodOptional<z.ZodString>;
    }, "strip", z.ZodTypeAny, {
        code: string;
        message: string;
        details?: unknown;
        field?: string | undefined;
    }, {
        code: string;
        message: string;
        details?: unknown;
        field?: string | undefined;
    }>;
}, "strip", z.ZodTypeAny, {
    ok: false;
    error: {
        code: string;
        message: string;
        details?: unknown;
        field?: string | undefined;
    };
}, {
    ok: false;
    error: {
        code: string;
        message: string;
        details?: unknown;
        field?: string | undefined;
    };
}>;
export declare function apiSuccessEnvelopeSchema<T extends z.ZodTypeAny>(dataSchema: T): z.ZodObject<{
    ok: z.ZodLiteral<true>;
    data: T;
}, "strip", z.ZodTypeAny, { [k in keyof z.objectUtil.addQuestionMarks<z.baseObjectOutputType<{
    ok: z.ZodLiteral<true>;
    data: T;
}>, any>]: z.objectUtil.addQuestionMarks<z.baseObjectOutputType<{
    ok: z.ZodLiteral<true>;
    data: T;
}>, any>[k]; }, { [k_1 in keyof z.baseObjectInputType<{
    ok: z.ZodLiteral<true>;
    data: T;
}>]: z.baseObjectInputType<{
    ok: z.ZodLiteral<true>;
    data: T;
}>[k_1]; }>;
export declare function apiEnvelopeSchema<T extends z.ZodTypeAny>(dataSchema: T): z.ZodDiscriminatedUnion<"ok", [z.ZodObject<{
    ok: z.ZodLiteral<true>;
    data: T;
}, "strip", z.ZodTypeAny, { [k in keyof z.objectUtil.addQuestionMarks<z.baseObjectOutputType<{
    ok: z.ZodLiteral<true>;
    data: T;
}>, any>]: z.objectUtil.addQuestionMarks<z.baseObjectOutputType<{
    ok: z.ZodLiteral<true>;
    data: T;
}>, any>[k]; }, { [k_1 in keyof z.baseObjectInputType<{
    ok: z.ZodLiteral<true>;
    data: T;
}>]: z.baseObjectInputType<{
    ok: z.ZodLiteral<true>;
    data: T;
}>[k_1]; }>, z.ZodObject<{
    ok: z.ZodLiteral<false>;
    error: z.ZodObject<{
        code: z.ZodString;
        message: z.ZodString;
        details: z.ZodOptional<z.ZodUnknown>;
        field: z.ZodOptional<z.ZodString>;
    }, "strip", z.ZodTypeAny, {
        code: string;
        message: string;
        details?: unknown;
        field?: string | undefined;
    }, {
        code: string;
        message: string;
        details?: unknown;
        field?: string | undefined;
    }>;
}, "strip", z.ZodTypeAny, {
    ok: false;
    error: {
        code: string;
        message: string;
        details?: unknown;
        field?: string | undefined;
    };
}, {
    ok: false;
    error: {
        code: string;
        message: string;
        details?: unknown;
        field?: string | undefined;
    };
}>]>;
export type ApiErrorPayload = z.infer<typeof apiErrorSchema>;
export type ApiFailureEnvelope = z.infer<typeof apiFailureEnvelopeSchema>;
export type ApiSuccessEnvelope<T> = {
    ok: true;
    data: T;
};
export type ApiEnvelope<T> = ApiSuccessEnvelope<T> | ApiFailureEnvelope;
