import type { ContextAgent, ContextPack } from '@a2a-console/contract';

class ContextPackStore {
  private readonly packs = new Map<string, ContextPack>();
  private sequence = 0;

  createId(): string {
    this.sequence += 1;
    return `CP-${Date.now()}-${String(this.sequence).padStart(4, '0')}`;
  }

  add(pack: ContextPack): ContextPack {
    this.packs.set(pack.pack_id, pack);
    return pack;
  }

  get(packId: string): ContextPack | null {
    return this.packs.get(packId) ?? null;
  }

  list(filter: { taskId?: string; agent?: ContextAgent } = {}): ContextPack[] {
    return Array.from(this.packs.values())
      .filter((pack) => filter.taskId === undefined || pack.task_id === filter.taskId)
      .filter((pack) => filter.agent === undefined || pack.agent === filter.agent)
      .sort((a, b) => b.created_at.localeCompare(a.created_at));
  }
}

export const contextPackStore = new ContextPackStore();
