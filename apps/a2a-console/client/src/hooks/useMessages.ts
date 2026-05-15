import { apiGet, usePolling } from './useApi';
import { useSettingsStore } from '@/store/settingsStore';
import type { MessageItem } from '@/types/message';

export function useMessages(taskId: string | null) {
  const interval = useSettingsStore((s) => s.pollIntervalMs);
  return usePolling<{ items: MessageItem[]; total?: number }>(
    () => apiGet(`/api/a2a/tasks/${taskId}/messages`),
    [taskId ?? ''],
    { intervalMs: interval, enabled: Boolean(taskId) },
  );
}
