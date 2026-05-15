import { apiGet, usePolling } from './useApi';
import { useSettingsStore } from '@/store/settingsStore';

export interface ActiveTaskData {
  active_task_id: string | null;
  last_switched_at: string | null;
  directory_exists: boolean;
}

export function useActiveTask() {
  const interval = useSettingsStore((s) => s.pollIntervalMs);
  return usePolling<ActiveTaskData>(
    () => apiGet<ActiveTaskData>('/api/a2a/active-task'),
    [],
    { intervalMs: interval },
  );
}

export function useProjectRoot() {
  const interval = useSettingsStore((s) => s.pollIntervalMs);
  return usePolling<{ project_root: string | null; configured_at: string | null }>(
    () => apiGet('/api/a2a/config/project-root'),
    [],
    { intervalMs: Math.max(interval, 10_000) },
  );
}
