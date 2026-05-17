import { z } from 'zod';
export const PolicyDecisionTypeSchema = z.enum([
    'AUTO_APPROVE',
    'AUTO_REJECT',
    'NEED_HUMAN_REVIEW',
    'NEED_MORE_TESTS',
    'NEED_FIX_LOOP',
]);
export const RiskLevelSchema = z.enum(['low', 'medium', 'high', 'critical']);
export const BudgetStatusSchema = z.enum(['ok', 'warning', 'breached']);
export const PolicyEvaluatedPathSchema = z.object({
    path: z.string(),
    risk: RiskLevelSchema,
});
export const PolicyDecisionSchema = z.object({
    decision: PolicyDecisionTypeSchema,
    risk_level: RiskLevelSchema,
    reasons: z.array(z.string()),
    matched_rules: z.array(z.string()),
    evaluated_paths: z.array(PolicyEvaluatedPathSchema),
    budget_status: BudgetStatusSchema,
    created_at: z.string().datetime(),
});
//# sourceMappingURL=policy.js.map