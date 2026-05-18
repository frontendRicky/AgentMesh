import { z } from 'zod';
export declare const contextAgentSchema: z.ZodEnum<["pm", "architect", "developer", "qa", "fix", "security"]>;
export declare const contextPackItemTypeSchema: z.ZodEnum<["requirement", "project_summary", "prd_summary", "file_change_plan", "file_change_plan_paths", "authorized_paths", "technical_constraints", "constraints", "diff", "fail_log", "acceptance_scope", "changed_paths", "fix_scope", "high_risk_paths", "forbidden_rules"]>;
export declare const contextPackItemSchema: z.ZodObject<{
    type: z.ZodEnum<["requirement", "project_summary", "prd_summary", "file_change_plan", "file_change_plan_paths", "authorized_paths", "technical_constraints", "constraints", "diff", "fail_log", "acceptance_scope", "changed_paths", "fix_scope", "high_risk_paths", "forbidden_rules"]>;
    title: z.ZodString;
    content: z.ZodString;
    source_path: z.ZodOptional<z.ZodString>;
    estimated_tokens: z.ZodNumber;
    truncated: z.ZodDefault<z.ZodBoolean>;
    inclusion_reason: z.ZodString;
}, "strip", z.ZodTypeAny, {
    type: "requirement" | "project_summary" | "prd_summary" | "file_change_plan" | "file_change_plan_paths" | "authorized_paths" | "technical_constraints" | "constraints" | "diff" | "fail_log" | "acceptance_scope" | "changed_paths" | "fix_scope" | "high_risk_paths" | "forbidden_rules";
    title: string;
    content: string;
    estimated_tokens: number;
    truncated: boolean;
    inclusion_reason: string;
    source_path?: string | undefined;
}, {
    type: "requirement" | "project_summary" | "prd_summary" | "file_change_plan" | "file_change_plan_paths" | "authorized_paths" | "technical_constraints" | "constraints" | "diff" | "fail_log" | "acceptance_scope" | "changed_paths" | "fix_scope" | "high_risk_paths" | "forbidden_rules";
    title: string;
    content: string;
    estimated_tokens: number;
    inclusion_reason: string;
    source_path?: string | undefined;
    truncated?: boolean | undefined;
}>;
export declare const contextPackSchema: z.ZodObject<{
    pack_id: z.ZodString;
    task_id: z.ZodString;
    agent: z.ZodEnum<["pm", "architect", "developer", "qa", "fix", "security"]>;
    items: z.ZodArray<z.ZodObject<{
        type: z.ZodEnum<["requirement", "project_summary", "prd_summary", "file_change_plan", "file_change_plan_paths", "authorized_paths", "technical_constraints", "constraints", "diff", "fail_log", "acceptance_scope", "changed_paths", "fix_scope", "high_risk_paths", "forbidden_rules"]>;
        title: z.ZodString;
        content: z.ZodString;
        source_path: z.ZodOptional<z.ZodString>;
        estimated_tokens: z.ZodNumber;
        truncated: z.ZodDefault<z.ZodBoolean>;
        inclusion_reason: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "requirement" | "project_summary" | "prd_summary" | "file_change_plan" | "file_change_plan_paths" | "authorized_paths" | "technical_constraints" | "constraints" | "diff" | "fail_log" | "acceptance_scope" | "changed_paths" | "fix_scope" | "high_risk_paths" | "forbidden_rules";
        title: string;
        content: string;
        estimated_tokens: number;
        truncated: boolean;
        inclusion_reason: string;
        source_path?: string | undefined;
    }, {
        type: "requirement" | "project_summary" | "prd_summary" | "file_change_plan" | "file_change_plan_paths" | "authorized_paths" | "technical_constraints" | "constraints" | "diff" | "fail_log" | "acceptance_scope" | "changed_paths" | "fix_scope" | "high_risk_paths" | "forbidden_rules";
        title: string;
        content: string;
        estimated_tokens: number;
        inclusion_reason: string;
        source_path?: string | undefined;
        truncated?: boolean | undefined;
    }>, "many">;
    total_estimated_input_tokens: z.ZodNumber;
    full_context: z.ZodDefault<z.ZodBoolean>;
    created_at: z.ZodString;
}, "strip", z.ZodTypeAny, {
    pack_id: string;
    task_id: string;
    agent: "pm" | "architect" | "developer" | "qa" | "fix" | "security";
    items: {
        type: "requirement" | "project_summary" | "prd_summary" | "file_change_plan" | "file_change_plan_paths" | "authorized_paths" | "technical_constraints" | "constraints" | "diff" | "fail_log" | "acceptance_scope" | "changed_paths" | "fix_scope" | "high_risk_paths" | "forbidden_rules";
        title: string;
        content: string;
        estimated_tokens: number;
        truncated: boolean;
        inclusion_reason: string;
        source_path?: string | undefined;
    }[];
    total_estimated_input_tokens: number;
    full_context: boolean;
    created_at: string;
}, {
    pack_id: string;
    task_id: string;
    agent: "pm" | "architect" | "developer" | "qa" | "fix" | "security";
    items: {
        type: "requirement" | "project_summary" | "prd_summary" | "file_change_plan" | "file_change_plan_paths" | "authorized_paths" | "technical_constraints" | "constraints" | "diff" | "fail_log" | "acceptance_scope" | "changed_paths" | "fix_scope" | "high_risk_paths" | "forbidden_rules";
        title: string;
        content: string;
        estimated_tokens: number;
        inclusion_reason: string;
        source_path?: string | undefined;
        truncated?: boolean | undefined;
    }[];
    total_estimated_input_tokens: number;
    created_at: string;
    full_context?: boolean | undefined;
}>;
export declare const contextBuildRequestSchema: z.ZodObject<{
    task_id: z.ZodString;
    agent: z.ZodEnum<["pm", "architect", "developer", "qa", "fix", "security"]>;
    full_context: z.ZodOptional<z.ZodBoolean>;
    reason: z.ZodOptional<z.ZodString>;
    extra_context: z.ZodOptional<z.ZodString>;
}, "strict", z.ZodTypeAny, {
    task_id: string;
    agent: "pm" | "architect" | "developer" | "qa" | "fix" | "security";
    full_context?: boolean | undefined;
    reason?: string | undefined;
    extra_context?: string | undefined;
}, {
    task_id: string;
    agent: "pm" | "architect" | "developer" | "qa" | "fix" | "security";
    full_context?: boolean | undefined;
    reason?: string | undefined;
    extra_context?: string | undefined;
}>;
export declare const contextPackListResponseSchema: z.ZodArray<z.ZodObject<{
    pack_id: z.ZodString;
    task_id: z.ZodString;
    agent: z.ZodEnum<["pm", "architect", "developer", "qa", "fix", "security"]>;
    items: z.ZodArray<z.ZodObject<{
        type: z.ZodEnum<["requirement", "project_summary", "prd_summary", "file_change_plan", "file_change_plan_paths", "authorized_paths", "technical_constraints", "constraints", "diff", "fail_log", "acceptance_scope", "changed_paths", "fix_scope", "high_risk_paths", "forbidden_rules"]>;
        title: z.ZodString;
        content: z.ZodString;
        source_path: z.ZodOptional<z.ZodString>;
        estimated_tokens: z.ZodNumber;
        truncated: z.ZodDefault<z.ZodBoolean>;
        inclusion_reason: z.ZodString;
    }, "strip", z.ZodTypeAny, {
        type: "requirement" | "project_summary" | "prd_summary" | "file_change_plan" | "file_change_plan_paths" | "authorized_paths" | "technical_constraints" | "constraints" | "diff" | "fail_log" | "acceptance_scope" | "changed_paths" | "fix_scope" | "high_risk_paths" | "forbidden_rules";
        title: string;
        content: string;
        estimated_tokens: number;
        truncated: boolean;
        inclusion_reason: string;
        source_path?: string | undefined;
    }, {
        type: "requirement" | "project_summary" | "prd_summary" | "file_change_plan" | "file_change_plan_paths" | "authorized_paths" | "technical_constraints" | "constraints" | "diff" | "fail_log" | "acceptance_scope" | "changed_paths" | "fix_scope" | "high_risk_paths" | "forbidden_rules";
        title: string;
        content: string;
        estimated_tokens: number;
        inclusion_reason: string;
        source_path?: string | undefined;
        truncated?: boolean | undefined;
    }>, "many">;
    total_estimated_input_tokens: z.ZodNumber;
    full_context: z.ZodDefault<z.ZodBoolean>;
    created_at: z.ZodString;
}, "strip", z.ZodTypeAny, {
    pack_id: string;
    task_id: string;
    agent: "pm" | "architect" | "developer" | "qa" | "fix" | "security";
    items: {
        type: "requirement" | "project_summary" | "prd_summary" | "file_change_plan" | "file_change_plan_paths" | "authorized_paths" | "technical_constraints" | "constraints" | "diff" | "fail_log" | "acceptance_scope" | "changed_paths" | "fix_scope" | "high_risk_paths" | "forbidden_rules";
        title: string;
        content: string;
        estimated_tokens: number;
        truncated: boolean;
        inclusion_reason: string;
        source_path?: string | undefined;
    }[];
    total_estimated_input_tokens: number;
    full_context: boolean;
    created_at: string;
}, {
    pack_id: string;
    task_id: string;
    agent: "pm" | "architect" | "developer" | "qa" | "fix" | "security";
    items: {
        type: "requirement" | "project_summary" | "prd_summary" | "file_change_plan" | "file_change_plan_paths" | "authorized_paths" | "technical_constraints" | "constraints" | "diff" | "fail_log" | "acceptance_scope" | "changed_paths" | "fix_scope" | "high_risk_paths" | "forbidden_rules";
        title: string;
        content: string;
        estimated_tokens: number;
        inclusion_reason: string;
        source_path?: string | undefined;
        truncated?: boolean | undefined;
    }[];
    total_estimated_input_tokens: number;
    created_at: string;
    full_context?: boolean | undefined;
}>, "many">;
export type ContextAgent = z.infer<typeof contextAgentSchema>;
export type ContextPackItemType = z.infer<typeof contextPackItemTypeSchema>;
export type ContextPackItem = z.infer<typeof contextPackItemSchema>;
export type ContextPack = z.infer<typeof contextPackSchema>;
export type ContextBuildRequest = z.infer<typeof contextBuildRequestSchema>;
