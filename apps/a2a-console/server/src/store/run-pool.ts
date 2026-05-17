export type RunPriority = 'urgent' | 'high' | 'normal' | 'background';
export type RunStatus = 'queued' | 'running' | 'paused' | 'cancelled' | 'completed' | 'failed';

export interface RunSession {
  run_id: string;
  task_id: string;
  status: RunStatus;
  priority: RunPriority;
  agent: string;
  model: string;
  created_at: string;
  updated_at: string;
  error_message?: string;
}

export interface RunSessionCreateInput {
  task_id: string;
  status?: RunStatus;
  priority?: RunPriority;
  agent: string;
  model?: string;
  error_message?: string;
}

export interface RunSessionUpdateInput {
  status?: RunStatus;
  priority?: RunPriority;
  error_message?: string;
}

const priorityRank: Record<RunPriority, number> = {
  urgent: 0,
  high: 1,
  normal: 2,
  background: 3,
};

class RunPool {
  private readonly runs = new Map<string, RunSession>();
  private runSeq = 0;

  add(input: RunSessionCreateInput): RunSession {
    const now = new Date().toISOString();
    const run: RunSession = {
      run_id: this.createRunId(),
      task_id: input.task_id,
      status: input.status ?? 'queued',
      priority: input.priority ?? 'normal',
      agent: input.agent,
      model: input.model ?? 'default',
      created_at: now,
      updated_at: now,
      error_message: input.error_message,
    };
    this.runs.set(run.run_id, run);
    return run;
  }

  get(runId: string): RunSession | null {
    return this.runs.get(runId) ?? null;
  }

  update(runId: string, patch: RunSessionUpdateInput): RunSession | null {
    const current = this.runs.get(runId);
    if (!current) return null;
    const next: RunSession = {
      ...current,
      ...patch,
      updated_at: new Date().toISOString(),
    };
    this.runs.set(runId, next);
    return next;
  }

  list(taskId?: string): RunSession[] {
    const items = Array.from(this.runs.values()).filter((run) => {
      return taskId === undefined || run.task_id === taskId;
    });
    return sortRunsByPriority(items);
  }

  listByStatus(status: RunStatus): RunSession[] {
    return sortRunsByPriority(Array.from(this.runs.values()).filter((run) => run.status === status));
  }

  private createRunId(): string {
    this.runSeq += 1;
    return `R-${Date.now()}-${String(this.runSeq).padStart(4, '0')}`;
  }
}

function sortRunsByPriority(items: RunSession[]): RunSession[] {
  return [...items].sort((a, b) => {
    const priorityDelta = priorityRank[a.priority] - priorityRank[b.priority];
    if (priorityDelta !== 0) return priorityDelta;
    return a.created_at.localeCompare(b.created_at);
  });
}

export const runPool = new RunPool();
