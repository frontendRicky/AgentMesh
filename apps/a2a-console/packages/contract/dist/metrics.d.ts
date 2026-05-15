import { z } from 'zod';
export declare const largestArtifactSchema: z.ZodObject<{
    path: z.ZodEffects<z.ZodString, string, string>;
    size_bytes: z.ZodNumber;
    tokens_estimate: z.ZodNumber;
}, "strip", z.ZodTypeAny, {
    path: string;
    size_bytes: number;
    tokens_estimate: number;
}, {
    path: string;
    size_bytes: number;
    tokens_estimate: number;
}>;
export declare const metricsResponseSchema: z.ZodObject<{
    tokens: z.ZodObject<{
        total_estimate: z.ZodNumber;
        by_agent: z.ZodObject<{
            pm: z.ZodNumber;
            architect: z.ZodNumber;
            developer: z.ZodNumber;
            qa: z.ZodNumber;
            controller: z.ZodNumber;
            human: z.ZodNumber;
        }, "strip", z.ZodTypeAny, {
            pm: number;
            architect: number;
            developer: number;
            qa: number;
            controller: number;
            human: number;
        }, {
            pm: number;
            architect: number;
            developer: number;
            qa: number;
            controller: number;
            human: number;
        }>;
        by_stage: z.ZodRecord<z.ZodString, z.ZodNumber>;
    }, "strip", z.ZodTypeAny, {
        total_estimate: number;
        by_agent: {
            pm: number;
            architect: number;
            developer: number;
            qa: number;
            controller: number;
            human: number;
        };
        by_stage: Record<string, number>;
    }, {
        total_estimate: number;
        by_agent: {
            pm: number;
            architect: number;
            developer: number;
            qa: number;
            controller: number;
            human: number;
        };
        by_stage: Record<string, number>;
    }>;
    context: z.ZodObject<{
        active_chars: z.ZodNumber;
        active_tokens_estimate: z.ZodNumber;
        model: z.ZodNullable<z.ZodString>;
        model_max_context: z.ZodNumber;
        usage_pct: z.ZodNumber;
        level: z.ZodEnum<["safe", "warning", "high", "danger"]>;
    }, "strip", z.ZodTypeAny, {
        active_chars: number;
        active_tokens_estimate: number;
        model: string | null;
        model_max_context: number;
        usage_pct: number;
        level: "safe" | "warning" | "high" | "danger";
    }, {
        active_chars: number;
        active_tokens_estimate: number;
        model: string | null;
        model_max_context: number;
        usage_pct: number;
        level: "safe" | "warning" | "high" | "danger";
    }>;
    largest_artifacts: z.ZodArray<z.ZodObject<{
        path: z.ZodEffects<z.ZodString, string, string>;
        size_bytes: z.ZodNumber;
        tokens_estimate: z.ZodNumber;
    }, "strip", z.ZodTypeAny, {
        path: string;
        size_bytes: number;
        tokens_estimate: number;
    }, {
        path: string;
        size_bytes: number;
        tokens_estimate: number;
    }>, "many">;
}, "strip", z.ZodTypeAny, {
    tokens: {
        total_estimate: number;
        by_agent: {
            pm: number;
            architect: number;
            developer: number;
            qa: number;
            controller: number;
            human: number;
        };
        by_stage: Record<string, number>;
    };
    context: {
        active_chars: number;
        active_tokens_estimate: number;
        model: string | null;
        model_max_context: number;
        usage_pct: number;
        level: "safe" | "warning" | "high" | "danger";
    };
    largest_artifacts: {
        path: string;
        size_bytes: number;
        tokens_estimate: number;
    }[];
}, {
    tokens: {
        total_estimate: number;
        by_agent: {
            pm: number;
            architect: number;
            developer: number;
            qa: number;
            controller: number;
            human: number;
        };
        by_stage: Record<string, number>;
    };
    context: {
        active_chars: number;
        active_tokens_estimate: number;
        model: string | null;
        model_max_context: number;
        usage_pct: number;
        level: "safe" | "warning" | "high" | "danger";
    };
    largest_artifacts: {
        path: string;
        size_bytes: number;
        tokens_estimate: number;
    }[];
}>;
export type LargestArtifact = z.infer<typeof largestArtifactSchema>;
export type MetricsResponse = z.infer<typeof metricsResponseSchema>;
