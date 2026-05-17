import { Router } from 'express';
import { z } from 'zod';

import { fail, ok } from './_helpers.js';
import { policyEngine } from '../store/policy-engine.js';

export const policyRouter = Router();

const policyEvaluateRequestSchema = z.object({
  task_id: z.string().min(1),
  project_id: z.string().min(1).optional(),
  file_change_plan_text: z.string(),
  estimated_cost_usd: z.number().min(0).optional(),
}).strict();

policyRouter.post('/evaluate', (req, res) => {
  const parsed = policyEvaluateRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return fail(res, 400, 'POLICY_EVALUATE_INVALID', 'Invalid policy evaluate request', {
      issues: parsed.error.issues,
    });
  }

  return ok(res, policyEngine.evaluate(parsed.data));
});

policyRouter.get('/decisions/:taskId', (req, res) => {
  const taskId = req.params['taskId'];
  if (typeof taskId !== 'string' || taskId.length === 0) {
    return fail(res, 400, 'TASK_ID_INVALID', 'taskId is required');
  }

  return ok(res, policyEngine.listByTask(taskId));
});
