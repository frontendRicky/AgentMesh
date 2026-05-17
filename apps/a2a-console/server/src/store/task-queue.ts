import type { RunPriority } from './run-pool.js';

export interface QueuedTask {
  task_id: string;
  priority: RunPriority;
  enqueued_at: string;
  sequence: number;
}

export interface QueuedTaskWithPosition {
  task_id: string;
  priority: RunPriority;
  enqueued_at: string;
  position: number;
}

const priorityRank: Record<RunPriority, number> = {
  urgent: 0,
  high: 1,
  normal: 2,
  background: 3,
};

class TaskQueue {
  private readonly items: QueuedTask[] = [];
  private sequence = 0;

  enqueue(taskId: string, priority: RunPriority = 'normal'): QueuedTaskWithPosition | null {
    if (this.items.some((item) => item.task_id === taskId)) return null;
    this.sequence += 1;
    this.items.push({
      task_id: taskId,
      priority,
      enqueued_at: new Date().toISOString(),
      sequence: this.sequence,
    });
    return this.findWithPosition(taskId);
  }

  dequeue(): QueuedTaskWithPosition | null {
    const [first] = this.sortedItems();
    if (!first) return null;
    this.remove(first.task_id);
    return this.toPositioned(first, 1);
  }

  list(): QueuedTaskWithPosition[] {
    return this.sortedItems().map((item, index) => this.toPositioned(item, index + 1));
  }

  remove(taskId: string): boolean {
    const index = this.items.findIndex((item) => item.task_id === taskId);
    if (index === -1) return false;
    this.items.splice(index, 1);
    return true;
  }

  private findWithPosition(taskId: string): QueuedTaskWithPosition | null {
    return this.list().find((item) => item.task_id === taskId) ?? null;
  }

  private sortedItems(): QueuedTask[] {
    return [...this.items].sort((a, b) => {
      const priorityDelta = priorityRank[a.priority] - priorityRank[b.priority];
      if (priorityDelta !== 0) return priorityDelta;
      return a.sequence - b.sequence;
    });
  }

  private toPositioned(item: QueuedTask, position: number): QueuedTaskWithPosition {
    return {
      task_id: item.task_id,
      priority: item.priority,
      enqueued_at: item.enqueued_at,
      position,
    };
  }
}

export const taskQueue = new TaskQueue();
