import { z } from 'zod';
export declare const PolicyDecisionTypeSchema: z.ZodEnum<["AUTO_APPROVE", "AUTO_REJECT", "NEED_HUMAN_REVIEW", "NEED_MORE_TESTS", "NEED_FIX_LOOP"]>;
export declare const RiskLevelSchema: z.ZodEnum<["low", "medium", "high", "critical"]>;
export declare const BudgetStatusSchema: z.ZodEnum<["ok", "warning", "breached"]>;
export declare const PolicyEvaluatedPathSchema: z.ZodObject<{
    path: z.ZodString;
    risk: z.ZodEnum<["low", "medium", "high", "critical"]>;
}, "strip", z.ZodTypeAny, {
    path: string;
    risk: "high" | "low" | "medium" | "critical";
}, {
    path: string;
    risk: "high" | "low" | "medium" | "critical";
}>;
export declare const PolicyDecisionSchema: z.ZodObject<{
    decision: z.ZodEnum<["AUTO_APPROVE", "AUTO_REJECT", "NEED_HUMAN_REVIEW", "NEED_MORE_TESTS", "NEED_FIX_LOOP"]>;
    risk_level: z.ZodEnum<["low", "medium", "high", "critical"]>;
    reasons: z.ZodArray<z.ZodString, "many">;
    matched_rules: z.ZodArray<z.ZodString, "many">;
    evaluated_paths: z.ZodArray<z.ZodObject<{
        path: z.ZodString;
        risk: z.ZodEnum<["low", "medium", "high", "critical"]>;
    }, "strip", z.ZodTypeAny, {
        path: string;
        risk: "high" | "low" | "medium" | "critical";
    }, {
        path: string;
        risk: "high" | "low" | "medium" | "critical";
    }>, "many">;
    budget_status: z.ZodEnum<["ok", "warning", "breached"]>;
    created_at: z.ZodString;
}, "strip", z.ZodTypeAny, {
    created_at: string;
    decision: "AUTO_APPROVE" | "AUTO_REJECT" | "NEED_HUMAN_REVIEW" | "NEED_MORE_TESTS" | "NEED_FIX_LOOP";
    risk_level: "high" | "low" | "medium" | "critical";
    reasons: string[];
    matched_rules: string[];
    evaluated_paths: {
        path: string;
        risk: "high" | "low" | "medium" | "critical";
    }[];
    budget_status: "ok" | "warning" | "breached";
}, {
    created_at: string;
    decision: "AUTO_APPROVE" | "AUTO_REJECT" | "NEED_HUMAN_REVIEW" | "NEED_MORE_TESTS" | "NEED_FIX_LOOP";
    risk_level: "high" | "low" | "medium" | "critical";
    reasons: string[];
    matched_rules: string[];
    evaluated_paths: {
        path: string;
        risk: "high" | "low" | "medium" | "critical";
    }[];
    budget_status: "ok" | "warning" | "breached";
}>;
export type PolicyDecisionType = z.infer<typeof PolicyDecisionTypeSchema>;
export type RiskLevel = z.infer<typeof RiskLevelSchema>;
export type BudgetStatus = z.infer<typeof BudgetStatusSchema>;
export type PolicyEvaluatedPath = z.infer<typeof PolicyEvaluatedPathSchema>;
export type PolicyDecision = z.infer<typeof PolicyDecisionSchema>;
