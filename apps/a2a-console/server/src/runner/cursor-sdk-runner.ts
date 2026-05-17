import type { IRunnerAdapter, RunnerStartInput } from './adapter.js';

export class CursorSdkRunner implements IRunnerAdapter {
  async start(_input: RunnerStartInput): Promise<void> {
    // TODO: Phase 1 - integrate @cursor/sdk
    throw new Error('not implemented - Cursor SDK integration pending');
  }

  async pause(_runId: string): Promise<void> {
    // TODO: Phase 1 - integrate @cursor/sdk
    throw new Error('not implemented - Cursor SDK integration pending');
  }

  async resume(_runId: string): Promise<void> {
    // TODO: Phase 1 - integrate @cursor/sdk
    throw new Error('not implemented - Cursor SDK integration pending');
  }

  async cancel(_runId: string): Promise<void> {
    // TODO: Phase 1 - integrate @cursor/sdk
    throw new Error('not implemented - Cursor SDK integration pending');
  }
}
