import { tokenLedger, type UsageRecord } from './token-ledger.js';

export interface Budget {
  max_cost_usd_per_run: number;
  max_cost_usd_per_task: number;
  max_cost_usd_per_project_per_day: number;
  mode: 'conservative' | 'balanced' | 'aggressive';
}

export interface BudgetCheckResult {
  ok: boolean;
  breached: Array<'run' | 'task' | 'project_day'>;
  current_cost: {
    run: number;
    task: number;
    project_day: number;
  };
  hint: string;
}

export const DEFAULT_BUDGET: Budget = {
  max_cost_usd_per_run: 2.0,
  max_cost_usd_per_task: 8.0,
  max_cost_usd_per_project_per_day: 30.0,
  mode: 'balanced',
};

export function checkBudget(recordToAdd: UsageRecord, budget: Budget = DEFAULT_BUDGET): BudgetCheckResult {
  const date = recordToAdd.created_at.slice(0, 10);
  const currentCost = {
    run: tokenLedger.sumCost({ run_id: recordToAdd.run_id }) + recordToAdd.cost_usd,
    task: tokenLedger.sumCost({ task_id: recordToAdd.task_id }) + recordToAdd.cost_usd,
    project_day: tokenLedger.sumCost({ project_id: recordToAdd.project_id, date }) + recordToAdd.cost_usd,
  };
  const breached: BudgetCheckResult['breached'] = [];
  const hints: string[] = [];

  if (currentCost.run > budget.max_cost_usd_per_run) {
    breached.push('run');
    hints.push(`该 run 累计 ${formatCost(currentCost.run)} 超过 ${formatCost(budget.max_cost_usd_per_run)} 上限`);
  }
  if (currentCost.task > budget.max_cost_usd_per_task) {
    breached.push('task');
    hints.push(`该 task 累计 ${formatCost(currentCost.task)} 超过 ${formatCost(budget.max_cost_usd_per_task)} 上限`);
  }
  if (currentCost.project_day > budget.max_cost_usd_per_project_per_day) {
    breached.push('project_day');
    hints.push(`该项目今日累计 ${formatCost(currentCost.project_day)} 超过 ${formatCost(budget.max_cost_usd_per_project_per_day)} 上限`);
  }

  return {
    ok: breached.length === 0,
    breached,
    current_cost: currentCost,
    hint: hints.length > 0 ? hints.join('；') : '预算未超限',
  };
}

export function isRunBudgetBreached(record: UsageRecord, budget: Budget = DEFAULT_BUDGET): boolean {
  return record.cost_usd > budget.max_cost_usd_per_run;
}

function formatCost(value: number): string {
  return `$${value.toFixed(2)}`;
}
