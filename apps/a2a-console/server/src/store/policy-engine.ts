import { checkBudget, DEFAULT_BUDGET } from './budget-gate.js';
import { parseFileChangePlanPaths } from './file-change-plan-parser.js';
import { projectRegistry } from './project-registry.js';
import { maxRiskLevel, scorePaths, type EvaluatedPath, type RiskLevel } from './risk-scorer.js';
import type { UsageRecord } from './token-ledger.js';

export type PolicyDecisionType =
  | 'AUTO_APPROVE'
  | 'AUTO_REJECT'
  | 'NEED_HUMAN_REVIEW'
  | 'NEED_MORE_TESTS'
  | 'NEED_FIX_LOOP';

export type BudgetStatus = 'ok' | 'warning' | 'breached';

export interface PolicyDecision {
  decision: PolicyDecisionType;
  risk_level: RiskLevel;
  reasons: string[];
  matched_rules: string[];
  evaluated_paths: EvaluatedPath[];
  budget_status: BudgetStatus;
  created_at: string;
}

export interface PolicyEvaluateInput {
  task_id: string;
  project_id?: string;
  file_change_plan_text: string;
  estimated_cost_usd?: number;
}

const MAX_DECISIONS = 50;
const MAX_HISTORY_PER_TASK = 10;
const BUDGET_WARNING_RATIO = 0.8;

class PolicyEngine {
  private readonly decisions: Array<{ task_id: string; decision: PolicyDecision }> = [];

  evaluate(input: PolicyEvaluateInput): PolicyDecision {
    const paths = parseFileChangePlanPaths(input.file_change_plan_text);
    const evaluatedPaths = scorePaths(paths);
    const riskLevel = maxRiskLevel(evaluatedPaths);
    const reasons: string[] = [];
    const matchedRules: string[] = [];
    const blockedMatches = input.project_id
      ? findProjectBlockedMatches(input.project_id, paths)
      : [];
    const budgetCheck = checkBudget(createUsageRecord(input));
    const budgetStatus = budgetStatusOf(budgetCheck.ok, budgetCheck.current_cost.run);

    if (paths.length === 0) {
      reasons.push('file-change-plan 未解析到授权路径，建议人工确认范围。');
      matchedRules.push('POLICY_NO_PATHS');
    }

    if (blockedMatches.length > 0) {
      reasons.push(`项目策略阻止路径：${blockedMatches.join('、')}。`);
      matchedRules.push('PROJECT_BLOCKED_PATH');
    }

    if (riskLevel === 'critical') {
      reasons.push('命中 critical 高风险路径，默认拒绝自动放行。');
      matchedRules.push('RISK_CRITICAL_PATH');
    } else if (riskLevel === 'high') {
      reasons.push('命中 high 风险路径，需要 Human Review。');
      matchedRules.push('RISK_HIGH_PATH');
    } else if (riskLevel === 'medium') {
      reasons.push('命中 medium 风险路径，需要 Human Review 或更严格测试。');
      matchedRules.push('RISK_MEDIUM_PATH');
    } else {
      reasons.push('仅命中 low 风险路径，可建议自动批准。');
      matchedRules.push('RISK_LOW_PATH');
    }

    if (!budgetCheck.ok) {
      reasons.push(`预算门禁提示：${budgetCheck.hint}。`);
      matchedRules.push('BUDGET_BREACHED');
    } else if (budgetStatus === 'warning') {
      reasons.push('预计成本接近单 run 预算上限，建议观察后续调用。');
      matchedRules.push('BUDGET_WARNING');
    }

    const decision: PolicyDecision = {
      decision: decide({
        riskLevel,
        blockedByProject: blockedMatches.length > 0,
        budgetBreached: !budgetCheck.ok,
        noPaths: paths.length === 0,
      }),
      risk_level: riskLevel,
      reasons,
      matched_rules: matchedRules,
      evaluated_paths: evaluatedPaths,
      budget_status: budgetStatus,
      created_at: new Date().toISOString(),
    };
    this.remember(input.task_id, decision);
    return decision;
  }

  listByTask(taskId: string): PolicyDecision[] {
    return this.decisions
      .filter((item) => item.task_id === taskId)
      .slice(-MAX_HISTORY_PER_TASK)
      .map((item) => item.decision);
  }

  private remember(taskId: string, decision: PolicyDecision): void {
    this.decisions.push({ task_id: taskId, decision });
    if (this.decisions.length > MAX_DECISIONS) {
      this.decisions.splice(0, this.decisions.length - MAX_DECISIONS);
    }
  }
}

function decide({
  riskLevel,
  blockedByProject,
  budgetBreached,
  noPaths,
}: {
  riskLevel: RiskLevel;
  blockedByProject: boolean;
  budgetBreached: boolean;
  noPaths: boolean;
}): PolicyDecisionType {
  if (blockedByProject || riskLevel === 'critical') return 'AUTO_REJECT';
  if (noPaths) return 'NEED_HUMAN_REVIEW';
  if (riskLevel === 'high') return 'NEED_HUMAN_REVIEW';
  if (riskLevel === 'medium') return budgetBreached ? 'NEED_MORE_TESTS' : 'NEED_HUMAN_REVIEW';
  return budgetBreached ? 'NEED_HUMAN_REVIEW' : 'AUTO_APPROVE';
}

function createUsageRecord(input: PolicyEvaluateInput): UsageRecord {
  const now = new Date().toISOString();
  return {
    project_id: input.project_id ?? 'policy-evaluation',
    task_id: input.task_id,
    run_id: `policy-${input.task_id}`,
    agent: 'policy',
    model: 'estimated',
    model_tier: 'cheap',
    input_tokens: 0,
    output_tokens: 0,
    cost_usd: input.estimated_cost_usd ?? 0,
    optimization_applied: [],
    created_at: now,
  };
}

function budgetStatusOf(ok: boolean, runCost: number): BudgetStatus {
  if (!ok) return 'breached';
  if (runCost >= DEFAULT_BUDGET.max_cost_usd_per_run * BUDGET_WARNING_RATIO) return 'warning';
  return 'ok';
}

function findProjectBlockedMatches(projectId: string, paths: string[]): string[] {
  const project = projectRegistry.get(projectId);
  if (!project) return [];
  return paths.filter((path) => {
    return project.blocked_paths.some((pattern) => matchesPattern(path, pattern));
  });
}

function matchesPattern(path: string, pattern: string): boolean {
  const normalizedPath = normalizePath(path);
  const normalizedPattern = normalizePath(pattern);
  if (normalizedPattern.endsWith('/**')) {
    const prefix = normalizedPattern.slice(0, -3);
    return normalizedPath === prefix || normalizedPath.startsWith(`${prefix}/`);
  }
  if (normalizedPattern.startsWith('*.')) {
    return normalizedPath.endsWith(normalizedPattern.slice(1));
  }
  return normalizedPath === normalizedPattern || normalizedPath.startsWith(`${normalizedPattern}/`);
}

function normalizePath(path: string): string {
  return path.trim().replaceAll('\\', '/').replace(/^\.\//, '').replace(/\/+/g, '/');
}

export const policyEngine = new PolicyEngine();
