import { z } from 'zod';

export const contextAgentSchema = z.enum([
  'pm',
  'architect',
  'developer',
  'qa',
  'fix',
  'security',
]);

export const contextPackItemTypeSchema = z.enum([
  'requirement',
  'project_summary',
  'prd_summary',
  'file_change_plan',
  'file_change_plan_paths',
  'authorized_paths',
  'technical_constraints',
  'constraints',
  'diff',
  'fail_log',
  'acceptance_scope',
  'changed_paths',
  'fix_scope',
  'high_risk_paths',
  'forbidden_rules',
]);

export const contextPackItemSchema = z.object({
  type: contextPackItemTypeSchema,
  title: z.string(),
  content: z.string(),
  source_path: z.string().optional(),
  estimated_tokens: z.number().int().nonnegative(),
  truncated: z.boolean().default(false),
  inclusion_reason: z.string(),
});

export const contextPackSchema = z.object({
  pack_id: z.string(),
  task_id: z.string(),
  agent: contextAgentSchema,
  items: z.array(contextPackItemSchema),
  total_estimated_input_tokens: z.number().int().nonnegative(),
  full_context: z.boolean().default(false),
  created_at: z.string(),
});

export const contextBuildRequestSchema = z.object({
  task_id: z.string(),
  agent: contextAgentSchema,
  full_context: z.boolean().optional(),
  reason: z.string().optional(),
  extra_context: z.string().optional(),
}).strict();

export const contextPackListResponseSchema = z.array(contextPackSchema);

export type ContextAgent = z.infer<typeof contextAgentSchema>;
export type ContextPackItemType = z.infer<typeof contextPackItemTypeSchema>;
export type ContextPackItem = z.infer<typeof contextPackItemSchema>;
export type ContextPack = z.infer<typeof contextPackSchema>;
export type ContextBuildRequest = z.infer<typeof contextBuildRequestSchema>;
