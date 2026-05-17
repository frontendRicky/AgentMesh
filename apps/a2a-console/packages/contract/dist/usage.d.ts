import { z } from 'zod';
export declare const UsageModelTierSchema: z.ZodEnum<["cheap", "balanced", "strong"]>;
export declare const UsageRecordSchema: z.ZodObject<{
    project_id: z.ZodString;
    task_id: z.ZodString;
    run_id: z.ZodString;
    agent: z.ZodString;
    model: z.ZodString;
    model_tier: z.ZodEnum<["cheap", "balanced", "strong"]>;
    input_tokens: z.ZodNumber;
    output_tokens: z.ZodNumber;
    cost_usd: z.ZodNumber;
    optimization_applied: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
    created_at: z.ZodString;
}, "strip", z.ZodTypeAny, {
    task_id: string;
    created_at: string;
    model: string;
    project_id: string;
    run_id: string;
    agent: string;
    model_tier: "cheap" | "balanced" | "strong";
    input_tokens: number;
    output_tokens: number;
    cost_usd: number;
    optimization_applied: string[];
}, {
    task_id: string;
    created_at: string;
    model: string;
    project_id: string;
    run_id: string;
    agent: string;
    model_tier: "cheap" | "balanced" | "strong";
    input_tokens: number;
    output_tokens: number;
    cost_usd: number;
    optimization_applied?: string[] | undefined;
}>;
export declare const BudgetModeSchema: z.ZodEnum<["conservative", "balanced", "aggressive"]>;
export declare const BudgetSchema: z.ZodObject<{
    max_cost_usd_per_run: z.ZodDefault<z.ZodNumber>;
    max_cost_usd_per_task: z.ZodDefault<z.ZodNumber>;
    max_cost_usd_per_project_per_day: z.ZodDefault<z.ZodNumber>;
    mode: z.ZodDefault<z.ZodEnum<["conservative", "balanced", "aggressive"]>>;
}, "strip", z.ZodTypeAny, {
    max_cost_usd_per_run: number;
    max_cost_usd_per_task: number;
    max_cost_usd_per_project_per_day: number;
    mode: "balanced" | "conservative" | "aggressive";
}, {
    max_cost_usd_per_run?: number | undefined;
    max_cost_usd_per_task?: number | undefined;
    max_cost_usd_per_project_per_day?: number | undefined;
    mode?: "balanced" | "conservative" | "aggressive" | undefined;
}>;
export type UsageModelTier = z.infer<typeof UsageModelTierSchema>;
export type UsageRecord = z.infer<typeof UsageRecordSchema>;
export type BudgetMode = z.infer<typeof BudgetModeSchema>;
export type Budget = z.infer<typeof BudgetSchema>;
