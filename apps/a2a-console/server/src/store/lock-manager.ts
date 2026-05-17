export type LockType = 'file' | 'directory' | 'project';
export type LockAcquireResult = 'acquired' | 'waiting';

export interface LockRecord {
  path: string;
  lock_type: LockType;
  held_by_run_id: string;
}

const PROJECT_LOCK_PATH = '<project>';

const highRiskPathRules = [
  (path: string) => path === 'package.json' || path.endsWith('/package.json'),
  (path: string) => path === 'src/auth' || path.startsWith('src/auth/') || path.includes('/src/auth/'),
  (path: string) => (
    path === 'src/payment'
    || path.startsWith('src/payment/')
    || path.includes('/src/payment/')
  ),
];

class LockManager {
  private readonly locks = new Map<string, LockRecord>();

  acquire(runId: string, paths: string[]): LockAcquireResult {
    const requested = this.createRequestedLocks(runId, paths);
    const conflicts = this.findConflicts(requested, runId);
    if (conflicts.length > 0) return 'waiting';

    for (const lock of requested) {
      this.locks.set(lockKey(lock), lock);
    }
    return 'acquired';
  }

  waitingOn(runId: string, paths: string[]): LockRecord[] {
    return this.findConflicts(this.createRequestedLocks(runId, paths), runId);
  }

  release(runId: string): void {
    for (const [key, lock] of this.locks.entries()) {
      if (lock.held_by_run_id === runId) {
        this.locks.delete(key);
      }
    }
  }

  listLocks(): LockRecord[] {
    return Array.from(this.locks.values()).sort((a, b) => {
      const typeDelta = lockTypeRank(a.lock_type) - lockTypeRank(b.lock_type);
      if (typeDelta !== 0) return typeDelta;
      return a.path.localeCompare(b.path);
    });
  }

  private createRequestedLocks(runId: string, paths: string[]): LockRecord[] {
    const locks = paths.map((path) => createLockRecord(runId, path));
    return dedupeLocks(locks);
  }

  private findConflicts(requested: LockRecord[], runId: string): LockRecord[] {
    const conflicts = new Map<string, LockRecord>();
    for (const request of requested) {
      for (const held of this.locks.values()) {
        if (held.held_by_run_id === runId) continue;
        if (!locksConflict(request, held)) continue;
        conflicts.set(lockKey(held), held);
      }
    }
    return Array.from(conflicts.values());
  }
}

function createLockRecord(runId: string, rawPath: string): LockRecord {
  const normalized = normalizePath(rawPath);
  if (isHighRiskPath(normalized)) {
    return { path: PROJECT_LOCK_PATH, lock_type: 'project', held_by_run_id: runId };
  }
  if (isDirectoryPattern(normalized)) {
    return {
      path: normalizeDirectoryPath(normalized),
      lock_type: 'directory',
      held_by_run_id: runId,
    };
  }
  return { path: normalized, lock_type: 'file', held_by_run_id: runId };
}

function normalizePath(path: string): string {
  return path.trim().replaceAll('\\', '/').replace(/^\.\//, '').replace(/\/+/g, '/');
}

function isHighRiskPath(path: string): boolean {
  return highRiskPathRules.some((rule) => rule(path));
}

function isDirectoryPattern(path: string): boolean {
  return path.endsWith('/**') || path.endsWith('/');
}

function normalizeDirectoryPath(path: string): string {
  return path.replace(/\/\*\*$/, '').replace(/\/$/, '');
}

function dedupeLocks(locks: LockRecord[]): LockRecord[] {
  const deduped = new Map<string, LockRecord>();
  for (const lock of locks) {
    deduped.set(lockKey(lock), lock);
  }
  return Array.from(deduped.values());
}

function locksConflict(a: LockRecord, b: LockRecord): boolean {
  if (a.lock_type === 'project' || b.lock_type === 'project') return true;
  if (a.lock_type === 'file' && b.lock_type === 'file') return a.path === b.path;
  if (a.lock_type === 'directory' && b.lock_type === 'directory') {
    return isSameOrChild(a.path, b.path) || isSameOrChild(b.path, a.path);
  }
  const directory = a.lock_type === 'directory' ? a : b;
  const file = a.lock_type === 'file' ? a : b;
  return isSameOrChild(file.path, directory.path);
}

function isSameOrChild(path: string, parent: string): boolean {
  return path === parent || path.startsWith(`${parent}/`);
}

function lockKey(lock: LockRecord): string {
  return `${lock.lock_type}:${lock.path}:${lock.held_by_run_id}`;
}

function lockTypeRank(type: LockType): number {
  if (type === 'project') return 0;
  if (type === 'directory') return 1;
  return 2;
}

export const lockManager = new LockManager();
