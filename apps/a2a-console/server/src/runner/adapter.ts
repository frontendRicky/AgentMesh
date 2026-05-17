export interface RunnerStartInput {
  runId: string;
  taskId: string;
  agent: string;
  model?: string;
}

export interface IRunnerAdapter {
  start(input: RunnerStartInput): Promise<void>;
  pause(runId: string): Promise<void>;
  resume(runId: string): Promise<void>;
  cancel(runId: string): Promise<void>;
}
