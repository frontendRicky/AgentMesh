import { z } from 'zod';
export declare const modelPresetsResponseSchema: z.ZodObject<{
    overrides: z.ZodObject<{
        pm: z.ZodNullable<z.ZodString>;
        architect: z.ZodNullable<z.ZodString>;
        developer: z.ZodNullable<z.ZodString>;
        qa: z.ZodNullable<z.ZodString>;
        controller: z.ZodNullable<z.ZodString>;
        risk: z.ZodNullable<z.ZodString>;
    }, "strip", z.ZodTypeAny, {
        pm: string | null;
        architect: string | null;
        developer: string | null;
        qa: string | null;
        controller: string | null;
        risk: string | null;
    }, {
        pm: string | null;
        architect: string | null;
        developer: string | null;
        qa: string | null;
        controller: string | null;
        risk: string | null;
    }>;
    defaults: z.ZodObject<{
        pm: z.ZodString;
        architect: z.ZodString;
        developer: z.ZodString;
        qa: z.ZodString;
        controller: z.ZodString;
        risk: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        pm: string;
        architect: string;
        developer: string;
        qa: string;
        controller: string;
        risk: string;
    }, {
        pm: string;
        architect: string;
        developer: string;
        qa: string;
        controller: string;
        risk: string;
    }>;
}, "strip", z.ZodTypeAny, {
    overrides: {
        pm: string | null;
        architect: string | null;
        developer: string | null;
        qa: string | null;
        controller: string | null;
        risk: string | null;
    };
    defaults: {
        pm: string;
        architect: string;
        developer: string;
        qa: string;
        controller: string;
        risk: string;
    };
}, {
    overrides: {
        pm: string | null;
        architect: string | null;
        developer: string | null;
        qa: string | null;
        controller: string | null;
        risk: string | null;
    };
    defaults: {
        pm: string;
        architect: string;
        developer: string;
        qa: string;
        controller: string;
        risk: string;
    };
}>;
export type ModelPresetsResponse = z.infer<typeof modelPresetsResponseSchema>;
