import { z } from 'zod';

export const RunSessionStatusSchema = z.enum([
  'queued',
  'running',
  'paused',
  'cancelled',
  'completed',
  'failed',
]);

export const RunPrioritySchema = z.enum([
  'urgent',
  'high',
  'normal',
  'background',
]);

export const RunLockStatusSchema = z.enum([
  'unlocked',
  'acquiring',
  'locked',
  'waiting_for_lock',
]);

export const RunSessionSchema = z.object({
  run_id: z.string(),
  task_id: z.string(),
  status: RunSessionStatusSchema,
  priority: RunPrioritySchema.default('normal'),
  lock_status: RunLockStatusSchema.default('unlocked'),
  locked_files: z.array(z.string()).default([]),
  agent: z.string(),
  model: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  error_message: z.string().optional(),
});

export const RunSessionCreateRequestSchema = z.object({
  task_id: z.string(),
  agent: z.string(),
  model: z.string().optional(),
  priority: RunPrioritySchema.optional(),
}).strict();

export const RunSessionActionSchema = z.enum(['pause', 'resume', 'cancel']);

export const RunSessionPatchRequestSchema = z.object({
  action: RunSessionActionSchema,
}).strict();

export type RunSessionStatus = z.infer<typeof RunSessionStatusSchema>;
export type RunPriority = z.infer<typeof RunPrioritySchema>;
export type RunLockStatus = z.infer<typeof RunLockStatusSchema>;
export type RunSession = z.infer<typeof RunSessionSchema>;
export type RunSessionCreateRequest = z.infer<typeof RunSessionCreateRequestSchema>;
export type RunSessionAction = z.infer<typeof RunSessionActionSchema>;
export type RunSessionPatchRequest = z.infer<typeof RunSessionPatchRequestSchema>;
