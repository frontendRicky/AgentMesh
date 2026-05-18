import { z } from 'zod';

export const sandboxErrorCodeSchema = z.enum([
  'PATH_NOT_ALLOWED',
  'SANDBOX_TOO_LARGE',
  'SANDBOX_NOT_FOUND',
  'SANDBOX_DIRTY',
  'LOCK_WAITING',
  'ROLLBACK_BACKUP_NOT_FOUND',
  'SANDBOX_APPLY_TOO_MANY_FILES',
]);

export const sandboxInitRequestSchema = z.object({
  run_id: z.string().min(1),
  project_id: z.string().min(1),
  source_files: z.array(z.string().min(1)),
}).strict();

export const sandboxInitResponseSchema = z.object({
  run_id: z.string(),
  project_id: z.string(),
  sandbox_path: z.string(),
  source_files: z.array(z.string()),
  total_size_bytes: z.number().int().nonnegative(),
  created_at: z.string(),
});

export const sandboxDiffResponseSchema = z.object({
  run_id: z.string(),
  changed_files: z.array(z.string()),
  patch: z.string(),
  patch_size_bytes: z.number().int().nonnegative(),
});

export const sandboxApplyResponseSchema = z.object({
  run_id: z.string(),
  applied_files: z.array(z.string()),
  backup_manifest_path: z.string(),
  applied_at: z.string(),
});

export const sandboxRollbackResponseSchema = z.object({
  run_id: z.string(),
  restored_files: z.array(z.string()),
  rolled_back_at: z.string(),
});

export type SandboxErrorCode = z.infer<typeof sandboxErrorCodeSchema>;
export type SandboxInitRequest = z.infer<typeof sandboxInitRequestSchema>;
export type SandboxInitResponse = z.infer<typeof sandboxInitResponseSchema>;
export type SandboxDiffResponse = z.infer<typeof sandboxDiffResponseSchema>;
export type SandboxApplyResponse = z.infer<typeof sandboxApplyResponseSchema>;
export type SandboxRollbackResponse = z.infer<typeof sandboxRollbackResponseSchema>;
