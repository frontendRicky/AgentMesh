import { Router } from 'express';
import { z } from 'zod';

import { fail, ok } from './_helpers.js';
import { checkBudget, isRunBudgetBreached } from '../store/budget-gate.js';
import { tokenLedger, type UsageFilter, type UsageRecord } from '../store/token-ledger.js';

export const usageRouter = Router();

const usageModelTierSchema = z.enum(['cheap', 'balanced', 'strong']);

const usageRecordRequestSchema = z.object({
  project_id: z.string().min(1),
  task_id: z.string().min(1),
  run_id: z.string().min(1),
  agent: z.string().min(1),
  model: z.string().min(1),
  model_tier: usageModelTierSchema,
  input_tokens: z.number().int().min(0),
  output_tokens: z.number().int().min(0),
  cost_usd: z.number().min(0),
  optimization_applied: z.array(z.string()).default([]),
  created_at: z.string().datetime().optional(),
}).strict();

usageRouter.get('/', (req, res) => {
  const filter = readUsageFilter(req.query);
  return ok(res, tokenLedger.list(filter));
});

usageRouter.post('/', (req, res) => {
  const parsed = usageRecordRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return fail(res, 400, 'USAGE_RECORD_INVALID', 'Invalid usage record', {
      issues: parsed.error.issues,
    });
  }

  const record: UsageRecord = {
    ...parsed.data,
    created_at: parsed.data.created_at ?? new Date().toISOString(),
  };
  const budgetCheck = checkBudget(record);
  tokenLedger.append(record);
  res.status(201);
  return ok(res, { record, budget_check: budgetCheck });
});

usageRouter.get('/summary', (req, res) => {
  const filter = readUsageFilter(req.query);
  const records = tokenLedger.list(filter);
  return ok(res, {
    total_cost_usd: records.reduce((total, record) => total + record.cost_usd, 0),
    total_input_tokens: records.reduce((total, record) => total + record.input_tokens, 0),
    total_output_tokens: records.reduce((total, record) => total + record.output_tokens, 0),
    record_count: records.length,
    breached_count: records.filter((record) => isRunBudgetBreached(record)).length,
  });
});

function readUsageFilter(query: Record<string, unknown>): UsageFilter {
  const filter: UsageFilter = {};
  const runId = readQueryString(query['run_id']);
  const taskId = readQueryString(query['task_id']);
  const projectId = readQueryString(query['project_id']);
  const date = readQueryString(query['date']);
  if (runId) filter.run_id = runId;
  if (taskId) filter.task_id = taskId;
  if (projectId) filter.project_id = projectId;
  if (date) filter.date = date;
  return filter;
}

function readQueryString(value: unknown): string | undefined {
  return typeof value === 'string' && value.length > 0 ? value : undefined;
}
