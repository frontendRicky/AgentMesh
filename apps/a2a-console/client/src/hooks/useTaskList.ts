import { apiGet, usePolling } from './useApi';
import { useSettingsStore } from '@/store/settingsStore';
import type { TaskListItem } from '@/types/task';

interface TaskListResponse {
  items: TaskListItem[];
  total: number;
}

export function useTaskList() {
  const interval = useSettingsStore((s) => s.pollIntervalMs);
  return usePolling<TaskListResponse>(
    () => apiGet<TaskListResponse>('/api/a2a/tasks'),
    [],
    { intervalMs: interval },
  );
}
