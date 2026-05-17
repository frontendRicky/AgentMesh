import { z } from 'zod';

export const ProjectTypeSchema = z.enum([
  'self_upgrade',
  'client_project',
  'generated_project',
  'maintenance',
]);

export const ProjectAutomationModeSchema = z.enum([
  'manual',
  'assisted',
  'selective_auto',
  'full_auto',
]);

export const ProjectSchema = z.object({
  project_id: z.string(),
  project_name: z.string(),
  project_root: z.string(),
  project_type: ProjectTypeSchema,
  automation_mode: ProjectAutomationModeSchema.default('assisted'),
  max_parallel_runs: z.number().default(2),
  allowed_paths: z.array(z.string()).default([]),
  blocked_paths: z.array(z.string()).default(['.env', '*.env', '.github/**', 'secrets/**']),
  created_at: z.string(),
  updated_at: z.string(),
});

export type ProjectType = z.infer<typeof ProjectTypeSchema>;
export type ProjectAutomationMode = z.infer<typeof ProjectAutomationModeSchema>;
export type Project = z.infer<typeof ProjectSchema>;
