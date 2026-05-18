import { z } from 'zod';
export declare const sandboxErrorCodeSchema: z.ZodEnum<["PATH_NOT_ALLOWED", "SANDBOX_TOO_LARGE", "SANDBOX_NOT_FOUND", "SANDBOX_DIRTY", "LOCK_WAITING", "ROLLBACK_BACKUP_NOT_FOUND", "SANDBOX_APPLY_TOO_MANY_FILES"]>;
export declare const sandboxInitRequestSchema: z.ZodObject<{
    run_id: z.ZodString;
    project_id: z.ZodString;
    source_files: z.ZodArray<z.ZodString, "many">;
}, "strict", z.ZodTypeAny, {
    run_id: string;
    project_id: string;
    source_files: string[];
}, {
    run_id: string;
    project_id: string;
    source_files: string[];
}>;
export declare const sandboxInitResponseSchema: z.ZodObject<{
    run_id: z.ZodString;
    project_id: z.ZodString;
    sandbox_path: z.ZodString;
    source_files: z.ZodArray<z.ZodString, "many">;
    total_size_bytes: z.ZodNumber;
    created_at: z.ZodString;
}, "strip", z.ZodTypeAny, {
    created_at: string;
    run_id: string;
    sandbox_path: string;
    project_id: string;
    source_files: string[];
    total_size_bytes: number;
}, {
    created_at: string;
    run_id: string;
    sandbox_path: string;
    project_id: string;
    source_files: string[];
    total_size_bytes: number;
}>;
export declare const sandboxDiffResponseSchema: z.ZodObject<{
    run_id: z.ZodString;
    changed_files: z.ZodArray<z.ZodString, "many">;
    patch: z.ZodString;
    patch_size_bytes: z.ZodNumber;
}, "strip", z.ZodTypeAny, {
    run_id: string;
    changed_files: string[];
    patch: string;
    patch_size_bytes: number;
}, {
    run_id: string;
    changed_files: string[];
    patch: string;
    patch_size_bytes: number;
}>;
export declare const sandboxApplyResponseSchema: z.ZodObject<{
    run_id: z.ZodString;
    applied_files: z.ZodArray<z.ZodString, "many">;
    backup_manifest_path: z.ZodString;
    applied_at: z.ZodString;
}, "strip", z.ZodTypeAny, {
    run_id: string;
    applied_files: string[];
    backup_manifest_path: string;
    applied_at: string;
}, {
    run_id: string;
    applied_files: string[];
    backup_manifest_path: string;
    applied_at: string;
}>;
export declare const sandboxRollbackResponseSchema: z.ZodObject<{
    run_id: z.ZodString;
    restored_files: z.ZodArray<z.ZodString, "many">;
    rolled_back_at: z.ZodString;
}, "strip", z.ZodTypeAny, {
    run_id: string;
    restored_files: string[];
    rolled_back_at: string;
}, {
    run_id: string;
    restored_files: string[];
    rolled_back_at: string;
}>;
export type SandboxErrorCode = z.infer<typeof sandboxErrorCodeSchema>;
export type SandboxInitRequest = z.infer<typeof sandboxInitRequestSchema>;
export type SandboxInitResponse = z.infer<typeof sandboxInitResponseSchema>;
export type SandboxDiffResponse = z.infer<typeof sandboxDiffResponseSchema>;
export type SandboxApplyResponse = z.infer<typeof sandboxApplyResponseSchema>;
export type SandboxRollbackResponse = z.infer<typeof sandboxRollbackResponseSchema>;
