import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

export type UsageModelTier = 'cheap' | 'balanced' | 'strong';

export interface UsageRecord {
  project_id: string;
  task_id: string;
  run_id: string;
  agent: string;
  model: string;
  model_tier: UsageModelTier;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number;
  optimization_applied: string[];
  created_at: string;
}

export interface UsageFilter {
  run_id?: string;
  task_id?: string;
  project_id?: string;
  date?: string;
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const APP_ROOT = path.resolve(__dirname, '..', '..');
const LEDGER_FILE = path.join(APP_ROOT, '.token-ledger.jsonl');

class TokenLedger {
  private readonly records: UsageRecord[] = [];

  constructor() {
    this.load();
  }

  append(record: UsageRecord): UsageRecord {
    this.records.push(record);
    fs.appendFileSync(LEDGER_FILE, `${JSON.stringify(record)}\n`, 'utf8');
    return record;
  }

  list(filter: UsageFilter = {}): UsageRecord[] {
    return this.records.filter((record) => matchesFilter(record, filter));
  }

  listByRun(runId: string): UsageRecord[] {
    return this.list({ run_id: runId });
  }

  listByTask(taskId: string): UsageRecord[] {
    return this.list({ task_id: taskId });
  }

  listByProject(projectId: string): UsageRecord[] {
    return this.list({ project_id: projectId });
  }

  listByDay(date: string): UsageRecord[] {
    return this.list({ date });
  }

  sumCost(filter: UsageFilter = {}): number {
    return this.list(filter).reduce((total, record) => total + record.cost_usd, 0);
  }

  private load(): void {
    if (!fs.existsSync(LEDGER_FILE)) return;
    try {
      const lines = fs.readFileSync(LEDGER_FILE, 'utf8').split('\n');
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.length === 0) continue;
        const parsed = JSON.parse(trimmed) as unknown;
        if (isUsageRecord(parsed)) this.records.push(parsed);
      }
    } catch {
      this.records.splice(0);
    }
  }
}

function matchesFilter(record: UsageRecord, filter: UsageFilter): boolean {
  if (filter.run_id !== undefined && record.run_id !== filter.run_id) return false;
  if (filter.task_id !== undefined && record.task_id !== filter.task_id) return false;
  if (filter.project_id !== undefined && record.project_id !== filter.project_id) return false;
  if (filter.date !== undefined && record.created_at.slice(0, 10) !== filter.date) return false;
  return true;
}

function isUsageRecord(value: unknown): value is UsageRecord {
  if (value === null || typeof value !== 'object') return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record['project_id'] === 'string'
    && typeof record['task_id'] === 'string'
    && typeof record['run_id'] === 'string'
    && typeof record['agent'] === 'string'
    && typeof record['model'] === 'string'
    && isModelTier(record['model_tier'])
    && Number.isInteger(record['input_tokens'])
    && Number(record['input_tokens']) >= 0
    && Number.isInteger(record['output_tokens'])
    && Number(record['output_tokens']) >= 0
    && typeof record['cost_usd'] === 'number'
    && record['cost_usd'] >= 0
    && Array.isArray(record['optimization_applied'])
    && record['optimization_applied'].every((item) => typeof item === 'string')
    && typeof record['created_at'] === 'string'
  );
}

function isModelTier(value: unknown): value is UsageModelTier {
  return value === 'cheap' || value === 'balanced' || value === 'strong';
}

export const tokenLedger = new TokenLedger();
export const tokenLedgerFilePath = LEDGER_FILE;
