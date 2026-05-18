import { z } from 'zod';
export declare const RunSessionStatusSchema: z.ZodEnum<["queued", "running", "paused", "cancelled", "completed", "failed"]>;
export declare const RunPrioritySchema: z.ZodEnum<["urgent", "high", "normal", "background"]>;
export declare const RunLockStatusSchema: z.ZodEnum<["unlocked", "acquiring", "locked", "waiting_for_lock"]>;
export declare const RunSessionSchema: z.ZodObject<{
    run_id: z.ZodString;
    task_id: z.ZodString;
    status: z.ZodEnum<["queued", "running", "paused", "cancelled", "completed", "failed"]>;
    priority: z.ZodDefault<z.ZodEnum<["urgent", "high", "normal", "background"]>>;
    lock_status: z.ZodDefault<z.ZodEnum<["unlocked", "acquiring", "locked", "waiting_for_lock"]>>;
    locked_files: z.ZodDefault<z.ZodArray<z.ZodString, "many">>;
    context_pack_id: z.ZodOptional<z.ZodString>;
    sandbox_path: z.ZodOptional<z.ZodString>;
    last_test_run_at: z.ZodOptional<z.ZodString>;
    last_test_result: z.ZodOptional<z.ZodNullable<z.ZodEnum<["pass", "fail", "timeout"]>>>;
    agent: z.ZodString;
    model: z.ZodString;
    created_at: z.ZodString;
    updated_at: z.ZodString;
    error_message: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    status: "queued" | "running" | "paused" | "cancelled" | "completed" | "failed";
    task_id: string;
    agent: string;
    created_at: string;
    priority: "high" | "urgent" | "normal" | "background";
    updated_at: string;
    model: string;
    run_id: string;
    lock_status: "unlocked" | "acquiring" | "locked" | "waiting_for_lock";
    locked_files: string[];
    context_pack_id?: string | undefined;
    sandbox_path?: string | undefined;
    last_test_run_at?: string | undefined;
    last_test_result?: "pass" | "fail" | "timeout" | null | undefined;
    error_message?: string | undefined;
}, {
    status: "queued" | "running" | "paused" | "cancelled" | "completed" | "failed";
    task_id: string;
    agent: string;
    created_at: string;
    updated_at: string;
    model: string;
    run_id: string;
    priority?: "high" | "urgent" | "normal" | "background" | undefined;
    lock_status?: "unlocked" | "acquiring" | "locked" | "waiting_for_lock" | undefined;
    locked_files?: string[] | undefined;
    context_pack_id?: string | undefined;
    sandbox_path?: string | undefined;
    last_test_run_at?: string | undefined;
    last_test_result?: "pass" | "fail" | "timeout" | null | undefined;
    error_message?: string | undefined;
}>;
export declare const RunSessionCreateRequestSchema: z.ZodObject<{
    task_id: z.ZodString;
    agent: z.ZodString;
    model: z.ZodOptional<z.ZodString>;
    priority: z.ZodOptional<z.ZodEnum<["urgent", "high", "normal", "background"]>>;
}, "strict", z.ZodTypeAny, {
    task_id: string;
    agent: string;
    priority?: "high" | "urgent" | "normal" | "background" | undefined;
    model?: string | undefined;
}, {
    task_id: string;
    agent: string;
    priority?: "high" | "urgent" | "normal" | "background" | undefined;
    model?: string | undefined;
}>;
export declare const RunSessionActionSchema: z.ZodEnum<["pause", "resume", "cancel"]>;
export declare const RunSessionPatchRequestSchema: z.ZodObject<{
    action: z.ZodEnum<["pause", "resume", "cancel"]>;
}, "strict", z.ZodTypeAny, {
    action: "pause" | "resume" | "cancel";
}, {
    action: "pause" | "resume" | "cancel";
}>;
export type RunSessionStatus = z.infer<typeof RunSessionStatusSchema>;
export type RunPriority = z.infer<typeof RunPrioritySchema>;
export type RunLockStatus = z.infer<typeof RunLockStatusSchema>;
export type RunSession = z.infer<typeof RunSessionSchema>;
export type RunSessionCreateRequest = z.infer<typeof RunSessionCreateRequestSchema>;
export type RunSessionAction = z.infer<typeof RunSessionActionSchema>;
export type RunSessionPatchRequest = z.infer<typeof RunSessionPatchRequestSchema>;
