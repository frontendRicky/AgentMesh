import { z } from 'zod';
export * from './envelope.js';
export * from './tasks.js';
export * from './messages.js';
export * from './metrics.js';
export * from './reviews.js';
export * from './model-presets.js';
export declare const projectGeneratorTaskIdSchema: z.ZodString;
export declare const projectGeneratorDraftIdSchema: z.ZodString;
export declare const projectGeneratorSlugSchema: z.ZodString;
export declare const projectGeneratorProjectTypeSchema: z.ZodEnum<["business-dashboard", "admin-system", "marketing-site", "mobile-h5", "data-report", "custom"]>;
export declare const projectGeneratorStrategySchema: z.ZodEnum<["quick", "quality", "budget", "strict"]>;
export declare const projectGeneratorModelProfileSchema: z.ZodEnum<["recommended", "faster", "stronger", "cheaper", "custom"]>;
export declare const projectGeneratorApiModeSchema: z.ZodEnum<["mock", "real", "unknown"]>;
export declare const projectGeneratorTemplateSchema: z.ZodObject<{
    id: z.ZodEnum<["business-dashboard", "admin-system", "marketing-site", "mobile-h5", "data-report", "custom"]>;
    name: z.ZodString;
    description: z.ZodString;
    examples: z.ZodArray<z.ZodString, "many">;
    recommended_strategy: z.ZodEnum<["quick", "quality", "budget", "strict"]>;
}, "strip", z.ZodTypeAny, {
    id: "custom" | "business-dashboard" | "admin-system" | "marketing-site" | "mobile-h5" | "data-report";
    name: string;
    description: string;
    examples: string[];
    recommended_strategy: "strict" | "quick" | "quality" | "budget";
}, {
    id: "custom" | "business-dashboard" | "admin-system" | "marketing-site" | "mobile-h5" | "data-report";
    name: string;
    description: string;
    examples: string[];
    recommended_strategy: "strict" | "quick" | "quality" | "budget";
}>;
export declare const projectGeneratorTemplatesResponseSchema: z.ZodObject<{
    items: z.ZodArray<z.ZodObject<{
        id: z.ZodEnum<["business-dashboard", "admin-system", "marketing-site", "mobile-h5", "data-report", "custom"]>;
        name: z.ZodString;
        description: z.ZodString;
        examples: z.ZodArray<z.ZodString, "many">;
        recommended_strategy: z.ZodEnum<["quick", "quality", "budget", "strict"]>;
    }, "strip", z.ZodTypeAny, {
        id: "custom" | "business-dashboard" | "admin-system" | "marketing-site" | "mobile-h5" | "data-report";
        name: string;
        description: string;
        examples: string[];
        recommended_strategy: "strict" | "quick" | "quality" | "budget";
    }, {
        id: "custom" | "business-dashboard" | "admin-system" | "marketing-site" | "mobile-h5" | "data-report";
        name: string;
        description: string;
        examples: string[];
        recommended_strategy: "strict" | "quick" | "quality" | "budget";
    }>, "many">;
}, "strip", z.ZodTypeAny, {
    items: {
        id: "custom" | "business-dashboard" | "admin-system" | "marketing-site" | "mobile-h5" | "data-report";
        name: string;
        description: string;
        examples: string[];
        recommended_strategy: "strict" | "quick" | "quality" | "budget";
    }[];
}, {
    items: {
        id: "custom" | "business-dashboard" | "admin-system" | "marketing-site" | "mobile-h5" | "data-report";
        name: string;
        description: string;
        examples: string[];
        recommended_strategy: "strict" | "quick" | "quality" | "budget";
    }[];
}>;
export declare const projectGeneratorDraftRequestSchema: z.ZodObject<{
    project_name: z.ZodString;
    project_type: z.ZodEnum<["business-dashboard", "admin-system", "marketing-site", "mobile-h5", "data-report", "custom"]>;
    business_description: z.ZodString;
    target_users: z.ZodDefault<z.ZodString>;
    pages: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
    style_preference: z.ZodDefault<z.ZodString>;
    data_source: z.ZodDefault<z.ZodString>;
    generation_strategy: z.ZodEnum<["quick", "quality", "budget", "strict"]>;
    model_profile: z.ZodEnum<["recommended", "faster", "stronger", "cheaper", "custom"]>;
    api_mode: z.ZodDefault<z.ZodEnum<["mock", "real", "unknown"]>>;
    needs_auth: z.ZodDefault<z.ZodBoolean>;
    needs_charts: z.ZodDefault<z.ZodBoolean>;
}, "strict", z.ZodTypeAny, {
    project_name: string;
    project_type: "custom" | "business-dashboard" | "admin-system" | "marketing-site" | "mobile-h5" | "data-report";
    business_description: string;
    target_users: string;
    pages: string[];
    style_preference: string;
    data_source: string;
    generation_strategy: "strict" | "quick" | "quality" | "budget";
    model_profile: "custom" | "recommended" | "faster" | "stronger" | "cheaper";
    api_mode: "unknown" | "mock" | "real";
    needs_auth: boolean;
    needs_charts: boolean;
}, {
    project_name: string;
    project_type: "custom" | "business-dashboard" | "admin-system" | "marketing-site" | "mobile-h5" | "data-report";
    business_description: string;
    generation_strategy: "strict" | "quick" | "quality" | "budget";
    model_profile: "custom" | "recommended" | "faster" | "stronger" | "cheaper";
    target_users?: string | undefined;
    pages?: string[] | undefined;
    style_preference?: string | undefined;
    data_source?: string | undefined;
    api_mode?: "unknown" | "mock" | "real" | undefined;
    needs_auth?: boolean | undefined;
    needs_charts?: boolean | undefined;
}>;
export declare const projectGeneratorDraftResponseSchema: z.ZodObject<{
    draft_id: z.ZodString;
    summary: z.ZodString;
    prd_preview: z.ZodString;
    openspec_preview: z.ZodString;
    model_snapshot_preview: z.ZodString;
}, "strip", z.ZodTypeAny, {
    summary: string;
    draft_id: string;
    prd_preview: string;
    openspec_preview: string;
    model_snapshot_preview: string;
}, {
    summary: string;
    draft_id: string;
    prd_preview: string;
    openspec_preview: string;
    model_snapshot_preview: string;
}>;
export declare const projectGeneratorTaskCreateRequestSchema: z.ZodObject<{
    slug: z.ZodString;
}, "strict", z.ZodTypeAny, {
    slug: string;
}, {
    slug: string;
}>;
export declare const projectGeneratorTaskCreateResponseSchema: z.ZodObject<{
    task_id: z.ZodString;
    task_path: z.ZodString;
    created_files: z.ZodArray<z.ZodEffects<z.ZodString, string, string>, "many">;
    model_snapshot_path: z.ZodEffects<z.ZodString, string, string>;
    next_step: z.ZodLiteral<"handoff_to_technical_owner">;
}, "strip", z.ZodTypeAny, {
    task_id: string;
    task_path: string;
    created_files: string[];
    model_snapshot_path: string;
    next_step: "handoff_to_technical_owner";
}, {
    task_id: string;
    task_path: string;
    created_files: string[];
    model_snapshot_path: string;
    next_step: "handoff_to_technical_owner";
}>;
export declare const projectGeneratorJobStatusSchema: z.ZodObject<{
    task_id: z.ZodString;
    status: z.ZodEnum<["not_started", "queued", "running", "succeeded", "failed"]>;
    message: z.ZodNullable<z.ZodString>;
    updated_at: z.ZodNullable<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    message: string | null;
    status: "not_started" | "queued" | "running" | "succeeded" | "failed";
    task_id: string;
    updated_at: string | null;
}, {
    message: string | null;
    status: "not_started" | "queued" | "running" | "succeeded" | "failed";
    task_id: string;
    updated_at: string | null;
}>;
export type ProjectGeneratorTaskId = z.infer<typeof projectGeneratorTaskIdSchema>;
export type ProjectGeneratorDraftId = z.infer<typeof projectGeneratorDraftIdSchema>;
export type ProjectGeneratorProjectType = z.infer<typeof projectGeneratorProjectTypeSchema>;
export type ProjectGeneratorStrategy = z.infer<typeof projectGeneratorStrategySchema>;
export type ProjectGeneratorModelProfile = z.infer<typeof projectGeneratorModelProfileSchema>;
export type ProjectGeneratorApiMode = z.infer<typeof projectGeneratorApiModeSchema>;
export type ProjectGeneratorTemplate = z.infer<typeof projectGeneratorTemplateSchema>;
export type ProjectGeneratorTemplatesResponse = z.infer<typeof projectGeneratorTemplatesResponseSchema>;
export type ProjectGeneratorDraftRequest = z.infer<typeof projectGeneratorDraftRequestSchema>;
export type ProjectGeneratorDraftResponse = z.infer<typeof projectGeneratorDraftResponseSchema>;
export type ProjectGeneratorTaskCreateRequest = z.infer<typeof projectGeneratorTaskCreateRequestSchema>;
export type ProjectGeneratorTaskCreateResponse = z.infer<typeof projectGeneratorTaskCreateResponseSchema>;
export type ProjectGeneratorJobStatus = z.infer<typeof projectGeneratorJobStatusSchema>;
