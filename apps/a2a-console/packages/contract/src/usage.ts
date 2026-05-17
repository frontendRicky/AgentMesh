import { z } from 'zod';

export const UsageModelTierSchema = z.enum(['cheap', 'balanced', 'strong']);

export const UsageRecordSchema = z.object({
  project_id: z.string(),
  task_id: z.string(),
  run_id: z.string(),
  agent: z.string(),
  model: z.string(),
  model_tier: UsageModelTierSchema,
  input_tokens: z.number().int().min(0),
  output_tokens: z.number().int().min(0),
  cost_usd: z.number().min(0),
  optimization_applied: z.array(z.string()).default([]),
  created_at: z.string().datetime(),
});

export const BudgetModeSchema = z.enum(['conservative', 'balanced', 'aggressive']);

export const BudgetSchema = z.object({
  max_cost_usd_per_run: z.number().min(0).default(2.0),
  max_cost_usd_per_task: z.number().min(0).default(8.0),
  max_cost_usd_per_project_per_day: z.number().min(0).default(30.0),
  mode: BudgetModeSchema.default('balanced'),
});

export type UsageModelTier = z.infer<typeof UsageModelTierSchema>;
export type UsageRecord = z.infer<typeof UsageRecordSchema>;
export type BudgetMode = z.infer<typeof BudgetModeSchema>;
export type Budget = z.infer<typeof BudgetSchema>;
